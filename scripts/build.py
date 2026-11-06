#!/usr/bin/env python3
"""Turn raw posts, press lists, articles and review data into the ranked site.

Inputs:  data/raw/instagram.jsonl, data/raw/web.jsonl, data/raw/guides.jsonl,
         data/press.json, data/cafes.json, and data/places.json when it exists
Outputs: data/site.json, site/index.html (for any static host),
         site/loudest-cup.html (body-only page for publishing as an artifact)
"""
import collections, datetime, glob, html, json, math, os, re, time, urllib.parse

NOW = int(time.time())
DAY = 86400
POST_VIEW_CAP = 1_000_000  # one viral reel must not decide the chart
AD = re.compile(r"#(ad|ads|sponsored|gifted|hosted|invited|paidpartnership|collab)\b|\b(invited by|in partnership with|paid partnership|sponsored by|gifted by)\b", re.I)
PLACES = json.load(open("data/places.json")) if os.path.exists("data/places.json") else {}  # optional official Google refresh
WEIGHTS = {"guides": .40, "reviews": .30, "creators": .20, "views": .10}
MIN_REVIEWS = 100  # below this a rating is too thin for the Best reviewed tab
SOURCE_SINCE = "2023-01"  # older write-ups say little about a cafe today
SKIP_GUIDES = {"Trends MENA", "Macau Business"}  # these only report the World's 100 Best list
SITE_NAMES = {"whatson.ae": "What's On", "www.arabianbusiness.com": "Arabian Business",
              "perfectdailygrind.com": "Perfect Daily Grind", "www.ahlanlive.com": "Ahlan",
              "mariandthecity.com": "Mari and the City", "emirateswoman.com": "Emirates Woman", "lovin.co": "Lovin Dubai"}
CAFE_WORDS = re.compile(r"coffee|caf[eé]|roast|espresso|latte|brunch|bakery|barista", re.I)

TODAY_Y = time.strftime("%Y", time.gmtime(NOW))
cafes = json.load(open("data/cafes.json"))
areas = cafes["areas"]
cafes = cafes["cafes"]
press = json.load(open("data/press.json"))
wanderlog = json.load(open("data/raw/wanderlog.json")) if os.path.exists("data/raw/wanderlog.json") else []

