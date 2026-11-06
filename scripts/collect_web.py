#!/usr/bin/env python3
"""Collect articles that mention Dubai cafes from publishers' public WordPress APIs.

Searches each site for each cafe plus a few general terms, then saves the full
article text to data/raw/web.jsonl. Build.py decides which articles really name
a cafe. Sites that block this kind of request are not worked around.
"""
import html, json, os, re, time, urllib.parse, urllib.request

SITES = ["https://whatson.ae", "https://www.arabianbusiness.com", "https://perfectdailygrind.com",
         "https://www.ahlanlive.com", "https://mariandthecity.com", "https://emirateswoman.com"]
GENERAL = ["specialty coffee Dubai", "best cafes Dubai", "coffee shop Dubai", "new cafe Dubai", "coffee roastery Dubai"]
OUT = "data/raw/web.jsonl"
UA = {"User-Agent": "Mozilla/5.0 (compatible; LoudestCup/0.1)"}
cafes = json.load(open("data/cafes.json"))["cafes"]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


seen = set()
if os.path.exists(OUT):
    for line in open(OUT):
        r = json.loads(line)
        seen.add((r["site"], r["id"]))

terms = [("cafe", a) for c in cafes for a in c["aliases"][:2]] + [("general", g) for g in GENERAL]
with open(OUT, "a") as f:
    for site in SITES:
        fails = 0
        for kind, term in terms:
            if fails >= 5:
                print(site, "stopped after repeated errors", flush=True)
                break
            q = urllib.parse.urlencode({"search": term, "per_page": 20, "type": "post"})
            try:
                hits = get(f"{site}/wp-json/wp/v2/search?{q}")
                fails = 0
            except Exception as e:
                fails += 1
                print(site, term, "ERR", repr(e)[:90], flush=True)
                time.sleep(3)
                continue
            for h in hits:
                key = (site, h["id"])
                if key in seen:
                    continue
                seen.add(key)
                try:
                    p = get(f"{site}/wp-json/wp/v2/posts/{h['id']}?_fields=date,link,title,content")
                except Exception as e:
                    print(site, h["id"], "ERR", repr(e)[:90], flush=True)
                    continue
                text = re.sub(r"<[^>]+>", " ", p["content"]["rendered"])
                f.write(json.dumps({"site": site, "id": h["id"], "url": p["link"], "date": p["date"][:10],
                                    "title": html.unescape(p["title"]["rendered"]),
                                    "text": re.sub(r"\s+", " ", html.unescape(text))}, ensure_ascii=False) + "\n")
                f.flush()
                time.sleep(.5)
            time.sleep(.6)
        print(site, "done", len(seen), flush=True)
print("finished", len(seen), flush=True)
