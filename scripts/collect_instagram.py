#!/usr/bin/env python3
"""Sample public Instagram 'popular' tag pages for Dubai cafe talk.

Reads what a logged-out visitor can see. Writes one JSON object per post to
data/raw/instagram.jsonl. Post dates are decoded from the shortcode.
"""
import json, os, re, subprocess, time

B = os.path.expanduser("~/.claude/skills/gstack/browse/dist/browse")
OUT = "data/raw/instagram.jsonl"
TAGS = """dubaicoffee dubaicafe dubaicafes dubaifoodie dubaifoodies dubaifood dubaieats newindubai
alserkalavenue alquoz jumeirah difc jbr dubaimarina downtowndubai jlt jvc mirdif dubaihills
businessbay dubaicreekharbour palmjumeirah""".split()
TOPICS = """best-cafes-in-dubai best-coffee-in-dubai coffee-shops-in-dubai specialty-coffee-dubai cafes-in-dubai
best-matcha-in-dubai matcha-dubai brunch-in-dubai best-brunch-in-dubai breakfast-in-dubai best-breakfast-in-dubai
cafes-in-jumeirah cafes-in-al-quoz cafes-in-alserkal-avenue cafes-in-downtown-dubai cafes-in-dubai-marina
cafes-in-jbr cafes-in-difc cafes-in-business-bay cafes-in-jlt cafes-in-jvc cafes-in-mirdif cafes-in-deira
cafes-in-bur-dubai cafes-in-palm-jumeirah cafes-in-dubai-hills cafes-in-nad-al-sheba new-cafes-in-dubai
new-cafe-in-dubai aesthetic-cafes-in-dubai hidden-cafes-in-dubai cafes-with-a-view-dubai work-friendly-cafes-dubai
study-cafes-in-dubai iced-latte-dubai coffee-dubai dubai-coffee spanish-latte-dubai pistachio-latte-dubai
bakery-in-dubai best-bakery-in-dubai cold-brew-dubai flat-white-dubai arabic-coffee-dubai best-karak-in-dubai""".split()

EXTRACT = r"""(async()=>{
for(let i=0;i<6;i++){window.scrollTo(0,document.body.scrollHeight);await new Promise(r=>setTimeout(r,1400))}
const seen={},out=[];
for(const a of document.querySelectorAll('a[href*="/p/"],a[href*="/reel/"]')){
  const h=a.getAttribute('href').split('?')[0]; if(seen[h])continue; seen[h]=1;
  out.push({href:h,text:a.innerText})}
return JSON.stringify({url:location.href,title:document.title,posts:out})})()"""

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def shortcode_ts(code):
    n = 0
    for c in code[:11]:
        n = n * 64 + ALPHA.index(c)
    return ((n >> 23) + 1314220021721) // 1000


def views(s):
    m = re.fullmatch(r"([\d,.]+)\s*([KMB]?)", s.strip())
    if not m:
        return None
    return int(float(m.group(1).replace(",", "")) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)])


def run(*a, timeout=60):
    return subprocess.run([B, *a], capture_output=True, text=True, timeout=timeout).stdout


# A page read in the past six days is skipped, so a stopped run can resume and a weekly run reads everything again.
RUN = int(time.time())
done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        r = json.loads(line)
        if RUN - r.get("run", 0) < 6 * 86400:
            done.add(r["tag"])

with open(OUT, "a") as f:
    for tag in TAGS + TOPICS:
        if tag in done:
            continue
        try:
            run("goto", f"https://www.instagram.com/{'popular' if '-' in tag else 'explore/tags'}/{tag}/")
            time.sleep(3)
            d = json.loads(run("js", EXTRACT, timeout=40).strip())
        except Exception as e:
            print(tag, "ERR", repr(e)[:100], flush=True)
            continue
        n = 0
        for p in d["posts"]:
            lines = p["text"].split("\n")
            code = p["href"].rstrip("/").split("/")[-1]
            v = views(lines[1]) if len(lines) > 1 else None
            cap = "\n".join(lines[2:] if v is not None else lines[1:])
            f.write(json.dumps({"tag": tag, "href": p["href"], "code": code, "handle": lines[0],
                                "views": v, "caption": cap, "ts": shortcode_ts(code), "run": RUN},
                               ensure_ascii=False) + "\n")
            n += 1
        f.flush()
        print(tag, n, d["url"][:60], flush=True)
        time.sleep(4)
