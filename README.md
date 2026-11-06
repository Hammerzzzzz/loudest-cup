# Loudest Cup Dubai

Dubai's coffee shops and cafes, ranked by independent recommendations, reviews and social posts.

Weekly update: `bash scripts/refresh.sh` collects everything and rebuilds. A source that fails keeps its last data.

```bash
python3 scripts/collect_wanderlog.py   # Google and Tripadvisor ratings, plus linked articles
python3 scripts/collect_guides.py      # guides and reader lists
python3 scripts/collect_instagram.py   # add new posts to data/raw/instagram.jsonl
python3 scripts/build.py               # rank cafes and rebuild site/
```

Optional, needs `GOOGLE_MAPS_KEY`: `python3 scripts/collect_places.py` writes fresher Google ratings to `data/places.json`, which override Wanderlog's copies.

- `data/cafes.json`: core cafes, areas, name variants and Instagram handles.
- `data/press.json`: guides and awards read by hand, including partial Time Out and Lovin Dubai picks.
- `site/index.html`: static page for any host.

Weights, excluded publishers and excluded venues are at the top of `scripts/build.py`.
