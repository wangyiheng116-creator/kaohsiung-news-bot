#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高雄要聞｜手機雲端網頁版
- 手機打開網址即可使用
- 一鍵更新 / 一鍵複製全部
- 抓取 Google News RSS 24 小時內高雄新聞
- 背景排程：每天台灣時間 09:00 自動更新快取
- 可部署到 Render / Replit / Railway 等 Python Web Service
"""

import html
import json
import os
import re
import ssl
import threading
import time
import urllib.parse as P
import urllib.request as U
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime as PD
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl._create_unverified_context()

TW = timezone(timedelta(hours=8))
CACHE_FILE = os.environ.get("CACHE_FILE", "news_cache.json")
PORT = int(os.environ.get("PORT", "8080"))
HOST = os.environ.get("HOST", "0.0.0.0")
QUERY = os.environ.get("NEWS_QUERY", "高雄 when:1d")
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "30"))

OK = [
    "自由時報", "聯合", "經濟日報", "中時", "中國時報", "工商時報", "ETtoday", "中央社", "鏡週刊", "鏡周刊", "CTWANT", "周刊王",
    "壹蘋", "知新聞", "鉅聞天下", "三立", "TVBS", "民視", "公視", "太報", "新頭殼", "Newtalk", "風傳媒", "NOWnews", "今日新聞",
    "菱傳媒", "芋傳媒", "信傳媒", "上報", "鏡新聞", "中天", "台視", "華視", "中視", "年代", "壹電視", "Yahoo", "台灣時報", "中華日報"
]

HARD = [
    "市長", "市府", "市政", "議會", "議員", "立委", "里長", "政策", "施政", "預算", "質詢", "選舉", "參選", "候選", "民調", "政黨", "國民黨",
    "民進黨", "民眾黨", "時代力量", "造勢", "藍白", "藍綠", "綠營", "藍營", "黨", "陳其邁", "柯志恩", "賴瑞隆", "黃捷", "罷免", "公投", "政見",
    "首長", "局長", "處長", "中央", "內政部", "行政院", "立法院", "監察院", "法案", "條例", "修法", "政風", "弊案", "貪", "收賄", "起訴",
    "檢調", "約談", "判決", "警", "消防", "火警", "火災", "車禍", "事故", "死", "重傷", "傷者", "詐騙", "毒品", "命案", "槍", "逮捕",
    "通緝", "性侵", "家暴", "虐", "抗議", "陳情", "自救會", "工安", "氣爆", "爆炸", "外洩", "罷工", "開罰", "稽查", "查獲", "食安",
    "中毒", "違規", "違法", "取締", "公聽會", "說明會", "遊行", "連署", "反彈", "停水", "停電", "缺水", "限水", "物價", "通膨",
    "交通", "捷運", "輕軌", "公車", "國道", "道路", "塞車", "淹水", "積水", "停班", "停課", "颱風", "豪雨", "地震", "空污", "登革熱",
    "疫情", "防疫", "醫院", "醫療", "缺藥", "長照", "社福", "社宅", "社會住宅", "住宅", "都更", "危老", "房屋稅", "囤房", "地價稅",
    "補助", "津貼", "敬老", "身障", "育兒", "托育", "台積電", "半導體", "產業", "投資", "設廠", "園區", "就業", "失業", "勞工",
    "工廠", "招商", "觀光", "經濟", "農業", "漁業", "缺工", "淨零", "光電", "台電", "中油", "污染", "汙染", "開發", "工程", "建設",
    "亞灣", "港區"
]

EXCLUDE = [
    "演唱會", "開唱", "演唱", "巡演", "彩排", "見面會", "簽售", "應援", "寵粉", "迷妹", "迷弟", "私服", "街拍", "藝人", "明星", "偶像",
    "男神", "女神", "天王", "女團", "男團", "天團", "歌手", "樂團", "主唱", "演員", "主持人", "綜藝", "實境秀", "真人秀", "影劇", "劇組",
    "票房", "專輯", "單曲", "新歌", "MV", "出道", "緋聞", "戀情", "熱戀", "認愛", "放閃", "閃婚", "分手", "復合", "劈腿", "婚變",
    "曬照", "辣照", "寫真", "泳裝", "比基尼", "深V", "事業線", "性感", "名媛", "名模", "網紅", "網美", "直播主", "YouTuber", "金曲",
    "金鐘", "金馬", "星二代", "粉絲", "演藝圈", "子瑜", "周子瑜", "TWICE", "BLACKPINK", "蔡依林", "周杰倫", "五月天", "張惠妹", "蕭敬騰",
    "林俊傑", "田馥甄", "楊丞琳", "玖壹壹", "告五人", "盧廣仲", "陳美鳳", "孫芸芸", "短片", "微電影", "僑生", "才藝", "徵件",
    "徵選", "校慶", "園遊會", "科展", "說故事", "演講比賽", "樂儀隊", "畢業典禮", "繪畫比賽", "作文比賽", "競賽"
]

REALTY = ["房價", "建案", "預售", "首購", "購屋", "房市", "成交", "建商", "豪宅", "屋齡", "新成屋", "中古屋", "每坪", "實登", "地產", "房產", "售價", "開價", "總價", "坪數", "低總價", "小宅", "買房", "賣房", "房仲"]
POLICY = ["政策", "社宅", "社會住宅", "公宅", "青年住宅", "都更", "危老", "房屋稅", "囤房", "地價稅", "補貼", "租金", "市府", "內政部", "平均地權", "打炒房", "打房", "條例", "修法", "法案", "議會", "質詢", "違建", "公有地"]

PAGE = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>高雄要聞</title>
<style>
:root{--ink:#f3f3f6;--sub:#a6a6b0;--accent:#d8f94e;--aink:#1b1c1e}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html{background:#191a1d}
body{margin:0;min-height:100vh;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro TC","PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;-webkit-font-smoothing:antialiased;line-height:1.45;background:radial-gradient(1100px 560px at 88% -8%,rgba(216,249,78,.12),transparent 60%),radial-gradient(1000px 680px at -8% 112%,rgba(90,132,205,.14),transparent 60%),#191a1d;background-attachment:fixed}.hd{position:sticky;top:10px;z-index:9;padding:10px 12px 0;max-width:780px;margin:0 auto}.glass{background:linear-gradient(150deg,rgba(70,70,80,.55),rgba(38,38,44,.42));backdrop-filter:blur(26px) saturate(180%);-webkit-backdrop-filter:blur(26px) saturate(180%);border:1px solid rgba(255,255,255,.12);border-radius:26px;box-shadow:0 10px 34px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.16);padding:18px 20px}.row{display:flex;align-items:center;gap:12px}.star{width:34px;height:34px;flex:0 0 auto;border-radius:50%;background:var(--accent);color:var(--aink);display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800}h1{margin:0;font-size:27px;font-weight:600;letter-spacing:-.5px}.meta{margin:8px 0 0;font-size:13px;color:var(--sub);font-weight:500}.bar{display:flex;gap:10px;margin-top:14px}button{border:0;font-weight:750;font-family:inherit;cursor:pointer;transition:transform .08s,filter .2s;font-size:15px}button:active{transform:scale(.98)}#c{flex:1;background:var(--accent);color:var(--aink);padding:14px 22px;border-radius:980px}#c:hover{filter:brightness(1.05)}#r{background:rgba(255,255,255,.14);color:var(--ink);padding:14px 20px;border-radius:980px;border:1px solid rgba(255,255,255,.1)}.wrap{padding:14px 16px calc(50px + env(safe-area-inset-bottom));max-width:780px;margin:0 auto}ul{list-style:none;margin:0;padding:0}.card{background:rgba(42,42,49,.66);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.07);border-radius:20px;padding:17px 19px;margin-bottom:12px;transition:transform .12s,background .2s}.card:active{transform:scale(.995)}.card a{color:var(--ink);text-decoration:none;font-size:16.5px;font-weight:620;letter-spacing:-.2px;display:block;line-height:1.42}.mrow{margin-top:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}.chip{font-size:12px;font-weight:750;padding:6px 12px;border-radius:980px}.chip.s{background:rgba(216,249,78,.16);color:var(--accent)}.chip.d{background:rgba(255,255,255,.08);color:var(--sub)}.empty{text-align:center;color:var(--sub);padding:56px 20px;font-size:15px}.foot{color:var(--sub);font-size:12px;text-align:center;margin-top:24px;opacity:.7}#raw{width:100%;height:38vh;display:none;margin-top:12px;border:0;border-radius:16px;padding:14px;font-size:13px;font-family:inherit;background:rgba(42,42,49,.8);color:var(--ink)}.toast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%) translateY(16px);background:var(--accent);color:var(--aink);padding:14px 26px;border-radius:980px;font-size:14.5px;font-weight:750;opacity:0;pointer-events:none;transition:.3s cubic-bezier(.2,.8,.2,1);box-shadow:0 12px 34px rgba(0,0,0,.5)}.toast.on{opacity:1;transform:translateX(-50%) translateY(0)}.spin{display:inline-block;width:13px;height:13px;border:2px solid rgba(255,255,255,.25);border-top-color:var(--accent);border-radius:50%;animation:sp .8s linear infinite;vertical-align:-1px;margin-right:7px}@keyframes sp{to{transform:rotate(360deg)}}
</style></head><body>
<div class="hd"><div class="glass"><div class="row"><span class="star">✦</span><h1>高雄要聞</h1></div><div class="meta" id="meta">載入中…</div><div class="bar"><button id="c">一鍵複製全部</button><button id="r">更新</button></div></div></div>
<div class="wrap"><ul id="list"></ul><div class="empty" id="empty"></div><textarea id="raw" readonly></textarea><div class="foot">只收錄 24 小時內・政治／市政／社會／民生／經濟</div></div><div class="toast" id="toast"></div>
<script>
var TX="",NL=String.fromCharCode(10);function $(i){return document.getElementById(i)}function toast(m){var t=$("toast");t.textContent=m;t.classList.add("on");setTimeout(function(){t.classList.remove("on")},2200)}function build(d){var o=["【高雄要聞】"+d.date,""];(d.items||[]).forEach(function(it,i){o.push((i+1)+". "+it.t+"（"+it.src+"）");o.push(it.url);o.push("")});return o.join(NL).trim()}async function cp(){if(!TX){toast("目前沒有內容可複製");return}try{await navigator.clipboard.writeText(TX);toast("已複製，可以貼上");return}catch(e){}var r=$("raw");r.style.display="block";r.value=TX;r.focus();r.select();toast("已選取，請長按複製")}function render(d){var cnt=(d.items||[]).length;$("meta").innerHTML=cnt?("共 "+cnt+" 則・更新 "+d.updated):"目前沒有符合的新聞";TX=build(d);$("raw").value=TX;var u=$("list");u.innerHTML="";$("empty").textContent=cnt?"":"24 小時內暫無符合的高雄硬新聞，稍後再按「更新」。";(d.items||[]).forEach(function(it){var li=document.createElement("li");li.className="card";var a=document.createElement("a");a.href=it.url;a.target="_blank";a.rel="noopener";a.textContent=it.t;var mr=document.createElement("div");mr.className="mrow";var cs=document.createElement("span");cs.className="chip s";cs.textContent=it.src;var cd=document.createElement("span");cd.className="chip d";cd.textContent=it.d;mr.appendChild(cs);mr.appendChild(cd);li.appendChild(a);li.appendChild(mr);u.appendChild(li)})}async function load(force){$("meta").innerHTML="<span class=spin></span>更新中…";try{var url="/api/news"+(force?"?refresh=1":"");var res=await fetch(url,{cache:"no-store"});render(await res.json());if(force)toast("已更新")}catch(e){$("meta").textContent="更新失敗，請確認網路"}}$("r").onclick=function(){load(true)};$("c").onclick=cp;load(false);
</script></body></html>"""


