"""
高雄市政/議會新聞收集器

來源：
  - 10 家媒體，各用「高雄市政府」「高雄市議會」兩組關鍵字跑 Google News RSS
  - 高雄市政府官方新聞（kcg.gov.tw，原生 RSS）

輸出：collect_all() 回傳去重後的 NewsItem list。
"""
import re
import time
import feedparser
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
from dataclasses import dataclass
from typing import Optional

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_GNEWS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    published: datetime
    source: str
    bucket: str  # "市府" or "議會"


# ─── 10 家媒體對應網域 ─────────────────────────────────────────
MEDIA_DOMAINS = {
    "ETtoday新聞雲": "ettoday.net",
    "鏡週刊": "mirrormedia.mg",
    "自由時報": "ltn.com.tw",
    "聯合新聞網": "udn.com",
    "中國時報": "chinatimes.com",
    "CTWANT": "ctwant.com",
    "知新聞": "knews.tw",
    "壹蘋新聞網": "nextapple.com",
    "鉅聞天下": "bigmedia.com.tw",
    "中央社": "cna.com.tw",
}

# 每家媒體會分別用這兩組關鍵字搜尋
KEYWORD_BUCKETS = {
    "市府": "高雄市政府",
    "議會": "高雄市議會",
}

# 高雄市政府官方新聞（原生 RSS，不用 Google News 代理）
KAOHSIUNG_GOV_FEEDS = {
    "高雄市府-最新消息": "https://www.kcg.gov.tw/OpenData.aspx?SN=FB01D469347C76A7",
    "高雄市府-市政新聞": "https://www.kcg.gov.tw/OpenData.aspx?SN=D33B55D537402BAA",
}


def _build_media_feeds():
    """組出 10 家媒體 x 2 關鍵字 = 20 組 Google News RSS 查詢"""
    feeds = {}
    for media_name, domain in MEDIA_DOMAINS.items():
        for bucket, keyword in KEYWORD_BUCKETS.items():
            query = f"site:{domain}+{keyword}"
            feeds[(media_name, bucket)] = _GNEWS.format(query=query)
    return feeds


def _parse_dt(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        s = getattr(entry, attr, None)
        if s:
            try:
                return dateparser.parse(s).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def fetch_feed(url: str, source: str, bucket: str, cutoff_start: datetime) -> list[NewsItem]:
    """抓取單一 RSS feed，只回傳 cutoff_start 之後的文章"""
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  [錯誤] {source}/{bucket}: {e}")
        return []

    items = []
    for entry in feed.entries:
        pub = _parse_dt(entry)
        if pub is None or pub < cutoff_start:
            continue

        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        summary = _HTML_TAG_RE.sub("", summary).strip()[:300]

        if title and link:
            items.append(NewsItem(
                title=title, link=link, summary=summary,
                published=pub, source=source, bucket=bucket,
            ))
    return items


def collect_all(hours_back: int = 30, verbose: bool = True) -> list[NewsItem]:
    """
    收集所有來源。hours_back：往回抓幾小時（預設 30，抓昨晚到今早，留緩衝）。
    回傳去重後的 NewsItem list（以 link 去重）。
    """
    cutoff_start = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)

    if verbose:
        print(f"收集起始時間（UTC）：{cutoff_start.isoformat()}")

    all_items: list[NewsItem] = []
    seen_links: set[str] = set()

    # 10 家媒體 x 2 關鍵字
    media_feeds = _build_media_feeds()
    for (media_name, bucket), url in media_feeds.items():
        items = fetch_feed(url, media_name, bucket, cutoff_start)
        if verbose:
            print(f"[{media_name}/{bucket}] {len(items)} 篇")
        for item in items:
            if item.link not in seen_links:
                seen_links.add(item.link)
                all_items.append(item)
        time.sleep(0.3)  # 禮貌性間隔

    # 高雄市政府官方新聞（歸「市府」類）
    for source_name, url in KAOHSIUNG_GOV_FEEDS.items():
        items = fetch_feed(url, source_name, "市府", cutoff_start)
        if verbose:
            print(f"[{source_name}] {len(items)} 篇")
        for item in items:
            if item.link not in seen_links:
                seen_links.add(item.link)
                all_items.append(item)

    if verbose:
        print(f"\n共收集 {len(all_items)} 篇（去重後）")

    return all_items


if __name__ == "__main__":
    # 本機測試用：python -m scripts.collectors
    results = collect_all()
    for r in results[:10]:
        print(f"- [{r.source}/{r.bucket}] {r.title}")
