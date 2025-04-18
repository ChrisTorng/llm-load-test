# LLM 壓測規格草案

我想要檢驗 LLM 在面對大量呼叫時的行為，要做一個壓力測試程式 llm-loadtest.py。

該程式接收一個壓力設定檔檔名 (如 loading1.json)，裡面指定要讀取一個問題列表檔名 (比如 problems1.md)
。
## 問題列表檔案
 
問題列表檔案內容是單純的:
```Markdown
1. 問題一
2. 問題二
```

然後在設定檔中，會指定使用該問題列表檔的問題個數 (因此會使用問題一到指定的問題題數)。

## 設定檔

設定檔中還要指定壓測的相關必要參數，包括:
1. 連線呼叫方法:
   請參考這個呼叫 LLM 指令:
   ```bash
   curl http://localhost:8000/v1/chat/completions \
   -H "Content-Type: application/json" \
   -d '{
       "model": "google/gemma-3-1b-it",
       "messages": [
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "Who won the world series in 2020?"}
       ]
   }'
   ```
   因此設定檔中需要 URL/model/system_prompt 值設定。
2. 壓測壓力量相關值，包括 初始同時發出幾個要求 (第一輪)/幾秒後再增加幾個要求 (第二輪...)/總同時要求量上限/總要求量 等等，請為我設計。
3. 收集壓測結果檔，包括一個回答檔檔名 (預設為設定檔檔名後加 `.{num}.answers.txt`)，統計值檔名 (預設為譳定檔檔名後加 `.{num}.stats.txt`)，統計圖檔名 (後加 `.{num}.graph.{graph_kind}.png`)。
4. 以上若有檔名重覆，則在設定檔名及各類別前加數字 (亦即以上 `.{num}`)，避免覆蓋先前結果，並有利排序 (同一次執行結果之多個檔會在檔名排序後排在一起，不會分開)。比如 `loading1.1.answers.txt`。

## 回答檔

回答檔 (如 `loading.1.answers.txt`) 內以下列欄位逐行輸出，每欄使用 Tab 字元隔開之格式輸出:

1. 該呼叫發出之時間 (以最高秒數小數位數顯示)
2. 該呼叫發出時間相對測試開始執行時間之分秒數(mm:ss)
3. 該呼叫第一個回覆 token 分秒數 (TTFT Time To First Token)
4. 該呼叫完成傳回完整答案之分秒數
5. 第幾輪要求
6. 該輪的第幾個要求
7. 該要求的問題編號
8. 回答答案

## 統計值檔

統計值檔 (如 `loading.1.stats.txt`) 內以 Tab 字元隔開各欄，輸出有利於收集完整壓測統計結果之數值。

## 統計圖

統計圖檔 (如 `loading.1.graph.{graph_kind}.png`) 依上述統計值檔再繪製壓測相關統計圖。請先設計兩種圖給我參考。