def _tag(seg, tag):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), seg, re.S)
    if not m:
        return ""
    return html.unescape(re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m.group(1), flags=re.S)).strip()


def fetch_news():
    url = "https://news.google.com/rss/search?q=" + P.quote(QUERY) + "&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    req = U.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    xml = U.urlopen(req, timeout=25, context=CTX).read().decode("utf-8", "replace")
    now = datetime.now(timezone.utc)
    out, seen = [], set()

    for seg in re.findall(r"<item>(.*?)</item>", xml, re.S):
        title, link, pub, src = _tag(seg, "title"), _tag(seg, "link"), _tag(seg, "pubDate"), _tag(seg, "source")
        if not title or not pub:
            continue
        try:
            ts = PD(pub)
        except Exception:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = now - ts
        if age > timedelta(hours=24) or age < timedelta(hours=-1):
            continue
        if not any(o in src for o in OK):
            continue
        clean = re.sub(r"\s+-\s+[^-]+$", "", title)
        if not any(h in clean for h in HARD):
            continue
        if any(x in clean for x in EXCLUDE):
            continue
        if any(r in clean for r in REALTY) and not any(pk in clean for pk in POLICY):
            continue
        key = clean[:16]
        if key in seen:
            continue
        seen.add(key)
        out.append((ts, clean, src, link))

    out.sort(reverse=True)
    out = out[:MAX_ITEMS]
    d = now.astimezone(TW)
    return {
        "date": f"{d.year}/{d.month}/{d.day}",
        "updated": f"{d.hour:02d}:{d.minute:02d}",
        "items": [
            {"t": title, "src": src, "d": f"{ts.astimezone(TW).month}/{ts.astimezone(TW).day}", "url": link}
            for ts, title, src, link in out
        ],
        "generated_at": d.isoformat(),
    }


