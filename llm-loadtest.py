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
import re  # 用於移除 JSONC 中的註解

async def worker(seq, sem, config, problems, test_start, results):
    # 等待 平行處理 槽位
    await sem.acquire()
    try:
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
            async with session.post(url, json=payload) as resp:
                # TTFT: 讀取第一個字元
                start_ttft = datetime.now()
                await resp.content.read(1)
                t1 = datetime.now()
                text = await resp.text()
                # print("回應內容:", text)
                if not text.strip().startswith('{'):
                    text = '{' + text
                data = json.loads(text)
        t2 = datetime.now()
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
            'answer': ans
        })
    finally:
        sem.release()

async def main():
    # 解析 設定檔
    import sys
    if len(sys.argv) != 2:
        print(f"用法: python {sys.argv[0]} <設定檔>.jsonc 或 .json")
        sys.exit(1)
    cfg_path = sys.argv[1]
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
    base = os.path.splitext(os.path.basename(cfg_path))[0]
    # 計算 seq
    existing = glob.glob(f"{base}.*.answers.txt")
    seq = 1
    for fn in existing:
        try:
            n = int(fn.split('.')[1])
            seq = max(seq, n + 1)
        except:
            continue
    # 檔名
    answers_file = f"{base}.{seq}.answers.txt"
    stats_file = f"{base}.{seq}.stats.txt"
    graph1_file = f"{base}.{seq}.graph.latency.png"
    graph2_file = f"{base}.{seq}.graph.concurrent.png"
    # 讀取 問題列表
    with open(config['problem_file'], 'r', encoding='utf-8') as f:
        lines = [l.strip()[3:] for l in f if l.strip() and l.strip()[0].isdigit()]
    problems = lines[:config['num_problems']]
    # 平行處理 構建
    lp = config['load_profile']
    initial = lp['initial_concurrent']
    ramp = lp.get('ramp_up', [])
    max_conc = lp['max_concurrent']
    total_req = lp['total_requests']
    sem = asyncio.Semaphore(initial)
    current_limit = initial
    # 記錄時間起點
    test_start = datetime.now()
    # 設定 release_sem，動態調整 Semaphore 限制
    def release_sem(add_count):
        nonlocal current_limit
        new_limit = min(current_limit + add_count, max_conc)
        for _ in range(new_limit - current_limit):
            sem.release()
        current_limit = new_limit

    # 計畫 增量
    for ev in ramp:
        after = ev['after_seconds']
        add = ev['add']
        asyncio.get_event_loop().call_later(after, lambda a=add: release_sem(a))
    # 建立 任務
    results = []
    tasks = [asyncio.create_task(worker(i, sem, config, problems, test_start, results)) for i in range(1, total_req + 1)]
    # 等待完成
    await asyncio.gather(*tasks)
    # 寫入 回答檔
    with open(answers_file, 'w', encoding='utf-8') as f:
        for r in sorted(results, key=lambda x: x['seq']):
            f.write(f"{r['abs_time']}\t{r['rel_time']}\t{r['ttft']:.3f}\t{r['completion']:.3f}\t{(r['seq']-1)//len(problems)+1}\t{(r['seq']-1)%len(problems)+1}\t{r['prompt_no']}\t{r['answer']}\n")
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
    ev_times = [0] + [ev['after_seconds'] for ev in ramp]
    concs = [initial] + [min(initial + sum(ev['add'] for ev in ramp[:i]), max_conc) for i in range(1, len(ramp)+1)]
    plt.figure()
    plt.step(ev_times, concs, where='post')
    plt.xlabel('執行時刻 (秒)')
    plt.ylabel('當前平行處理數')
    plt.savefig(graph2_file)

if __name__ == '__main__':
    asyncio.run(main())
