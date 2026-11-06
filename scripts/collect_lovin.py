#!/usr/bin/env python3
"""Collect Lovin Dubai articles naming each cafe into data/raw/lovin.jsonl.

Uses the site's public search, which its robots.txt allows. Paid posts in its
/sponsored/ section are skipped.
"""
import html, json, re, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; LoudestCup/0.1)"}
BASE = "https://lovin.co/dubai/en/"
cafes = json.load(open("data/cafes.json"))["cafes"]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf8", "ignore")


seen = set()
with open("data/raw/lovin.jsonl", "w") as f:
    for c in cafes:
        try:
            page = get(BASE + "?" + urllib.parse.urlencode({"s": c["aliases"][0]}))
        except Exception as e:
            print(c["name"], "ERR", repr(e)[:80], flush=True)
            time.sleep(3)
            continue
        links = re.findall(r'href="(https://lovin\.co/dubai/en/(?:[\w-]+/){1,3}[\w-]+/)"', page)
        for u in dict.fromkeys(links):
            if u in seen or "/sponsored/" in u or re.search(r"/(category|tag|author|page)/", u):
                continue
            seen.add(u)
            try:
                raw = get(u)
            except Exception:
                continue
            d = re.search(r'article:published_time" content="(\d{4}-\d\d-\d\d)', raw) or re.search(r'"datePublished":"(\d{4}-\d\d-\d\d)', raw)
            t = re.search(r"<title>(.*?)</title>", raw, re.S)
            body = re.sub(r"(?is)<(script|style|nav|footer|aside)\b.*?</\1>", " ", raw)
            f.write(json.dumps({"site": "https://lovin.co", "id": u, "url": u, "date": d.group(1) if d else "",
                                "title": html.unescape(t.group(1)).split(" - Lovin")[0].strip() if t else "Lovin Dubai",
                                "text": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))}, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(.8)
        time.sleep(1)
print("finished", len(seen), flush=True)