# Publishers that sell property, travel, tickets or gifts, or are other cafes: their lists aren't independent.
NOT_INDEPENDENT = re.compile(r"bayut|thrillophilia|sothebys|alharmain|propertyfinder|nextholidays|holidify|beautifulbrands|tourscanner|damac|agluxury|forevertourism|gokite|merikacafe|myholidays|holidaylocationguide|akbartravels|wowdubaitravel|rentechdigital|regencyholidays|wowdeals|insurancemarket|luxuryproperty|anika-property|coffeeroasterfinder|medium\.com|sourdoughbread|alkhail|pickyourtrail|onevasco|uaevisaonline|nyongesasande|igp\.com|twocontinents|addresshotels|satatravels|flyingcup|allsopp|greatvaluevacations|triptipedia|indubaimall|trip101|makemytrip|raynatours|saadatrent|arabmls|thebeach\.ae|wego|almaya|beststartupstory|sana\.|grandmotherroastery|ticketstodo|citywalk|desertcitystays|visitrasalkhaimah|aleppo-grills|circle-cafe|fnp\.ae|dxboffplan|bigbustours|deliveroo|theentertainerme|bakerskitchen")
PUBLISHERS = {"whatson.ae": "What's On", "harpersbazaararabia.com": "Harper's Bazaar Arabia", "cntravellerme.com": "Condé Nast Traveller ME",
              "factmagazines.com": "FACT", "front.factmagazines.com": "FACT", "gulfnews.com": "Gulf News", "timeoutdubai.com": "Time Out Dubai",
              "lovin.co": "Lovin Dubai", "guide.michelin.com": "Michelin Guide", "gqmiddleeast.com": "GQ Middle East", "cosmopolitanme.com": "Cosmopolitan ME",
              "savoirflair.com": "Savoir Flair", "curlytales.com": "Curly Tales", "sheerluxe.me": "Sheerluxe ME", "thehuntr.com": "The Huntr",
              "thenationalnews.com": "The National", "bbcgoodfoodme.com": "BBC Good Food ME", "telegraph.co.uk": "The Telegraph",
              "emirateswoman.com": "Emirates Woman", "sassymamadubai.com": "Sassy Mama Dubai", "expatwoman.com": "ExpatWoman",
              "dannibindubai.com": "Danni B in Dubai", "fltrmagazine.com": "FLTR Magazine", "gaultmillauae.com": "Gault&Millau UAE",
              "squaremeal.ae": "SquareMeal", "ahlanlive.com": "Ahlan", "graziamagazine.com": "Grazia Middle East", "elitetraveler.com": "Elite Traveler",
              "worldofmouth.app": "World of Mouth", "roadbook.com": "Roadbook", "platinumlist.net": "Platinumlist", "roasters.app": "Roasters App",
              "vdqa104.testvisitdubai.com": "Visit Dubai", "timeoutsharjah.com": "Time Out Dubai", "front.factmagazines.com": "FACT",
              "blog.dubailocal.ae": "Dubai Local", "nearfarmag.com": "NearFar Magazine", "dubaisbest.com": "Dubai's Best", "adameshandbook.com": "Adam's Handbook",
              "traveltastediscover.com": "Travel Taste Discover", "thebohochica.com": "The Boho Chica", "dubai-on.com": "Dubai On", "latestnewsdubai.com": "Latest News Dubai",
              "foodiva.net": "Foodiva", "wheresachi.com": "Where's Achi", "thegaggler.com": "The Gaggler", "travelsaga.com": "Travel Saga", "arabiers.com": "Arabiers",
              "dubainight.com": "Dubai Night", "albertreview.com.au": "Albert Review", "theneedforcoffee.com": "The Need for Coffee", "mala.ae": "Mala", "ebestdubai.ae": "eBest Dubai",
              "hungrito.com": "Hungrito", "dubaimusts.me": "Dubai Musts", "myreviewly.com": "MyReviewly", "thingstododubai.com": "Things To Do Dubai", "uaestories.com": "UAE Stories",
              "artandthensome.com": "Art and Then Some", "liloneoftheashes.com": "Lil One of the Ashes", "theluxediary.com": "The Luxe Diary", "rumemagazine.com": "Rume Magazine",
              "few.ae": "Few", "experiencesluxe.com": "Experiences Luxe", "world-arabia.com": "World Arabia", "mariandthecity.com": "Mari and the City", "mycustardpie.com": "My Custard Pie","focus.hidubai.com": "Hi Dubai", "theculturetrip.com": "Culture Trip", "planetware.com": "PlanetWare"}
GENERIC = {"society", "french bakery", "home bakery", "black coffee", "the eatery", "late lounge", "bakery", "the coffee lab", "circle cafe", "brews cafe", "cafe rider custom", "emirati coffee roastery"}  # too common to match in captions
COFFEE_CATS = {"Cafe", "Coffee shop", "Coffee roastery", "Coffee store"}
CHAINS = re.compile(r"starbucks|costa|tim hortons|dunkin|caribou|peet|seattle|krispy|cinnabon|^paul\b|ladur[eé]e|angelina|mcdonald|nespresso|lavazza|patchi|bateel|hotel|resort|jumeirah al qasr|versace|armani|burj al arab|"
                    r"coffee club|pain quotidien|magnolia|el&n|eggspectation|ikea|marks & spencer|huqqa|royal tearoom|lobby lounge|shai salon|raffles|peacock alley|the tea room|hafiz mustafa|moishi|freez|morelli|said dal|katrina|^cake$|loqa|humyum|brownie point|choix|the patisserie|cipriani|room 1618|the farm|terra eatery|darjeeling|al fanar|al khayma|al mallah|the guild|ror coffee|gold box|intellect|specialty batch|mattina|coffee museum|artisan bakers", re.I)
