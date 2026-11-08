# 研究審查部署與驗收

採用 [官方 Codex GitHub Action](https://learn.chatgpt.com/docs/github-action)，將研究格式寫入 PR Conversation。官方 [Code Review](https://learn.chatgpt.com/docs/third-party/github) 可作額外行內審查，它的公開功能說明未保證這份結構化輸出與逐 PR 預算。現行研究規格與 Issue #10 在 [Draft PR #9](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/9)，W0 證據在 PR #13。

## 第一階段

Research CI 結束後，預設分支上的可信工作流程查找相同倉庫、研究主持人建立、目前 SHA 一致的 PR。分支保護、合併和科學驗收由主持人管理。PR 說明須單獨一行 `Research-Issue: #N`，Issue 須由主持人建立並開啟。相容既有的「對應 #10」寫法。CI 成敗傳給審查員，評論的 PASS 與 CI 成功分開判讀。

只把有容量限制的差異和 Issue 當資料交給模型。模型作業沒有 GitHub 寫入權限、沒有 PR checkout，使用唯讀設定與 drop-sudo。受信任的發布程式只處理已驗證格式，且模型文字以純文字程式碼區塊發布，避免標記、連結與提及被執行。若差異不完整、缺授權或模型失敗，保留 SHA 綁定的 BLOCKED。舊 SHA 無法被當前結果取代。每一 SHA 預留一次，每 PR 最多三筆 live 預留，跳過手動重跑。人工刪除預留會影響計數，因此保留紀錄。作業有逾時，超容量轉人工。

正式部署須由主持人先批准及合併此 Draft，確認 `main` 分支保護，再建立 `research-ai-review` GitHub Environment。限制只能從 `main` 部署，視需求加審批。將專用 OpenAI 專案金鑰儲存於該環境的 `OPENAI_API_KEY` Secret，允許預定模型，設定專案用量警示與速率限制。最後設定 repository variable `RESEARCH_AI_REVIEW_ENABLED=true`，再以受控同倉庫 PR 實測。金鑰勿放倉庫、聊天或 PR。僅批准該專案的研究材料交給模型。無金鑰 smoke 用同一準備、權限隔離和發布路徑，只在主持人推送 `codex/research-ai-review` 且存在同分支 Draft PR 時執行。

GPT-5.4 mini 標準價格每百萬輸入／輸出 token 為 USD 0.75／4.50。例每次累計 20,000 輸入、2,000 輸出約 USD 0.024，三次約 USD 0.072。Codex Action 可能多次呼叫，這是用量情境，並非費用上限。停用 repository variable 可中止後續審查。環境金鑰與有 PR 評論權的可信作業需分離。參考 [官方價格](https://developers.openai.com/api/docs/models/gpt-5.4-mini)。


### 合併前正式模型驗收

主持人可先只允許 `codex/research-ai-review` 部署至 `research-ai-review`，加入環境 Secret 並批准模型費用，再將 repository variable `RESEARCH_AI_REVIEW_PILOT` 設為 `true`。保持正式開關停用，由主持人推送新提交至 Draft PR #15 的分支。驗收預期是模型對明示的合成測例回報 NEEDS_CHANGES，定位 `pilot_ber.py:3` 並指出 1 個錯誤位元／32 個總位元應為 1/32。該案例只驗證真實模型呼叫與報告格式。測試後關閉 pilot 開關，將環境部署限制改回僅 main。正式上線前再以正式 Issue 的受控 PR 驗收研究審查。

## 第二階段設計（未啟用）

第一階段實際模型審查獲主持人驗收並明確批准後，才考慮新增修正執行器。從 GitHub API 讀取可信 bot 評論，驗證工作流程、PR、完整 SHA、Issue、審查格式與 `NEEDS_CHANGES`；禁止從評論抽取或執行命令。主持人核准的 Issue 檔案範圍須使用明列允許清單，排除 main、歷史資料、工作流程及保護分支。評論的自然語言只作建議，Codex 逐項對照原始證據產生 patch，先以唯讀身分驗證，隔離執行測試。通過後由獨立發布者重新核對 PR 頭部 SHA、範圍、測試和輪次，再推送至原實驗分支。自動發送提交的身分需由主持人另行核准，並驗證後續 CI 及獨立審查會觸發。現行階段只允許主持人觸發；未來自動提交若獲准，須對專用身分另建明確信任規則。

以 PR 為單位記錄已消耗輪次，最多兩輪。遇過期或衝突意見、範圍不明、研究方向變更、測試失敗或用盡輪次，停止並標記 BLOCKED。合併由主持人決定。第一階段單元測試已覆蓋報告狀態、SHA 與不可信文字；第二階段發布前須另以假評論測試舊 SHA、冒名、第三輪和越界變更。
