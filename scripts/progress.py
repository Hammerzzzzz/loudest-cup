#!/usr/bin/env python3
"""Show a live progress bar for scripts/refresh.sh. Run it from the project folder."""
import json, os, subprocess, sys, time

LOG = "data/raw/refresh.log"
FEED = "data/raw/instagram.jsonl"
src = open("scripts/collect_instagram.py").read()
TOTAL = len(src.split('TAGS = """')[1].split('"""')[0].split()) + len(src.split('TOPICS = """')[1].split('"""')[0].split())


def pages_done():
    """Pages read in the past six days, the same rule the collector uses to skip them."""
    now, tags = time.time(), set()
    if os.path.exists(FEED):
        for line in open(FEED):
            r = json.loads(line)
            if now - r.get("run", 0) < 6 * 86400:
                tags.add(r["tag"])
    return len(tags)


def running():
    return subprocess.run(["pgrep", "-f", "scripts/refresh.sh"], capture_output=True).returncode == 0


while True:
    text = open(LOG).read()
    last = text.rsplit("\n", 2)[-2][:44] if text.count("\n") > 1 else ""
    done = "REFRESH DONE" in text or "BUILD FAILED" in text
    if "== Instagram" in text:
        pages = pages_done()
        pct = min(pages / TOTAL, 1)
        label = f"Instagram {min(pages, TOTAL)}/{TOTAL}"
    else:
        pct, label = 0, "Collecting reviews and guides"
    if done:
        pct, label = 1, "Finished"
    bar = "#" * int(pct * 30) + "-" * (30 - int(pct * 30))
    sys.stdout.write(f"\r[{bar}] {pct:4.0%}  {label:<24}")
    sys.stdout.flush()
    if done or not running():
        print("\n" + (last if done else "Refresh is no longer running."))
        break
    time.sleep(3)