DISPLAY_TRIM = re.compile(r"\s+(Dubai Health Care City|Dubai Hills|Al Thanyah?|Tilal AL Ghaf|Concept Store.*|LLC|UAE.*|Dubai|Restaurant|& Restaurant|Cafe & Kitchen)$", re.I)
AREA_RULES = [("d3", r"design district|d3"),
              ("hills", r"dubai hills|hadaeq|mohammed bin rashid|al barsha|mall of the emirates|emirates hills|al thanyah|jumeirah islands|jumeirah village|jvc|tilal al ghaf|sustainable city|motor city|arabian ranches|town square|investment park|gold and diamond"),
              ("old", r"health ?care city|al razzi|muraqqabat"),("marina", r"marina|jbr|jumeirah beach residence|jlt|jumeirah lake|bluewaters|the walk"),
              ("difc", r"difc|financial cent|trade cent"), ("downtown", r"downtown|business bay|burj khalifa|dubai mall|souk al bahar|boulevard|opera"),
              ("alquoz", r"al quoz|al qouz|alserkal|quoz"), ("alwasl", r"al wasl|al safa|al manara|wasl"),
              ("jumeirah", r"jumeirah|jumeira|umm suqeim|umm suqueim|kite beach|la mer|palm|city walk|al satwa|satwa|sufouh"),
              ("old", r"deira|bur dubai|fahidi|al seef|karama|mankhool|al souq|bastakiya|creek|oud metha|al jaffiliya|al raffa"),
              ("east", r"mirdif|nad al sheba|festival|rashidiya|al warqa|meydan")]


def pretty(host):
    return PUBLISHERS.get(host) or re.sub(r"\.[a-z.]+$", "", host).replace("-", " ").title()


DISPLAY_NAMES = {"Orto cafe": "Orto", "Risen Café and Artisanal Bakery": "Risen Café", "Bloomsbury's Boutique Cafe & Artisan Bakery": "Bloomsbury's",
                 "Arrows and Sparrows Cafe": "Arrows and Sparrows", "The Hamptons Cafe & Restaurant": "The Hamptons", "Xva Café & Restaurant": "XVA Café", "MONDOUX": "Mondoux",
                 "RIINA": "Riina", "THREE Coffee": "Three Coffee", "EARTH ROASTERY": "Earth Roastery", "Comptoir 102 Concept Store & Healthy Eatery": "Comptoir 102",
                 "Friends Avenue Cafe": "Friends Avenue", "Grandmother Roastery": "Grandmother Roastery", "Pekoe tea & bread bar": "Pekoe"}
LINKS = json.load(open("data/link_status.json")) if os.path.exists("data/link_status.json") else {}


def recency(date):
    """Newer articles count for more. Undated ones sit in the middle."""
    if not re.match(r"\d{4}", date or ""):
        return .7
    age = int(TODAY_Y) - int(date[:4])
    return 1 if age <= 2 else .7 if age <= 4 else .4


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def area_of(addr):
    for aid, rx in AREA_RULES:
        if re.search(rx, addr, re.I):
            return aid
    return "other"

posts = {}
for line in open("data/raw/instagram.jsonl"):
    r = json.loads(line)
    p = posts.setdefault(r["code"], {**r, "tags_seen": set()})
    p["tags_seen"].add(r["tag"])
    if r["views"] is not None:
        p["views"] = r["views"]  # the newest reading wins
posts = list(posts.values())


def norm_handle(s):
    return s.lower().strip("@ ")


def is_own(c, p):
    """True when the post comes from the cafe. Long handles arrive cut short with '...'."""
    h = norm_handle(p["handle"])
    stem = h[:-3] if h.endswith("...") else None
    return h in c["_own"] or bool(stem and any(o.startswith(stem) for o in c["_own"]))


