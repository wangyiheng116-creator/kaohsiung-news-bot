# 高雄要聞｜手機雲端網頁版

這是由原本的 `高雄要聞.command` 改成的手機可用網頁版。

## 功能

- 手機打開網址即可使用
- 一鍵更新 24 小時內高雄要聞
- 一鍵複製全部文字，可直接貼到 LINE / Facebook / Threads / 備忘錄
- 每天台灣時間 09:00 自動更新快取
- 保留原本的新聞篩選邏輯：知名媒體、24 小時內、排除演藝娛樂與純房市新聞

## 本機測試

```bash
pip install -r requirements.txt
python app.py
```

打開：

```text
http://127.0.0.1:8080/
```

## Render 部署

1. 把整個資料夾上傳到 GitHub。
2. 到 Render 新增 `Web Service`。
3. 連接這個 GitHub Repository。
4. 設定：
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`python app.py`
5. 部署完成後，用 Render 提供的網址在手機打開即可。

Render 會自動提供 HTTPS，所以手機的一鍵複製功能比較穩定。

> 注意：Render 免費方案可能會休眠。如果早上 9:00 服務剛好睡著，排程不一定會準時跑；但你打開頁面後按「更新」仍可手動抓最新。

## Replit 部署

1. 建立新的 Python Repl。
2. 上傳這些檔案。
3. 在 Shell 執行：

```bash
pip install -r requirements.txt
python app.py
```

4. Replit 會產生一個網址，用手機打開即可。

## 可以調整的設定

在環境變數中調整：

- `NEWS_QUERY`：預設 `高雄 when:1d`
- `MAX_ITEMS`：預設 `30`
- `PORT`：預設 `8080`，Render 會自動提供

## 手機使用方式

1. 用手機打開部署後的網址。
2. 按「更新」抓最新新聞。
3. 按「一鍵複製全部」。
4. 到 LINE / Facebook / Threads / 備忘錄貼上。
