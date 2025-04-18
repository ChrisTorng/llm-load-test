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
15. 