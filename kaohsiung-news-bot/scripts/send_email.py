"""
用 Gmail SMTP 寄送每日摘要通知。

事前準備（見 README）：
  1. 你的 Google 帳號要先開「兩步驟驗證」
  2. 到 Google 帳號設定 → 安全性 → 應用程式密碼，產生一組給這個腳本用
  3. GMAIL_ADDRESS：你的 gmail 地址
     GMAIL_APP_PASSWORD：上面產生的應用程式密碼（不是你的登入密碼）
     TO_EMAIL：收件信箱（可以跟 GMAIL_ADDRESS 相同，寄給自己）
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_digest_email(text: str, subject: str, drive_link: str | None = None) -> None:
    gmail_address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_email = os.environ.get("TO_EMAIL", gmail_address)

    body = text
    if drive_link:
        body += f"\n\n雲端文件連結：{drive_link}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_address, app_password)
        server.send_message(msg)


if __name__ == "__main__":
    send_digest_email("測試內容", "測試信件")
    print("已寄出測試信")
