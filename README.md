# llm-load-test

llm-load-test 是一套針對大型語言模型（LLM）API 進行壓力測試的程式碼產生器，支援平行處理、多批次呼叫、串流回應時間統計與結果分析。

## 專案摘要
本專案可協助開發者評估 LLM API 在不同負載下的效能表現，並自動產生統計圖表與詳細測試資訊。所有設定皆以 JSONC 格式描述，方便註解與維護。

使用 GitHub Copilot 製作過程紀錄於 [progress.md](progress.md)。規格草案為 [SPEC.draft.md](SPEC.draft.md)，詳細規格為 [SPEC.md](SPEC.md)。

## 依賴模型說明
目前 `ollama/1/easy.json` 設定檔預設依賴本機端 Ollama 伺服器，模型名稱為 `dsr11.5`，對應 [deepseek-r1 1.5b](https://ollama.com/library/deepseek-r1:1.5b) 模型。請先於本機安裝並啟動 Ollama，並下載對應模型。

## 環境設定與執行方式
1. 使用 [uv](https://github.com/astral-sh/uv) 建立虛擬環境：

   Windows:
   ```pwsh
   uv venv
   .\.venv\Scripts\activate
   ```

   Linux:
   ```bash
   uv venv
   source ./.venv/bin/activate
   ```

2. 還原相依套件：
   ```pwsh
   uv pip install -r requirements.txt
   ```

3. 執行測試主程式：
   ```cmd
   python .\llm-loadtest.py .\ollama\easy\easy.json
   ```
   ```bash
   python ./llm-loadtest.py ./ollama/easy/easy.json
   ```

   可選參數
   - `-d`：執行時輸出回覆答案內容，便於除錯與觀察串流回應。
   - `-df`：僅顯示第一個 token 以及時間。
   - `-de`：僅顯示最後一個 token 以及時間。
   - `-dv`：顯示所有 token 以及時間。

4. 執行結果將輸出至 json 設定檔之下數字資料夾，包括:
   - `easy.1.answers.txt` 所有回答答案
   - `easy.1.stats.txt` 統計數據
   - `easy.1.graph.latency.png` 延遲時間圖
   - `easy.1.graph.concurrent.png` 平行處理量圖

## 相關檔案說明
- `llm-loadtest.py`：主程式碼產生器，負責依據設定檔執行壓力測試。
- `requirements.txt`：相依套件清單。
- `ollama`/`local8000`：目前提供本機 Ollama 及任何 8000 port OpenAI 相容 API 測試設定檔資料夾，描述測試參數與目標模型。
- `easy`/`fix-length`/`reason`：容易/固定輸出長度/推理相關 測試問題列表資料夾，以及其下的 `json` 設定檔與 `md` 問題列表檔。

## 授權

[MIT](LICENSE)