def matcher(c):
    bits = [re.escape(a) for a in c["aliases"]]
    hs = [re.escape(h) for h in c.get("handles", [])]
    body = r"(?<![\w.])(?:" + "|".join(bits + ["@" + h for h in hs]) + r")(?![\w])"
    return re.compile(body, re.I)


for c in cafes:
    c["_re"] = matcher(c)
    c["_own"] = {norm_handle(h) for h in c.get("handles", [])}
    c["_hits"] = []
    c["_sources"] = []
    for v in press.values():
        if c["name"] in v["cafes"] or set(c.get("press", [])) & set(v["cafes"]):
            c["_sources"].append({"name": v["name"].split(",")[0], "kind": "award" if "100 Best" in v["name"] else "guide",
                                  "title": v["name"], "url": v["url"], "date": v.get("date", "")})



def names_cafe(c, text):
    """Exact, case-sensitive name in a Dubai article, with coffee talk close by."""
    if "Dubai" not in text:
        return False
    for a in c["aliases"]:
        for m in re.finditer(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", text):
            if CAFE_WORDS.search(text[max(0, m.start() - 220):m.end() + 220]):
                return True
    return False


articles = []
for path in ("data/raw/web.jsonl", "data/raw/lovin.jsonl"):
    for line in (open(path) if os.path.exists(path) else []):
        r = json.loads(line)
        if not r["date"]:
            continue  # undated rows are section pages, not articles
        host = r["site"].split("//")[1]
        articles.append({"name": SITE_NAMES[host], "kind": "news", "title": r["title"], "url": r["url"], "date": r["date"], "text": r["title"] + " " + r["text"]})
if os.path.exists("data/raw/guides.jsonl"):
    for line in open("data/raw/guides.jsonl"):
        r = json.loads(line)
        if r["name"] not in SKIP_GUIDES:
            articles.append({"name": r["name"].replace(" readers", ""), "kind": r["kind"], "title": r["name"], "url": r["url"], "date": r["date"] or "", "text": r["text"]})
articles = [a for a in articles if not a["date"] or a["date"] >= SOURCE_SINCE]
for a in articles:
    for c in cafes:
        if names_cafe(c, a["text"]):
            c["_sources"].append({k: a[k] for k in ("name", "kind", "title", "url", "date")})

# Merge Wanderlog venues: branches of a known cafe join it, other coffee venues join the chart.
new = {}
for p in wanderlog:
    addr = p.get("address") or ""
    if p.get("businessStatus") != "OPERATIONAL" or "Dubai" not in addr:
        continue
    hit = next((c for c in cafes if c["_re"].search(p["name"]) or c["name"].lower() == p["name"].lower()), None)
    if not hit:
        base = re.split(r"\s[-–—|@]\s*|,|\(|\s+at\s+|\s+by\s+", p["name"])[0].strip()
        if (not set((p.get("categories") or [])[:3]) & COFFEE_CATS) or CHAINS.search(p["name"]) or len(norm(base)) < 4:
            continue
        base = DISPLAY_TRIM.sub("", DISPLAY_TRIM.sub("", base)).strip()
        hit = new.setdefault(norm(base), {"name": base, "area": area_of(addr), "aliases": [base] if len(norm(base)) > 5 and base.lower() not in GENERIC else [],
                                          "handles": [], "press": [], "url": p.get("website"), "_re": re.compile(r"(?!x)x"), "_own": set(), "_hits": [], "_sources": [], "_wl": []})
    hit.setdefault("_wl", []).append(p)
for c in new.values():
    if c["aliases"]:
        c["_re"] = matcher(c)
cafes += [c for c in new.values() if sum(p.get("numRatings") or 0 for p in c["_wl"]) >= 50 or sum(len(p.get("sources") or []) for p in c["_wl"]) >= 2]
for c in cafes:
    biggest = max(c.get("_wl", []), key=lambda p: p.get("numRatings") or 0, default=None)
    if biggest and (c["area"] == "other" or c["name"] in new or norm(c["name"]) in new):
        c["area"] = area_of(biggest.get("address") or "")
    if c["name"] in DISPLAY_NAMES:
        c["name"] = DISPLAY_NAMES[c["name"]]
    c["area"] = {"Angel Cakes": "hills", "Bloomsbury's": "old"}.get(c["name"], c["area"])
    c["maps"] = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(c["name"] + " Dubai")
    if biggest and biggest.get("placeId"):
        c["maps"] += "&query_place_id=" + biggest["placeId"]

for c in cafes:
    wl = c.get("_wl", [])
    g = [(p["rating"], p["numRatings"]) for p in wl if p.get("rating") and p.get("numRatings")]
    t = [(p["tripadvisorRating"], p["tripadvisorNumRatings"]) for p in wl if p.get("tripadvisorRating") and p.get("tripadvisorNumRatings")]
    avg = lambda xs: round(sum(r * n for r, n in xs) / sum(n for _, n in xs), 1)
    if g or t:
        c["reviews"] = {"count": sum(n for _, n in g + t), "rating": avg(g + t), "google": avg(g) if g else None, "googleCount": sum(n for _, n in g),
                        "tripadvisor": avg(t) if t else None, "tripadvisorCount": sum(n for _, n in t)}
    for p in wl:
        for s in p.get("sources") or []:
            u = s.get("url") or ""
            if "//" not in u:
                continue
            host = re.sub(r"^www\.", "", u.split("/")[2])
            if NOT_INDEPENDENT.search(host):
                continue
            state = LINKS.get(u, {})
            if host.endswith("testvisitdubai.com"):
                u = u.replace(u.split("/")[2], "www.visitdubai.com")
            c["_sources"].append({"name": pretty(host), "kind": "news", "title": pretty(host), "url": u, "date": state.get("date", ""), "dead": state.get("dead", False)})

for c in cafes:
    c["guides"] = sorted({s["name"] for s in c["_sources"]})  # one vote per publisher, however many articles
    uniq = {}
    for s in sorted(c["_sources"], key=lambda s: (not s.get("dead"), s["date"] or "")):  # a live, newer article wins
        uniq[s["name"]] = s
    c["_gw"] = sum(recency(s["date"]) for s in uniq.values())
    c["sources"] = [{k: v for k, v in s.items() if k != "dead"} for s in sorted(uniq.values(), key=lambda s: s["date"] or "", reverse=True) if not s.get("dead")][:8]
    c["kinds"] = dict(collections.Counter(s["kind"] for s in uniq.values()))
    p = PLACES.get(c["name"])
    if p and p.get("count"):
        r = c.get("reviews") or {}
        t = r.get("tripadvisorCount") or 0
        total = p["count"] + t
        c["reviews"] = {"count": total, "rating": round((p["rating"] * p["count"] + (r.get("tripadvisor") or 0) * t) / total, 1), "google": p["rating"],
                        "googleCount": p["count"], "tripadvisor": r.get("tripadvisor"), "tripadvisorCount": t}

matched = 0
for p in posts:
    cap = p["caption"]
    hit = [c for c in cafes if c["_re"].search(cap) or is_own(c, p)]
    p["paid"] = bool(AD.search(cap))
    if hit:
        matched += 1
    for c in hit:
        c["_hits"].append(p)


def metrics(c, days, end=0):
    lo, hi = NOW - (days + end) * DAY, NOW - end * DAY
    earned = [p for p in c["_hits"] if lo <= p["ts"] < hi and not is_own(c, p)]
    creators = {norm_handle(p["handle"]) for p in earned if not p["paid"]}
    paid_only = {norm_handle(p["handle"]) for p in earned if p["paid"]} - creators
    views = sum(min(p["views"] or 0, POST_VIEW_CAP) * (.5 if p["paid"] else 1) for p in earned)
    return {"creators": len(creators | paid_only), "weighted": len(creators) + .5 * len(paid_only), "views": int(views), "posts": len(earned)}


# Quiet listings: no reviews, one source at most and no recent posts. Too little to rank.
cafes[:] = [c for c in cafes if c.get("reviews") or len(c["guides"]) > 1 or
            any(p["ts"] >= NOW - 365 * DAY and not is_own(c, p) for p in c["_hits"])]


def review_score(c):
    """0-1. Pulls small review counts towards the average, so 5.0 from six people isn't a win."""
    r = c.get("reviews")
    if not r:
        return 0
    stars = (100 * 4.3 + r["count"] * r["rating"]) / (100 + r["count"])
    return .5 * max(0, min(1, (stars - 3.5) / 1.5)) + .5 * min(1, math.log1p(r["count"]) / math.log1p(5000))


def score(ms, key, trend=False):
    """0-100 on log scales. A cafe with no review data is scored on its other signals."""
    mc = max(math.log1p(m["weighted"]) for m in ms) or 1
    mv = max(math.log1p(m["views"]) for m in ms) or 1
    mg = max(math.log1p(c["_gw"]) for c in cafes) or 1
    for c, m in zip(cafes, ms):
        cr, vi = math.log1p(m["weighted"]) / mc, math.log1p(m["views"]) / mv
        if trend:
            s = .7 * cr + .3 * vi if m["posts"] else 0
        else:
            s = WEIGHTS["creators"] * cr + WEIGHTS["views"] * vi + WEIGHTS["guides"] * math.log1p(c["_gw"]) / mg
            s = s + WEIGHTS["reviews"] * review_score(c) if c.get("reviews") else s / (1 - WEIGHTS["reviews"])
        c[key] = {**m, "score": round(100 * s, 1)}


score([metrics(c, 365) for c in cafes], "d365")
score([metrics(c, 90) for c in cafes], "d90", trend=True)

for c in cafes:
    m = c["d365"]
    c["guidesTab"] = {**m, "score": round(c["_gw"] * 10 + min(m["creators"], 9) / 10, 1)} if c["guides"] else None
    r = c.get("reviews")
    c["reviewsTab"] = {**m, "score": round(100 * review_score(c), 1)} if r and r["count"] >= MIN_REVIEWS else None

# Movement: rank now against the last saved rank, like a stock's change on the day.
METHOD = "v3-google" if PLACES else "v3"  # a change of method resets the comparison, so it never shows as a real move
TODAY = time.strftime("%Y-%m-%d", time.gmtime(NOW))
TABS = ["d365", "d90", "guidesTab", "reviewsTab"]


def ranks(key):
    live = [c for c in cafes if c.get(key) and c[key]["score"] > 0]
    live.sort(key=lambda c: (-c[key]["score"], c["name"]))
    return {c["name"]: i + 1 for i, c in enumerate(live)}


now_ranks = {t: ranks(t) for t in TABS}
snapshots = []
for path in sorted(glob.glob("data/history/*.json")):
    snap = json.load(open(path))
    if snap["date"] < TODAY and snap["method"] == METHOD:
        snapshots.append(snap)
if snapshots:
    prev_ranks = snapshots[-1]["ranks"]
    move_note = "Compared with " + datetime.date.fromisoformat(snapshots[-1]["date"]).strftime("%-d %B %Y")
else:
    # No earlier snapshot: rebuild the two post-based charts as they stood 30 days ago, using post dates.
    score([metrics(c, 365, end=30) for c in cafes], "_prev365")
    score([metrics(c, 90, end=30) for c in cafes], "_prev90", trend=True)
    prev_ranks = {"d365": ranks("_prev365"), "d90": ranks("_prev90")}
    move_note = "Estimated: compared with 30 days ago, from post dates"
for c in cafes:
    c["move"] = {}
    for t in TABS:
        if c["name"] not in now_ranks[t]:
            continue
        prev = prev_ranks.get(t)
        c["move"][t] = None if prev is None else ("new" if c["name"] not in prev else prev[c["name"]] - now_ranks[t][c["name"]])
os.makedirs("data/history", exist_ok=True)
json.dump({"date": TODAY, "method": METHOD, "ranks": now_ranks}, open(f"data/history/{TODAY}.json", "w"), ensure_ascii=False)

for c in cafes:
    c["url"] = (c.get("url") or "").replace("http://", "https://", 1) if not LINKS.get((c.get("url") or "").replace("http://", "https://", 1), {}).get("dead") else c["url"]
    c["url"] = c["url"] or (f"https://www.instagram.com/{c['handles'][0]}/" if c.get("handles") else
                                "https://www.google.com/maps/search/" + re.sub(r"\s+", "+", c["name"] + " Dubai"))

window = [p for p in posts if p["ts"] >= NOW - 365 * DAY]
tagc = collections.Counter(t.lower() for p in window for t in set(re.findall(r"#(\w+)", p["caption"])))
stock = {"dubairealestate", "realestate", "visitdubai", "dubailife", "dubaivibes", "abudhabi", "food", "foodie", "dubai", "uae", "fyp", "viral", "explore", "explorepage", "reels", "instagram", "love", "instagood", "trending"}
tags = [[t, n] for t, n in tagc.most_common(60) if t not in stock][:24]

used = {}
for c in cafes:
    for s in c["_sources"]:
        used.setdefault(s["name"], s["url"] if s["kind"] != "news" else "https://" + s["url"].split("/")[2])
guides_links = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in sorted(used.items()))
n_articles = len({s["url"] for c in cafes for s in c["_sources"]})
ranked = [c for c in cafes if c["d365"]["score"] > 0]
top_creators = max(c["d365"]["creators"] for c in cafes)
site = {
    "generated": time.strftime("%-d %B %Y", time.gmtime(NOW)),
    "totals": {"posts": len(posts), "window": len(window), "matched": matched, "cafes": len(ranked),
               "creators": len({norm_handle(p["handle"]) for p in window}), "tags": len({p["tag"] for p in posts}),
               "guides": len(used), "articles": n_articles},
    "areas": areas,
    "cafes": [{**{k: v for k, v in c.items() if not k.startswith("_") and k not in ("aliases", "press", *TABS)},
               **{t: {"score": c[t]["score"]} if c.get(t) else None for t in TABS}} for c in cafes],
    "moveNote": move_note,
    "tags": tags,
    "tabLabels": {"d90": "Trending now", "d365": "Overall", "guidesTab": "Most recommended", "reviewsTab": "Best reviewed"},
    "tabNotes": {"d365": "Ranked by recommendations, reviews and social posts",
                 "d90": "Ranked by Instagram activity in the past 90 days",
                 "guidesTab": "Ranked by independent recommendations, with newer articles counting for more",
                 "reviewsTab": f"Google and Tripadvisor combined, minimum {MIN_REVIEWS} reviews"},
    "tagNote": f"The most-used tags across {len(window):,} Dubai posts from the past 12 months, with how many posts used each.",
    "method": [
        {"weight": "40%", "name": "Recommendations", "text": f"How many of {len(used)} independent publishers named the cafe. Each counts once, and newer articles count for more. Sites selling property, travel or tickets don't count."},
        {"weight": "30%", "name": "Reviews", "text": "Google and Tripadvisor ratings and review counts, with small counts pulled towards the average."},
        {"weight": "30%", "name": "Talk", "text": "Instagram activity from people other than the cafe. One viral reel can't decide the chart."},
        {"weight": "½", "name": "Ads", "text": "Posts marked as an ad, gift or invite count for half."},
        {"weight": "▲▼", "name": "Movement", "text": "How many places a cafe has risen or fallen since the last update."},
    ],
    "limits": (f"<strong>How far to trust this.</strong> It combines {sum(1 for c in cafes if c.get('reviews'))} cafes' Google and Tripadvisor ratings, "
               f"{n_articles} articles from {len(used)} publishers and {len(window):,} public Instagram posts. "
               + ("Google ratings come directly from Google; Tripadvisor ratings are Wanderlog's copies and may be months old. " if PLACES else "Ratings come from Wanderlog's copies and may be months old. ")
               + f"{sum(1 for c in ranked if not c.get('reviews'))} newer cafes have no review data yet and are scored on their other signals. "
               "Older cafes have had longer to collect reviews and mentions, so the Trending tab is the better guide to what's new. "
               "TikTok, Reddit and private community groups aren't included, and shares and saves aren't public."),
    "sourcesHtml": "Guides used: " + guides_links,
    "footer": f"Updated {time.strftime('%-d %B %Y', time.gmtime(NOW))} from {len(ranked)} cafes, {n_articles} articles and {len(window):,} posts. " + ("Ratings from Google, and Tripadvisor via Wanderlog." if PLACES else "Ratings via Wanderlog, from Google and Tripadvisor."),
}
json.dump(site, open("data/site.json", "w"), ensure_ascii=False, indent=1)

