#!/bin/bash
# Weekly update. Run from the project folder. One failed source doesn't stop the others.
set -u
cd "$(dirname "$0")/.."
failed=""
step() { name="$1"; shift; echo "== $name"; "$@" || failed="$failed $name"; }
step "Wanderlog" python3 scripts/collect_wanderlog.py
step "Guides" python3 scripts/collect_guides.py
step "Links" python3 scripts/check_links.py
step "Instagram" python3 scripts/collect_instagram.py
if [ -n "${GOOGLE_MAPS_KEY:-}" ]; then step "Google" python3 scripts/collect_places.py; fi
python3 scripts/build.py || { echo "BUILD FAILED"; exit 1; }
echo "REFRESH DONE failed:${failed:- none}"
