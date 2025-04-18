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