SITE_URL = "https://loudest-cup.onrender.com/"
top20 = sorted(ranked, key=lambda c: -c["d365"]["score"])[:20]
AREA_NAMES = {a["id"]: a["name"] for a in areas}
TITLE = "Best Coffee Shops and Cafes in Dubai | Loudest Cup"
DESCRIPTION = (f"The top coffee shops and cafes in Dubai, ranked weekly from {len(used)} independent publishers, Google and Tripadvisor reviews and social talk. "
               f"This week's N°1: {top20[0]['name']}.")
ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Best coffee shops and cafes in Dubai", "url": SITE_URL,
      "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": c["name"], "url": c["url"]} for i, c in enumerate(top20)]}
HEAD = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{html.escape(DESCRIPTION)}">
<link rel="canonical" href="{SITE_URL}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}">
<meta property="og:site_name" content="Loudest Cup"><meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{html.escape(DESCRIPTION)}">
<meta property="og:image" content="{SITE_URL}og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{html.escape(DESCRIPTION)}"><meta name="twitter:image" content="{SITE_URL}og.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<" + chr(92) + "/")}</script>
</head><body style="margin:0">"""
prerender = "".join(f'<li class="row"><span class="r">{i + 1}</span><span class="nm"><a href="{html.escape(c["url"])}">{html.escape(c["name"])}</a></span><span class="ar"><a href="{html.escape(c["maps"])}">{html.escape(AREA_NAMES[c["area"]])}</a></span></li>' for i, c in enumerate(top20))
open("site/robots.txt", "w").write(f"User-agent: *\nAllow: /\nDisallow: /template.html\nDisallow: /loudest-cup.html\n\nSitemap: {SITE_URL}sitemap.xml\n")
open("site/sitemap.xml", "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq></url></urlset>\n')
open("site/favicon.svg", "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#08302c"/><circle cx="16" cy="16" r="10" fill="#f7b90f"/><path d="M11 18c2-5 8-5 10-1" fill="none" stroke="#eef3e6" stroke-width="2" stroke-linecap="round"/></svg>')

tpl = open("site/template.html").read()
payload = json.dumps(site, ensure_ascii=False).replace("</", "<\\/")
page = tpl.replace("/*DATA*/", payload)
open("site/loudest-cup.html", "w").write(page)
open("site/index.html", "w").write(HEAD + re.sub(r"<title>.*?</title>\n?", "", page, count=1).replace('<ol class="chart" id="chart"></ol>', '<ol class="chart" id="chart">' + prerender + "</ol>") + "</body></html>")

print(site["totals"], WEIGHTS)
for c in sorted(ranked, key=lambda c: -c["d365"]["score"])[:30]:
    m = c["d365"]
    r = c.get("reviews") or {}
    print(f'{c["d365"]["score"]:5} {c["name"]:<28} {c["area"]:<9} cr={m["creators"]} v={m["views"]} g={len(c["guides"])} r={r.get("rating")}/{r.get("count")} d90={c["d90"]["score"]}')
