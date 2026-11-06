#!/usr/bin/env python3
"""Read Wanderlog's public Dubai cafe lists, which robots.txt allows.

Each listing carries Google and Tripadvisor ratings with their counts, the address,
categories and the outside lists that mention the place. Writes data/raw/wanderlog.json.
"""
import json, re, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; LoudestCup/0.1)"}
SLUGS = ["best-coffee-shops-and-best-cafes-in-dubai", "best-coffee-roasters-in-dubai", "best-outdoor-cafes-in-dubai",
         "best-breakfast-and-brunch-in-dubai", "best-brunch-spots-in-dubai", "best-bakeries-in-dubai",
         "best-french-bakeries-in-dubai", "best-spots-for-croissants-in-dubai", "best-pastries-and-patisseries-in-dubai",
         "best-desserts-and-snacks-in-dubai", "best-sweets-spots-in-dubai", "best-cake-shops-and-cake-bakeries-in-dubai",
         "best-pancakes-in-dubai", "best-quiet-places-in-dubai", "best-spots-for-arabic-breakfast-in-dubai",
         "best-spots-for-afternoon-tea-in-dubai"]


def get(path):
    return urllib.request.urlopen(urllib.request.Request("https://wanderlog.com" + path, headers=UA), timeout=30).read().decode("utf8", "ignore")


def state(h):
    i = h.index("__MOBX_STATE__")
    i = h.index("{", i)
    obj, _ = json.JSONDecoder().raw_decode(h[i:])
    return obj


def walk(o, found):
    if isinstance(o, dict):
        if "numRatings" in o and "name" in o:
            found.append(o)
        for v in o.values():
            walk(v, found)
    elif isinstance(o, list):
        for v in o:
            walk(v, found)


EXTRA = ["/list/geoCategory/293298/best-coffee-shops-and-best-cafes-in-emirate-of-dubai", "/list/geoCategory/448244/best-bakeries-in-emirate-of-dubai",
         "/list/geoCategory/236954/best-breakfast-and-brunch-in-emirate-of-dubai", "/list/geoCategory/9460/best-bread-shops-in-dubai",
         "/place/details/2045741/hampstead-bakery-and-cafe", "/place/details/10217412/knot-bakehouse-jumeirah",
         "/place/details/10509735/three-coffee", "/place/details/3831334/jaow-caf"]
first = get("/list/geoCategory/1862944/best-coffee-roasters-in-dubai")
paths = {}
for p in set(re.findall(r"/list/geoCategory/\d+/[a-z0-9-]+", first)):
    paths[p.rsplit("/", 1)[1]] = p
places = {}
paths.update({p: p for p in EXTRA})
for s in SLUGS + EXTRA:
    if s not in paths:
        print("no link", s)
        continue
    h = first if "roasters" in s else get(paths[s])
    found = []
    walk(state(h), found)
    n = 0
    for p in found:
        key = p.get("placeId") or p["name"]
        rec = places.setdefault(key, {**p, "lists": []})
        if s not in rec["lists"]:
            rec["lists"].append(s)
            n += 1
    print(s, n, len(places), flush=True)
    time.sleep(2)
json.dump(list(places.values()), open("data/raw/wanderlog.json", "w"), ensure_ascii=False)
