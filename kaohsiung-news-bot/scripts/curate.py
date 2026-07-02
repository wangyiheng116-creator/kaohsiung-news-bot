"""
呼叫 Anthropic API，把 collectors.py 抓到的候選新聞整理成
6-10 則、可直接複製貼上 LINE 的高雄新聞晨報。
"""
import os
import json
from datetime import datetime, timezone, timedelta

import anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """你是台灣高雄地方政治新聞編輯，服務對象是一群關注政治的LINE社群夥伴。

你會收到一批候選新聞（標題、摘要、來源、連結），任務是選出當中最重要的 6-10 則，
整理成可以直接複製貼上 LINE 群組的晨報。

## 篩選標準
- 範疇聚焦：高雄市政府/市議會/政策，包括市長、議員、局處首長的動態、政策、質詢、預算、法規
- 2026 年下半年是高雄市長選舉年（民進黨賴瑞隆 對決 國民黨柯志恩），這段時間市政新聞跟選戰新聞會高度重疊：
  - 有實質政策訴求、市政評論、議會質詢內容的 → 收
  - 純粹造勢場面、口水戰、民調數字、選情分析 → 不收
- 排除純社會案件、交通事故、犯罪新聞（除非有明確市府政策後果）、娛樂、體育
- 同一事件有多篇報導時，合併成一則，選最完整的來源
- 若候選新聞不足 6 則，寧可少於 6 則也不要硬湊不相關的內容；若超過 10 則，選最重要的 10 則

## 分類
分成三類，依實際內容數量彈性調整（沒有的類別就不要出現該標題）：
- 🏛 市府動態：市府/局處政策、預算、人事、市長公開行動
- 🗳 議會焦點：議員質詢、提案、三讀、委員會審查
- 📌 其他政策動態：不屬於上面兩類但仍重要的高雄政策新聞

## 輸出格式（純文字，不要用 Markdown 符號，因為要直接貼到 LINE）
第一行固定是：📍高雄新聞晨報｜{日期}（{星期}）
空一行後依類別輸出，每則格式：

{序號}. {一句話重點，包含關鍵人物/機關/數字，30字以內}
　{來源媒體名稱}

序號整份晨報連續編號（1, 2, 3...），不要每類別重新從1開始。
每類別之間空一行，類別標題只有「🏛 市府動態」「🗳 議會焦點」「📌 其他政策動態」這三種，不要自創。
最後不要加任何額外的說明、免責聲明或「以上是根據...」之類的話——直接在最後一則新聞結束。

只輸出晨報本身，不要有其他前言或後語。"""


def _load_candidates_text(items) -> str:
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(
            f"[{i}] 來源：{it.source}｜分類：{it.bucket}\n"
            f"標題：{it.title}\n"
            f"摘要：{it.summary}\n"
            f"連結：{it.link}\n"
        )
    return "\n".join(lines)


def curate(items, api_key: str | None = None) -> str:
    """items 為 collectors.NewsItem 的 list。回傳整理好的晨報純文字。"""
    if not items:
        tz = timezone(timedelta(hours=8))
        today = datetime.now(tz)
        weekday = "一二三四五六日"[today.weekday()]
        return f"📍高雄新聞晨報｜{today.strftime('%-m/%-d')}（{weekday}）\n\n今天沒有抓到符合條件的高雄市政/議會新聞，建議人工確認來源是否正常。"

    client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz)
    weekday = "一二三四五六日"[today.weekday()]

    candidates_text = _load_candidates_text(items)
    user_message = (
        f"今天日期：{today.strftime('%-m/%-d')}（{weekday}）\n\n"
        f"候選新聞如下（共 {len(items)} 則）：\n\n{candidates_text}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return "".join(block.text for block in response.content if block.type == "text").strip()


if __name__ == "__main__":
    # 本機測試用：用假資料測試格式，不呼叫真的 API
    from collectors import NewsItem
    fake_items = [
        NewsItem("測試標題一", "https://example.com/1", "測試摘要", datetime.now(timezone.utc), "自由時報", "市府"),
    ]
    print(_load_candidates_text(fake_items))
