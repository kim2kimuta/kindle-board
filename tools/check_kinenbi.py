"""Verify data/kinenbi.json: 366 days, required fields, and each "wiki" name appears
in that day's ja.wikipedia 記念日 list (titles.json from wiki_titles.py)."""
import json
import sys
from datetime import date, timedelta

data = json.load(open(sys.argv[1], encoding="utf-8"))
titles = json.load(open(sys.argv[2], encoding="utf-8"))

d, problems = date(2024, 1, 1), []
while d.year == 2024:
    k = d.strftime("%m-%d")
    e = data.get(k)
    if not e or not all(e.get(f) for f in ("wiki", "title", "text")):
        problems.append(f"{k}: missing entry/field")
    elif not any(e["wiki"] in t for t in titles[k]):
        problems.append(f"{k}: '{e['wiki']}' not in wiki list")
    elif len(e["text"]) > 70:
        problems.append(f"{k}: text too long ({len(e['text'])})")
    d += timedelta(days=1)
extra = set(data) - set(titles)
problems += [f"{k}: unexpected key" for k in sorted(extra)]
with open(sys.argv[3], "w", encoding="utf-8") as f:
    f.write("\n".join(problems) or "OK")
print(len(data), "entries,", len(problems), "problems")
