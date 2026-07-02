# 高雄新聞晨報機器人

每天台北時間 07:30 自動執行：抓取 10 家媒體＋高雄市府官方新聞中跟「高雄市政府／高雄市議會」有關的內容，
交給 AI 整理成 6-10 則重點，存成 Google 文件並寄 email 通知，讓你 9 點前就能複製貼上 LINE 社群。

## 這個帳號要用誰的？

這份程式碼預設用**你自己的** GitHub／Google／Gmail 帳號，跟 NPP 共用的 `nppofficetw` 體系是分開的。
如果你想改成掛在共用帳號下（例如想讓其他同事也能維護），跟負責共用帳號的同事說一聲，
用共用的 GitHub PAT 走 `gh repo create` 到 `nppofficetw` 底下即可，其他步驟不變。

## 開始前要準備的東西（核取清單）

- [ ] 一個 GitHub 帳號（免費）
- [ ] 一個 Anthropic API 金鑰（[console.anthropic.com](https://console.anthropic.com) 申請，需綁信用卡，但這個用量一個月估計不到 2 美元）
- [ ] 一個 Google Cloud 專案 + 服務帳號（免費，用來讓程式自動寫入你的 Google Drive）
- [ ] 一個 Gmail 帳號 + 應用程式密碼（免費，用來寄通知信）

以下步驟一步一步做，每一步都做完再往下走。網站介面可能會隨時間改版，如果畫面跟說明不完全一樣，
找關鍵字（如「服務帳號」「Secrets」）通常還是能找到對應功能。

---

## 步驟 1：建立 GitHub repo，把程式碼傳上去

1. 到 [github.com/new](https://github.com/new) 建立一個新 repo，例如取名 `kaohsiung-news-bot`，設為 **Private**（私人）。
2. 把這個資料夾裡的所有檔案上傳上去（可以直接在 GitHub 網頁上用「Add file → Upload files」把整個資料夾拖上去，
   或是如果你熟悉 git 指令：

   ```bash
   cd kaohsiung-news-bot
   git init
   git add -A
   git commit -m "初始版本"
   git branch -M main
   git remote add origin https://github.com/<你的帳號>/kaohsiung-news-bot.git
   git push -u origin main
   ```

---

## 步驟 2：申請 Anthropic API 金鑰

1. 到 [console.anthropic.com](https://console.anthropic.com) 註冊/登入，綁定付款方式。
2. 左側選單找到「API Keys」，建立一組新金鑰，複製起來（只會顯示一次，先存到安全的地方）。

---

## 步驟 3：設定 Google 服務帳號（給 Drive 上傳用）

服務帳號是一個「機器人專用」的 Google 身分，讓沒有瀏覽器的 GitHub Actions 也能寫入你的 Drive，
不用像平常一樣跳出「用 Google 登入」的畫面。

1. 到 [Google Cloud Console](https://console.cloud.google.com/)，建立一個新專案（或用現有的）。
2. 左上選單找「API 和服務 → 已啟用的 API 和服務」，點「啟用 API 和服務」，搜尋 **Google Drive API**，啟用它。
3. 左側選單找「IAM 與管理 → 服務帳號」，點「建立服務帳號」，名稱隨意（例如 `kaohsiung-news-bot`），一路下一步到完成。
4. 建好後點進這個服務帳號，找「金鑰」頁籤 → 「新增金鑰」→「建立新的金鑰」→ 選 **JSON** → 下載。
   這個 JSON 檔案的**整份內容**之後會存成一個 GitHub Secret。
5. 打開下載的 JSON 檔案，找到 `"client_email"` 那一行，會是類似
   `kaohsiung-news-bot@你的專案.iam.gserviceaccount.com` 的一串 email，複製起來。
6. 到你的 Google Drive，建立一個資料夾（例如「高雄新聞晨報」），對這個資料夾按右鍵「共用」，
   把上一步複製的服務帳號 email 加進去，權限選「編輯者」。
7. 打開這個資料夾，網址列會是 `https://drive.google.com/drive/folders/一長串ID`，複製那段 ID。

---

## 步驟 4：設定 Gmail 應用程式密碼

1. 你的 Google 帳號要先開啟「兩步驟驗證」（設定 → 安全性）。
2. 開啟後，同一頁面找「應用程式密碼」，建立一組新的（應用程式可以隨意選「郵件」或自訂名稱）。
3. 會產生一組 16 位數的密碼，複製起來——這不是你平常登入用的密碼，是專門給程式用的。

---

## 步驟 5：把所有金鑰加到 GitHub Secrets

回到你的 GitHub repo 頁面 → **Settings → Secrets and variables → Actions → New repository secret**，
依序加入以下 6 組（名稱要完全一樣）：

| Secret 名稱 | 值 |
|---|---|
| `ANTHROPIC_API_KEY` | 步驟 2 的金鑰 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 步驟 3 下載的 JSON 檔案，**整份內容**貼進去 |
| `GDRIVE_FOLDER_ID` | 步驟 3 最後複製的資料夾 ID |
| `GMAIL_ADDRESS` | 你的 gmail 地址 |
| `GMAIL_APP_PASSWORD` | 步驟 4 的 16 位數應用程式密碼 |
| `TO_EMAIL` | 收件信箱（可以跟 GMAIL_ADDRESS 填一樣，寄給自己） |

---

## 步驟 6：手動測試一次

1. 到 repo 頁面上方的 **Actions** 頁籤。
2. 左側應該會看到「高雄新聞晨報」這個 workflow，點進去。
3. 右側有「Run workflow」按鈕，點一下手動觸發一次。
4. 等 1-2 分鐘，重新整理，點進剛剛那次執行紀錄，可以展開每個步驟看log；
   如果哪一步失敗，log 裡通常會直接寫出是哪個環節（例如金鑰打錯、資料夾沒共用權限等）。
5. 成功的話，去檢查：Google Drive 資料夾裡有沒有新文件、信箱有沒有收到信。

測試成功後，就不用再管它了——**每天台北時間 07:30 會自動跑一次**，8 點前後你信箱/雲端文件就會有結果。

---

## 之後想調整的話

- **想換抓取時間**：改 `.github/workflows/daily-digest.yml` 裡的 `cron: '30 23 * * *'`（時間是 UTC，要减8小時換算回台北時間）。
- **想調整篩選標準/選題數量/語氣**：改 `scripts/curate.py` 裡的 `SYSTEM_PROMPT`。
- **想加減新聞來源**：改 `scripts/collectors.py` 裡的 `MEDIA_DOMAINS`。
- **想省一點費用**：把 `curate.py` 裡 `MODEL = "claude-sonnet-5"` 改成 `"claude-haiku-4-5-20251001"`，
  品質會稍微簡單一點，但費用降到約 1/3。

## 目前版本的已知限制

- 每次執行只抓「過去 30 小時內」的新聞，沒有記錄「上次已經抓過哪些」，
  如果同一則新聞連續兩天都在候選名單裡，理論上有極小機率被選進兩天的晨報。之後可以加一個
  「已發送清單」存到 repo 裡來解決，目前先用 30 小時窗口＋AI 篩選降低這個機率。
- 高雄市議會官網本身也有 RSS 訂閱區（kcc.gov.tw），目前沒有另外串接，先靠 10 家媒體用
  「高雄市議會」關鍵字搜尋覆蓋議員質詢/提案動態。如果之後發現漏新聞，可以再加這個來源。
