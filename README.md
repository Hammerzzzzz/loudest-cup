# Loudest Cup Dubai

Dubai's coffee shops and cafes, ranked by independent recommendations, reviews and social posts.

**[Live chart → loudest-cup.onrender.com](https://loudest-cup.onrender.com)** · [![Site health](https://github.com/Hammerzzzzz/loudest-cup/actions/workflows/site-health.yml/badge.svg)](https://github.com/Hammerzzzzz/loudest-cup/actions/workflows/site-health.yml)

## Why I built it

"Best cafés in Dubai" lists are everywhere, and most are paid placements or one writer's taste. I wanted to see what happens when you treat the question the way a social listening team would: gather what lots of independent sources say, weight it, and rank the result.

- **Audience:** Dubai residents and visitors choosing where to get coffee, and anyone curious which cafés people are actually talking about.
- **Approach:** combine review ratings, editorial guides and Instagram chatter into one score, with sponsored, gifted and #ad posts filtered out. The weights sit at the top of `scripts/build.py` so they're easy to inspect and change.
- **What I'd measure:** return visits each week, clicks through to Google Maps, and whether the weekly movers match what people notice in real life.
- **What I learned:** most of the work is in the data, not the page. Matching one café's many name variants across sources, and keeping a source that fails one week from wiping out its data, mattered more than the design.

## How it's run

- A local script (`scripts/refresh.sh`) collects the sources and rebuilds the static page each week. Raw third-party content stays off GitHub.
- A GitHub Action (`.github/workflows/site-health.yml`) checks the data files, confirms the weekly update ran, and checks the live site is up.
- Render publishes `site/` automatically on every push to `main`.

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
