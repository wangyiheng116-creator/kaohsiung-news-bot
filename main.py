"""
高雄新聞晨報 主程式

流程：抓取新聞 → AI整理排序 → 上傳Google文件 → 寄送email通知
用法：python main.py
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from collectors import collect_all
from curate import curate
from gdrive_upload import upload_digest
from send_email import send_digest_email


def main():
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz)
    date_str = today.strftime("%Y%m%d")

    print("=== Step 1: 抓取新聞來源 ===")
    items = collect_all()

    print("\n=== Step 2: AI 整理排序 ===")
    digest_text = curate(items)
    print(digest_text)

    print("\n=== Step 3: 上傳 Google 文件 ===")
    drive_link = None
    try:
        drive_link = upload_digest(digest_text, f"高雄新聞晨報_{date_str}")
        print(f"雲端文件連結：{drive_link}")
    except Exception as e:
        print(f"[警告] Google文件上傳失敗，將只寄送email：{e}")

    print("\n=== Step 4: 寄送 Email 通知 ===")
    try:
        send_digest_email(
            digest_text,
            subject=f"高雄新聞晨報 {today.strftime('%Y-%m-%d')}",
            drive_link=drive_link,
        )
        print("Email 已寄出")
    except Exception as e:
        print(f"[錯誤] Email 寄送失敗：{e}")
        # email失敗但雲端文件成功時，不視為整體失敗
        if not drive_link:
            raise

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
