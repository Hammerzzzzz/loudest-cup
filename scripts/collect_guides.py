#!/usr/bin/env python3
"""Fetch independent guides, reader picks and community lists into data/raw/guides.jsonl.

Respects robots.txt and skips any page that refuses the request.
"""
import html, json, re, urllib.parse, urllib.request, urllib.robotparser

UA = "Mozilla/5.0 (compatible; LoudestCup/0.1)"
PAGES = [
    ("Gulf News readers", "community", "https://gulfnews.com/food/national-espresso-day-15-best-cafes-for-espresso-in-dubai-picked-by-gulf-news-readers-1.1700749379837"),
    ("Benable", "community", "https://benable.com/jojo21/dubai-s-20-best-coffee-shops-from-artisan-roasts-to-unique-cafe-experiences-f7"),
    ("Grazia Middle East", "news", "https://graziamagazine.com/me/articles/best-coffee-spots-dubai-2025-2/"),
    ("Jdeed", "news", "https://www.jdeedmagazine.com/news/sip-city-where-to-drink-the-best-coffee-in-dubai-right-now"),
    ("tbreak", "news", "https://tbreak.com/food/best-coffee-in-dubai/"),
    ("Danni B in Dubai", "blog", "https://dannibindubai.com/?p=2847"),
    ("Trends MENA", "news", "https://trendsmena.com/?p=269731"),
    ("Roasters App", "community", "https://roasters.app/city-guides/dubai"),
    ("World of Coffee Dubai", "news", "https://dubai.worldofcoffee.org/cafe-network"),
    ("Menu Pages", "news", "https://menupages.ae/featured/dubais-top-16-specialty-coffeehouses/"),
    ("Macau Business", "news", "https://macaubusiness.com/middle-east-coffee-shops-earn-spots-in-the-worlds-100-best-coffee-shops-2026-list/"),
]


def allowed(url):
    p = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt", headers={"User-Agent": UA})
        rp.parse(urllib.request.urlopen(req, timeout=12).read().decode("utf8", "ignore").splitlines())
    except Exception:
        return True
    return rp.can_fetch("*", url)


with open("data/raw/guides.jsonl", "w") as f:
    for name, kind, url in PAGES:
        if not allowed(url):
            print("ROBOTS", name)
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=25).read().decode("utf8", "ignore")
        except Exception as e:
            print("FAIL", name, repr(e)[:70])
            continue
        date = re.search(r'(?:datePublished|article:published_time|dateModified)["\']?\s*[:=]?\s*(?:content=)?["\'](\d{4}-\d\d)', raw)
        body = re.sub(r"(?is)<(script|style|nav|footer)\b.*?</\1>", " ", raw)
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
        f.write(json.dumps({"name": name, "kind": kind, "url": url, "date": date.group(1) if date else None, "text": text}, ensure_ascii=False) + "\n")
        print("OK", name, date.group(1) if date else None, len(text))
