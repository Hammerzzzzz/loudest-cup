#!/usr/bin/env python3
"""Check article and cafe links, and read publish dates from the articles.

Writes data/link_status.json: {url: {"dead": bool, "date": "YYYY-MM" or ""}}.
Only 404 and 410 count as dead, as 403 usually means a site refuses bots.
Dates already found are kept, so weekly runs stay quick.
"""
import concurrent.futures as cf, json, os, re, urllib.error, urllib.request

PATH = "data/link_status.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; LoudestCup/0.1)"}
DATE = re.compile(r'(?:article:published_time"\s+content="|"datePublished"\s*:\s*"|"dateCreated"\s*:\s*"|<time[^>]+datetime=")(20\d\d-\d\d)')
PATH_DATE = re.compile(r"/(20\d\d)/(\d\d)/")


def check(url):
    rec = {"dead": False, "date": ""}
    m = PATH_DATE.search(url)
    if m:
        rec["date"] = f"{m.group(1)}-{m.group(2)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12) as r:
            html = r.read(300000).decode("utf8", "ignore")
        d = DATE.search(html)
        if d:
            rec["date"] = d.group(1)
    except urllib.error.HTTPError as e:
        rec["dead"] = e.code in (404, 410)
    except Exception:
        pass  # timeouts and refusals aren't proof a page is gone
    return url, rec


site = json.load(open("data/site.json"))
wl = json.load(open("data/raw/wanderlog.json"))
urls = {s.get("url") for p in wl for s in (p.get("sources") or []) if (s.get("url") or "").startswith("http")}
urls |= {c["url"].replace("http://", "https://", 1) for c in site["cafes"] if "google.com/maps" not in c["url"] and "instagram.com" not in c["url"]}
old = json.load(open(PATH)) if os.path.exists(PATH) else {}
todo = sorted(u for u in urls if not old.get(u, {}).get("date"))
print(len(urls), "links,", len(todo), "to check", flush=True)
with cf.ThreadPoolExecutor(8) as ex:
    for i, (u, rec) in enumerate(ex.map(check, todo)):
        old[u] = {**old.get(u, {}), **rec, "date": rec["date"] or old.get(u, {}).get("date", "")}
        if i % 200 == 0:
            json.dump(old, open(PATH, "w"), indent=0)
json.dump(old, open(PATH, "w"), indent=0)
print("dead", sum(r["dead"] for r in old.values()), "dated", sum(1 for r in old.values() if r["date"]), "of", len(old))
