#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 壓測工具
"""

import asyncio
import aiohttp
import json
import os
import glob
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import platform
import argparse

def _set_chinese_font():
    sys_fonts = []
    try:
        from matplotlib.font_manager import fontManager
        sys_fonts = [f.name for f in fontManager.ttflist]
    except Exception:
        pass
    family = None
    if platform.system() == 'Windows':
        if 'Microsoft YaHei' in sys_fonts:
            family = 'Microsoft YaHei'
    elif platform.system() == 'Darwin':
        # macOS 常見中文字型
        for f in ['PingFang TC', 'Heiti TC', 'STHeitiTC-Light']:
            if f in sys_fonts:
                family = f
                break
    elif platform.system() == 'Linux':
        # Ubuntu 常見中文字型
        for f in ['Noto Sans CJK TC', 'WenQuanYi Zen Hei', 'AR PL UMing CN']:
            if f in sys_fonts:
                family = f
                break
    if family:
        matplotlib.rcParams['font.sans-serif'] = [family]
    else:
        import warnings
        warnings.warn('找不到合適的中文字型，請安裝 Noto Sans CJK TC 或 WenQuanYi Zen Hei 以避免中文顯示異常。')
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

_set_chinese_font()

import re  # 用於移除 JSONC 中的註解
import sys  # 新增 sys 以解析命令列參數
import shutil  # 用於複製檔案

def format_time_delta(delta):
    # 將 timedelta 轉為 00:00:05.123456 格式
    total_seconds = delta.total_seconds()
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02}:{int(minutes):02}:{seconds:09.6f}"

async def worker(seq, config, problems, test_start, results, debug=False, args=None, start_time=None):
    url = config['url']
    model = config['model']
    system_prompt = config.get('system_prompt', '')
    total_start = datetime.now()
    rel_start = (total_start - test_start).total_seconds()
    # 選擇問題
    problem = problems[(seq - 1) % len(problems)]
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': problem}
        ],
        'stream': True
    }
    # 時間指標
    t0 = datetime.now()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            start_ttft_time = None
            text = ''
            t1 = None  # 確保 t1 有賦值
            tokens = []
            first_token_printed = False
            last_token = None
            async for raw_bytes in resp.content:
                decoded = raw_bytes.decode('utf-8')
                for line in decoded.splitlines():
                    if line.startswith('data:'):
                        data_str = line[len('data:'):].strip()
                        if data_str == '[DONE]':
                            break
                        chunk = json.loads(data_str)
                        content = chunk['choices'][0]['delta'].get('content', '')
                        if content:
                            if start_ttft_time is None:
                                start_ttft_time = datetime.now()
                                t1 = start_ttft_time
                            text += content
                            tokens.append(content)
                            now = datetime.now()
                            elapsed = now - start_time
                            if args.d:
                                print(content, end='', flush=True)
                            if args.df and not first_token_printed:
                                print(f"{format_time_delta(elapsed)}\t{content}")
                                first_token_printed = True
                            if args.dv:
                                print(f"{format_time_delta(elapsed)}\t{content}")
                            last_token = content
            if t1 is None:  # 非 streaming 模式下明確賦值 t1
                t1 = datetime.now()
            t2 = datetime.now()
            if args.de and last_token is not None:
                now = datetime.now()
                elapsed = now - start_time
                print(f"{format_time_delta(elapsed)}\t{last_token}")
            data = {'choices': [{'message': {'content': text}}]}
    # 解析回答
    ans = data['choices'][0]['message']['content'].replace('\n', ' ')
    # 計算時間
    ttft = (t1 - t0).total_seconds()
    completion = (t2 - t0).total_seconds()
    # 記錄結果
    results.append({
        'seq': seq,
        'abs_time': total_start.strftime('%H:%M:%S.%f')[:-3],
        'rel_time': f"{rel_start // 60:02.0f}:{rel_start % 60:06.3f}",
        'ttft': ttft,
        'completion': completion,
        'prompt_no': (seq - 1) % len(problems) + 1,
        'problem': problem,
        'answer': ans
    })

async def warmup_worker(config, start_time):
    # 預設暖身題
    warmup_problem = "請簡單自我介紹"
    url = config['url']
    model = config['model']
    system_prompt = config.get('system_prompt', '')
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': warmup_problem}
        ],
        'stream': True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            async for raw_bytes in resp.content:
                decoded = raw_bytes.decode('utf-8')
                for line in decoded.splitlines():
                    if line.startswith('data:'):
                        data_str = line[len('data:'):].strip()
                        if data_str == '[DONE]':
                            return

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true', help='顯示 streaming 回覆')
    parser.add_argument('-df', action='store_true', help='僅顯示第一個 token')
    parser.add_argument('-de', action='store_true', help='僅顯示最後一個 token')
    parser.add_argument('-dv', action='store_true', help='顯示所有 token')
    parser.add_argument('config', help='設定檔路徑 (.jsonc 或 .json)')
    args = parser.parse_args()
    debug = args.d
    cfg_path = args.config
    start_time = datetime.now()
    # 支援 jsonc，先移除註解再解析
    with open(cfg_path, encoding='utf-8') as f:
        raw = f.read()
    # 移除單行註解 (必須在行首或前面有空白)
    raw = re.sub(r'(?m)^\s*//.*$|(?<=\s)//.*', '', raw)
    # 移除多行註解
    raw = re.sub(r'/\*[\s\S]*?\*/', '', raw)
    # 移除尾隨逗號 (JSONC 支援)
    raw = re.sub(r',(\s*[}\]])', r'\1', raw)
    # 清除非法控制字元
    raw = ''.join(ch for ch in raw if ch >= ' ' or ch in '\t\r\n')
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤: {e}")
        print("請確認 JSON 格式是否正確")
        sys.exit(1)
    # 執行暖身題
    print("執行預設暖身題...", flush=True)
    await warmup_worker(config, start_time)
    print("暖身完成，開始正式壓測。", flush=True)
    # 根據設定檔路徑計算輸出資料夾
    abs_cfg = os.path.abspath(cfg_path)
    cfg_dir = os.path.dirname(abs_cfg)
    base = os.path.splitext(os.path.basename(cfg_path))[0]
    # 計算下一個 seq: 資料夾以數字命名
    dirs = [d for d in os.listdir(cfg_dir) if os.path.isdir(os.path.join(cfg_dir, d)) and d.isdigit()]
    seq = max((int(d) for d in dirs), default=0) + 1
    output_dir = os.path.join(cfg_dir, str(seq))
    os.makedirs(output_dir, exist_ok=True)
    # 複製 設定檔 並在副檔名前加上 seq
    cfg_basename = os.path.basename(cfg_path)
    base_name, ext = os.path.splitext(cfg_basename)
    new_cfg_name = f"{base_name}.{seq}{ext}"
    shutil.copy(cfg_path, os.path.join(output_dir, new_cfg_name))
    problem_src = config['problem_file']
    if not os.path.isabs(problem_src):
        problem_src = os.path.join(cfg_dir, problem_src)
    # 複製 問題檔 並在副檔名前加上 seq
    prob_basename = os.path.basename(problem_src)
    prob_base, prob_ext = os.path.splitext(prob_basename)
    new_problem_name = f"{prob_base}.{seq}{prob_ext}"
    shutil.copy(problem_src, os.path.join(output_dir, new_problem_name))
    # 檔名置於 seq 資料夾下
    answers_file = os.path.join(output_dir, f"{base}.{seq}.answers.txt")
    stats_file = os.path.join(output_dir, f"{base}.{seq}.stats.txt")
    graph1_file = os.path.join(output_dir, f"{base}.{seq}.graph.latency.png")
    graph2_file = os.path.join(output_dir, f"{base}.{seq}.graph.concurrent.png")
    # 讀取 問題列表
    with open(problem_src, 'r', encoding='utf-8') as f:
        lines = [l.strip()[3:] for l in f if l.strip() and l.strip()[0].isdigit()]
    problems = lines[:config['num_problems']]
    # 平行處理 構建
    lp = config['load_profile']
    batch_concurrent = lp['batch_concurrent']
    batch_interval_seconds = lp['batch_interval_seconds']
    max_batches = lp['max_batches']
    repeat_per_request = lp['repeat_per_request']
    # 記錄時間起點
    test_start = datetime.now()
    results = []
    tasks = []
    total_batches = max_batches
    total_requests = batch_concurrent * repeat_per_request * max_batches
    # 依批次啟動
    seq = 1
    for batch in range(max_batches):
        for i in range(batch_concurrent):
            for j in range(repeat_per_request):
                tasks.append(asyncio.create_task(worker(seq, config, problems, test_start, results, debug, args, start_time)))
                seq += 1
        if batch < max_batches - 1:
            await asyncio.sleep(batch_interval_seconds)
    # 等待完成
    await asyncio.gather(*tasks)
    # 寫入 回答檔
    with open(answers_file, 'w', encoding='utf-8') as f:
        # 寫入欄位名稱，將 round 改為 batch，index_in_round 改為 index_in_batch
        f.write('abs_time\trel_time\tttft\tcompletion\tbatch\tindex_in_batch\tprompt_no\tproblem\tanswer\n')
        for r in sorted(results, key=lambda x: x['seq']):
            # 計算批次 (batch) 與在批次內的序號 (index_in_batch)
            batch_no = (r['seq'] - 1) // (batch_concurrent * repeat_per_request) + 1
            index_in_batch = (r['seq'] - 1) % (batch_concurrent * repeat_per_request) + 1
            f.write(f"{r['abs_time']}\t{r['rel_time']}\t{r['ttft']:.6f}\t{r['completion']:.6f}\t{batch_no}\t{index_in_batch}\t{r['prompt_no']}\t{r['problem']}\t{r['answer']}\n")
    # 計算 統計
    ttfts = [r['ttft'] for r in results]
    comps = [r['completion'] for r in results]
    # 計算 TPOT 與 ITL
    tpot_list = []
    itl_list = []
    for r in results:
        # 以 completion 減去 TTFT，除以 token 數（假設 answer token 數）
        answer = r['answer']
        token_count = max(len(answer), 1)
        tpot = (r['completion'] - r['ttft']) / token_count * 1000  # ms
        tpot_list.append(tpot)
        itl_list.append(tpot)  # 近似處理，若有 token-by-token latency 可細分
    def p99(lst):
        if not lst:
            return 0
        idx = int(0.99 * len(lst)) - 1
        idx = max(0, min(idx, len(lst)-1))
        return sorted(lst)[idx]
    stats = {
        'min_TTFT': min(ttfts), 'max_TTFT': max(ttfts), 'avg_TTFT': statistics.mean(ttfts), 'p50_TTFT': statistics.median(ttfts), 'p99_TTFT': p99(ttfts),
        'min_completion_time': min(comps), 'max_completion_time': max(comps), 'avg_completion_time': statistics.mean(comps), 'p50_completion_time': statistics.median(comps), 'p99_completion_time': p99(comps),
        'mean_TPOT': statistics.mean(tpot_list), 'median_TPOT': statistics.median(tpot_list), 'p99_TPOT': p99(tpot_list),
        'mean_ITL': statistics.mean(itl_list), 'median_ITL': statistics.median(itl_list), 'p99_ITL': p99(itl_list),
        'total_success': len(results), 'total_failure': 0
    }
    # 寫入 統計檔
    with open(stats_file, 'w', encoding='utf-8') as f:
        header = '\t'.join(stats.keys())
        values = '\t'.join(str(v) for v in stats.values())
        f.write(header + '\n' + values + '\n')
        # 附加格式化摘要
        f.write('\n')
        f.write('Successful requests:\t\t\t\t{}\n'.format(stats['total_success']))
        f.write('Benchmark duration (s):\t\t\t\t{:.2f}\n'.format((results[-1]['completion'] if results else 0)))
        f.write('Total input tokens:\t\t\t\t\tN/A\n')
        f.write('Total generated tokens:\t\t\t\tN/A\n')
        f.write('Request throughput (req/s):\t\t\tN/A\n')
        f.write('Output token throughput (tok/s):\tN/A\n')
        f.write('Total Token throughput (tok/s):\t\tN/A\n')
        f.write('---------------Time to First Token----------------\n')
        f.write('Mean TTFT (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['avg_TTFT']*1000))
        f.write('Median TTFT (ms):\t\t\t\t\t{:.2f}\n'.format(stats['p50_TTFT']*1000))
        f.write('P99 TTFT (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['p99_TTFT']*1000))
        f.write('-----Time per Output Token (excl. 1st token)------\n')
        f.write('Mean TPOT (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['mean_TPOT']))
        f.write('Median TPOT (ms):\t\t\t\t\t{:.2f}\n'.format(stats['median_TPOT']))
        f.write('P99 TPOT (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['p99_TPOT']))
        f.write('---------------Inter-token Latency----------------\n')
        f.write('Mean ITL (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['mean_ITL']))
        f.write('Median ITL (ms):\t\t\t\t\t{:.2f}\n'.format(stats['median_ITL']))
        f.write('P99 ITL (ms):\t\t\t\t\t\t{:.2f}\n'.format(stats['p99_ITL']))
    # 螢幕輸出同樣內容
    print('\nSuccessful requests:\t\t\t{}'.format(stats['total_success']))
    print('Benchmark duration (s):\t\t\t{:.2f}'.format((results[-1]['completion'] if results else 0)))
    print('Total input tokens:\t\t\tN/A')
    print('Total generated tokens:\t\t\tN/A')
    print('Request throughput (req/s):\t\tN/A')
    print('Output token throughput (tok/s):\tN/A')
    print('Total Token throughput (tok/s):\t\tN/A')
    print('---------------Time to First Token----------------')
    print('Mean TTFT (ms):\t\t\t\t{:.2f}'.format(stats['avg_TTFT']*1000))
    print('Median TTFT (ms):\t\t\t{:.2f}'.format(stats['p50_TTFT']*1000))
    print('P99 TTFT (ms):\t\t\t\t{:.2f}'.format(stats['p99_TTFT']*1000))
    print('-----Time per Output Token (excl. 1st token)------')
    print('Mean TPOT (ms):\t\t\t\t{:.2f}'.format(stats['mean_TPOT']))
    print('Median TPOT (ms):\t\t\t{:.2f}'.format(stats['median_TPOT']))
    print('P99 TPOT (ms):\t\t\t\t{:.2f}'.format(stats['p99_TPOT']))
    print('---------------Inter-token Latency----------------')
    print('Mean ITL (ms):\t\t\t\t{:.2f}'.format(stats['mean_ITL']))
    print('Median ITL (ms):\t\t\t{:.2f}'.format(stats['median_ITL']))
    print('P99 ITL (ms):\t\t\t\t{:.2f}'.format(stats['p99_ITL']))
    # 繪製 圖表
    # 1. TTFT/Completion
    times = [(datetime.strptime(r['rel_time'], '%M:%S.%f').minute*60 + datetime.strptime(r['rel_time'], '%M:%S.%f').second + datetime.strptime(r['rel_time'], '%M:%S.%f').microsecond/1e6) for r in results]
    plt.figure()
    plt.plot(times, ttfts, '.', label='TTFT')
    plt.plot(times, comps, 'x', label='Completion')
    plt.xlabel('執行時刻 (秒)')
    plt.ylabel('秒')
    plt.legend()
    plt.savefig(graph1_file)
    # 2. 平行處理 vs 時間
    # 以批次啟動時間與平行數繪圖
    ev_times = [i * batch_interval_seconds for i in range(max_batches + 1)]
    concs = [batch_concurrent * (i if i <= max_batches else max_batches) for i in range(max_batches + 1)]
    plt.figure()
    plt.step(ev_times, concs, where='post')
    plt.xlabel('執行時刻 (秒)')
    plt.ylabel('當前平行處理數')
    plt.savefig(graph2_file)

if __name__ == '__main__':
    asyncio.run(main())
