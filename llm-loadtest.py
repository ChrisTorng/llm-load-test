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
# 設定中文字體以避免中文顯示錯誤
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False

import re  # 用於移除 JSONC 中的註解
import sys  # 新增 sys 以解析命令列參數
import shutil  # 用於複製檔案

async def worker(seq, config, problems, test_start, results, debug=False):
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
        ]
    }
    # 時間指標
    t0 = datetime.now()
    async with aiohttp.ClientSession() as session:
        payload['stream'] = True  # 使用 串流模式
        async with session.post(url, json=payload) as resp:
            start_ttft_time = None
            text = ''
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
                            if debug:
                                print(content, end='', flush=True)
            t2 = datetime.now()
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

async def main():
    # 解析命令列參數 支援 -d 顯示 串流 訊息
    args = sys.argv[1:]
    debug = False
    if args and args[0] == '-d':
        debug = True
        args = args[1:]
    if not args:
        print(f"用法: python {sys.argv[0]} [-d] <設定檔>.jsonc 或 .json")
        sys.exit(1)
    cfg_path = args[0]
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
                tasks.append(asyncio.create_task(worker(seq, config, problems, test_start, results, debug)))
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
    stats = {
        'min_TTFT': min(ttfts), 'max_TTFT': max(ttfts), 'avg_TTFT': statistics.mean(ttfts), 'p50_TTFT': statistics.median(ttfts), 'p90_TTFT': sorted(ttfts)[int(0.9*len(ttfts))-1],
        'min_completion_time': min(comps), 'max_completion_time': max(comps), 'avg_completion_time': statistics.mean(comps), 'p50_completion_time': statistics.median(comps), 'p90_completion_time': sorted(comps)[int(0.9*len(comps))-1],
        'total_success': len(results), 'total_failure': 0
    }
    # 寫入 統計檔
    with open(stats_file, 'w', encoding='utf-8') as f:
        header = '\t'.join(stats.keys())
        values = '\t'.join(str(v) for v in stats.values())
        f.write(header + '\n' + values + '\n')
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