def read_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_cache(data):
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_FILE)


def update_cache():
    data = fetch_news()
    write_cache(data)
    return data


def get_news(force=False):
    if force:
        return update_cache()
    cached = read_cache()
    if cached:
        return cached
    return update_cache()


def scheduler_loop():
    """每天台灣時間 09:00 後自動更新一次。"""
    last_day = None
    while True:
        now = datetime.now(TW)
        if now.hour == 9 and last_day != now.date().isoformat():
            try:
                update_cache()
                last_day = now.date().isoformat()
                print(f"[{now.isoformat()}] cache updated")
            except Exception as e:
                print(f"[{now.isoformat()}] scheduled update failed: {e}")
        time.sleep(30)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/news"):
            try:
                parsed = P.urlparse(self.path)
                qs = P.parse_qs(parsed.query)
                force = qs.get("refresh", ["0"])[0] == "1"
                body = json.dumps(get_news(force=force), ensure_ascii=False).encode("utf-8")
            except Exception as e:
                fallback = read_cache()
                if fallback:
                    fallback["warning"] = f"更新失敗，顯示快取：{e}"
                    body = json.dumps(fallback, ensure_ascii=False).encode("utf-8")
                else:
                    body = json.dumps({"date": "", "updated": "", "items": [], "error": str(e)}, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
            return

        if self.path.startswith("/health"):
            self._send(200, "text/plain; charset=utf-8", b"ok")
            return

        self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))


if __name__ == "__main__":
    try:
        get_news(force=True)
    except Exception as e:
        print(f"startup fetch failed: {e}")
    threading.Thread(target=scheduler_loop, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"高雄要聞已啟動：http://{HOST}:{PORT}/")
    server.serve_forever()
