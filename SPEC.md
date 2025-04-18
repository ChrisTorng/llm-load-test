# LLM 壓測規格書

本文件為 llm-loadtest.py 工具之完整 LLM 壓測規格。依據 SPEC.draft.md 要求，說明執行流程、設定格式、輸出結果與統計圖繪製方式。

---

## 1. 簡介

本工具旨在模擬大量對 LLM (大型語言模型) 的連線呼叫，檢驗其在高壓條件下的時效性與穩定性。透過自訂 壓測設定檔，依序讀取問題列表並平行執行，最終輸出 回答檔、統計值檔與統計圖。

## 2. 工具概述

程式名稱：`llm-loadtest.py`

執行方式：
```pwsh
python llm-loadtest.py <設定檔>.json
```

執行後，工具依據設定檔內容 開始 壓測流程並輸出結果。

輸出結果檔名格式:
- 回答檔檔名: "{config_name}.{seq}.answers.txt"
- 統計值檔檔名: "{config_name}.{seq}.stats.txt"
- 統計圖檔檔名: "{config_name}.{seq}.graph.{kind}.png"

以上 `{config_name}` 為設定檔基底名稱（不含 `.json`），`{seq}` 為流水號，`{kind}` 為圖表類型標示。

---

## 3. 問題列表檔案

- 格式：Markdown（副檔名 `.md`）
- 內容：以數字編號列出每題內容，範例如下：
```markdown
1. 這是問題一？
2. 這是問題二？
3. 依此類推...
```
- 在設定檔中以 `problem_file` 欄位指定，並以 `num_problems` 決定取用前 N 題。

---

## 4. 設定檔格式

設定檔為 JSON，必要欄位如下：

```json
{
  "problem_file": "problems1.md",       // 問題列表檔名
  "num_problems": 50,                    // 讀取題數
  "url": "http://localhost:8000/v1/chat/completions",
  "model": "google/gemma-3-1b-it",
  "system_prompt": "You are a helpful assistant.",

  "load_profile": {
    "initial_concurrent": 10,             // 初始同時發出要求數
    "ramp_up": [                         // 之後每個輪次增加量與間隔
      { "after_seconds": 30, "add": 5 },
      { "after_seconds": 60, "add": 10 }
    ],
    "max_concurrent": 100,               // 最多同時要求數上限
    "total_requests": 1000               // 全部要求次數上限
  },
}
```

---

## 5. 壓測流程

1. 解析設定檔，讀取 `problem_file`，取前 `num_problems` 題。
2. 依 `load_profile.initial_concurrent` 第一輪 平行處理要求。
3. 每達一個 `ramp_up` 時間點，額外新增 `add` 額度，直到 `max_concurrent` 或 `total_requests` 閾值。
4. 每一筆要求都記錄時間指標並輸出到 回答檔。

---

## 6. 回答檔  格式

- 副檔名預設為 `.answers.txt`
- 每行以 Tab 分隔欄位，欄位依序：
  1. 請求發出（mm:ss.fff）之當天時間 (hh:mm:ss.fff)
  2. 相對測試開始之分秒（mm:ss.fff）
  3. TTFT（Time To First Token）分秒（mm:ss.fff）
  4. 完整回覆傳回完成之分秒（mm:ss.fff）
  5. 迴圈輪次號
  6. 該輪中之第幾個要求
  7. 問題編號（在問題列表中的序號）
  8. 回答文字內容

範例：
```
16:18:03.567	00:00.000	00:01.234	00:02.500	1	3	3	The winner was the Los Angeles Dodgers.
```

---

## 7. 統計值檔  格式

- 副檔名預設為 `.stats.txt`
- 每行以 Tab 分隔，欄位可依需求彈性擴充，建議包含：
  - min_TTFT
  - max_TTFT
  - avg_TTFT
  - p50_TTFT
  - p90_TTFT
  - min_completion_time
  - max_completion_time
  - avg_completion_time
  - p50_completion_time
  - p90_completion_time
  - total_success
  - total_failure

範例標題行：
```
min_TTFT	max_TTFT	avg_TTFT	p50_TTFT	p90_TTFT	min_completion_time max_completion_time avg_completion_time p50_completion_time p90_completion_time total_success	total_failure
```

---

## 8. 統計圖

需繪製下列兩種 圖表，輸出 PNG 檔：

1. 時效性走勢圖 (line chart)
   - 橫軸：執行時刻 (秒)
   - 縱軸：秒
   - 圖表線包括 min/max/avg/p50/p90 用不同顏色線
   - 圖表數值標點包括 TTFT/completion 用不同標點形狀

2. 請求量 vs 平行處理走勢圖
   - 橫軸：執行時刻 (秒)
   - 縱軸：當前同時要求數

檔名格式依 `graph_file_pattern`，如：
```
loading1.1.graph.latency.png
loading1.1.graph.concurrent.png
```

---

## 9. 檔名命名與覆蓋策略

- 若執行多次同一設定檔，透過 `{seq}` 自動增加流水號，避免覆蓋先前結果。
- 各種輸出檔皆以相同 `{seq}` 保持一致，並於排序時歸為同一組。

---

## 10. 範例

**設定檔** `loading1.json`：
```json
{
  "problem_file": "problems1.md",
  "num_problems": 20,
  "url": "http://localhost:8000/v1/chat/completions",
  ...
}
```

執行：
```pwsh
python llm-loadtest.py loading1.json
```

**輸出**：
```
loading1.1.answers.txt
loading1.1.stats.txt
loading1.1.graph.latency.png
loading1.1.graph.concurrent.png
```

以上即為完整 LLM 壓測 規格書。
