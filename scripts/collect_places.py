#!/usr/bin/env python3
"""Fetch current Google ratings for every cafe on the chart with the official Places API.

Needs GOOGLE_MAPS_KEY in the environment. Writes data/places.json, which build.py
uses in place of Wanderlog's Google figures. Review text is not fetched. Possible
wrong matches go to data/places_check.json for review instead of the score.
"""
import json, os, re, sys, time, urllib.error, urllib.request

KEY = os.environ.get("GOOGLE_MAPS_KEY", "").strip()
if not KEY:
    sys.exit("GOOGLE_MAPS_KEY is not set")
FIELDS = "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.googleMapsUri,places.businessStatus"
STOP = {"the", "cafe", "café", "coffee", "bakery", "dubai", "and", "co", "roasters", "roastery", "house", "restaurant"}


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP}


def search(name):
    req = urllib.request.Request("https://places.googleapis.com/v1/places:searchText",
        data=json.dumps({"textQuery": name + " cafe Dubai", "pageSize": 1, "languageCode": "en"}).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": KEY, "X-Goog-FieldMask": FIELDS})
    return json.load(urllib.request.urlopen(req, timeout=25)).get("places", [])


good, check = {}, {}
cafes = json.load(open("data/site.json"))["cafes"]
for c in cafes:
    try:
        hits = search(c["name"])
    except urllib.error.HTTPError as e:
        sys.exit(f"Google refused the request ({e.code}). Check the key and that Places API (New) is enabled.")
    if not hits:
        print("NOT FOUND", c["name"])
        continue
    p = hits[0]
    rec = {"id": p["id"], "found": p["displayName"]["text"], "rating": p.get("rating"), "count": p.get("userRatingCount", 0),
           "url": p.get("googleMapsUri"), "address": p.get("formattedAddress", ""), "status": p.get("businessStatus")}
    same = words(c["name"]) & words(rec["found"]) or not words(c["name"])
    (good if same and "Dubai" in rec["address"] else check)[c["name"]] = rec
    print("OK   " if c["name"] in good else "CHECK", c["name"], "->", rec["found"], rec["rating"], rec["count"], flush=True)
    time.sleep(.2)
json.dump(good, open("data/places.json", "w"), ensure_ascii=False, indent=1)
json.dump(check, open("data/places_check.json", "w"), ensure_ascii=False, indent=1)
print(f"Done: {len(good)} matched, {len(check)} to check, {len(cafes) - len(good) - len(check)} not found")
