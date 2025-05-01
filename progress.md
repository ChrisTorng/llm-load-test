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
19. 我要刪除目前的 problems1.md 所有的問題，請為我建立新的問題組，每組十個問題:
    - problems.easy.md: 很容易不用思考就可以直接回答的問題
    - problems.reason.md: 很困難需要高度推理才能回答的問題
    - problems.fix-length.md: 要求 LLM 的回答能固定長度 token 數量的問題 (為方便壓力測試控制固定的回答長度，避免壓測數據因為回答長度不同導致數據差異太大)，比如說要求由 1 數到 10 且不要加入其他說明文字等等。每個問題所需的答案 tokens 數都要能一致。
    => 有手工修問題，修改 loading.json 為 easy/reason/fix-length.json。
20. (json/md 精簡檔名並搬移位置)
21. 請在建立輸出資料夾後，先將目前的設定檔及問題檔複製到輸出資料夾。
22. 修正執行錯誤。
23. 執行 python .\llm-loadtest.py .\ollama\fix-length\fix-length.json 直到無錯誤。
    => 取消退回
24. 問題檔 md 改為由設定檔 json 之相對路徑。依目前來說兩個檔就是同路徑，因此完全不用寫相對路徑。請修改 py 及所有 json。
25. 複製 json/md 到目標資料夾時，同樣也要套 {seq} 在副檔名之前，與 txt/png 一樣。
    (增加 `.gitignore` 忽略複製後之設定及問題檔)
26. 輸出回答檔中，在目前的答案欄前，再增加輸出原始問題編號，及問題 兩欄。
27. 目前的 fix-length.json 執行結果 fix-length.3.answers.txt 似乎怪怪的。首先 answers 中的 round 是否要更新名稱? 另目前 round 值都是 1，那參考 json 裡的 batch_concurrent=1;max_batches=2;repeat_per_request=2，我看起來 round 值都是 1 的意義似乎不太正確，請依最新的 json 設定值的意義再仔細檢查。
28. 我看回答檔內，第 0 秒開始了六個 request，但目前 json 中 batch_concurrent=3，我預期是看到三個 request 在第 0 秒發出。之後是第四秒。但我要求的 json 設定是 batch_interval_seconds=1，意思是「每隔幾秒啟動下一個批次」，因此我預期是第一秒要看到第二 batch 共三個 request 發出。目前的 request 開始時間感覺不對。
29. #file:fix-length.8.answers.txt:2-8 
目前看到 0 秒發出三個，但我沒有看到一秒發出下一 batch 的三個，而是在 0 秒的三個各自結束後的 5/6/6 秒，才繼續發出第 4/5/6 個 request。應該是第 1 秒又發出第二 batch 的三個 request。

# Ubuntu
1. Windows 下正常，但 Ubuntu 下:
findfont: Generic family 'sans-serif' not found because none of the following families were found: Microsoft YaHei
請支援兩種
2. findfont: Generic family 'sans-serif' not found because none of the following families were found: Noto Sans CJK TC
/home/christorng/GitHub/ChrisTorng/llm-load-test/llm-loadtest.py:214: UserWarning: Glyph 30070 (\N{CJK UNIFIED IDEOGRAPH-7576}) missing from font(s) DejaVu Sans.
  plt.savefig(graph2_file)

# WSL
