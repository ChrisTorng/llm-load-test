以下預設使用 o4-mini (Preview)/Agent:

1. 請依 SPEC.draft.md 指示，再為我生成完整規格檔 SPEC.md。
2. 手工修改 SPEC.md。
3. 請依 SPEC.md 為我生成完整的程式，加上設定檔及問題列表檔。
4. 手工修改 loading1.json 增加註解後錯誤。
   #terminalSelection
5. 請修改為支援 jsonc 格式。
6. #terminalSelection 仍有錯誤。
   
以下改用 Claude 3.7 Sonnet:

7. Claude 3.7 Sonnet: #terminalSelection 仍有錯誤。
8. GPT-4.1: #terminalSelection 仍有錯誤。
9. Fix using Copilot
```pwsh
uv venv
.\.venv\Scripts\activate
uv pip install asyncio aiohttp statistics matplotlib
uv pip freeze > requirements.txt
```
10. Explain by Copilot

以下改回 o4-mini (Preview):

11. 請修改 SPEC.md，所有輸出檔案均放在設定檔目前資料夾之下，以 {seq} 建立資料夾 (亦即僅有數字名稱資料夾)，數字由 1 開始。檔名仍維持不變，僅有要求全部位於以上資料夾之下。修改完 SPEC.md 再修改相關 py。
12. (修正圖表中文編碼問題)
    ```
    UserWarning: Glyph 22519 (\N{CJK UNIFIED IDEOGRAPH-57F7}) missing from font(s) DejaVu Sans.
      plt.savefig(graph1_file)
    ```
13. UserWarning: Glyph 22519 (\N{CJK UNIFIED IDEOGRAPH-57F7}) missing from font(s) DejaVu Sans.
      plt.savefig(graph1_file)
    請修正圖表內中文編碼錯誤。
14. 目前的 TTFT/completion 時間都一樣。請修改呼叫 LLM 為 streaming 模式，這樣才有正確時間。命令列增加 -d 參數，可以顯示目前接收到的傳回訊息，也要支援 streaming 顯示。
15. 回答檔第一行請加入欄位名稱。秒數小數請與統計檔一致為六位小數。
16. Ask: 目前的 ramp_up 要一組一組加入設定，我現在要連同 initial_concurrent，只做一組的設定，指定每一輪要同時幾個要求，每幾秒增加一輪要求，max_concurrent 要改為同時幾輪，total_requests 要改為每輪總共重覆呼叫幾次。以上的「幾輪」一般會用什麼詞? 請幫我更正。請先為我修改 SPEC.md 之後再修改 json，最後才是 py。
17. 「`requests_per_batch`: 每個批次內每個要求要重覆呼叫幾次（原 total_requests）」不確定是否有誤解。我想的是一個 batch 裡面比如說同時 10 個呼叫，那這 10 個呼叫結束後，還會再重覆相同的呼叫，這個參數要控制說重覆呼叫幾次。也就是若 batch_concurrent=10，重覆呼叫值 5，那就是它們會呼叫 50 次。若 max_batches=3 那代表全部的呼叫 150 次。
請將以上建議幫我修改完成。
18. 請為我撰寫 REAMD.md 提供專案摘要說明。並請說明目前 loading1.json 是依賴本機 Ollama dsr11.5 模型，對應 [deepseek-r1 1.5b](https://ollama.com/library/deepseek-r1:1.5b) 模型。可由 `uv` 建立虛擬環境，`requirements.txt` 還原套件，執行參數為 `python .\llm-loadtest.py .\ollama\1\loading1.json`，有可選參數 `-d` 輸出回覆答案。