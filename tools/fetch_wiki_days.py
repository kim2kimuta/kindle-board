"""Fetch the 記念日・年中行事 section of each ja.wikipedia day page (1月1日 .. 12月31日).

Saves {"MM-DD": "<section wikitext>"} to the given JSON path. Used only to verify data/kinenbi.json.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = "https://ja.wikipedia.org/w/api.php"
UA = "kindle-board/0.1 (personal e-ink calendar; https://github.com/kim2kimuta)"


def wikitext(title):
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                "format": "json", "formatversion": 2})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["parse"]["wikitext"]


def section(text, name="記念日・年中行事"):
    start = text.find(f"== {name} ==")
    if start < 0:
        start = text.find(f"=={name}==")
    if start < 0:
        return ""
    end = text.find("\n== ", start + 5)
    return text[start:end if end > 0 else None]


def main(out):
    result = {}
    d = date(2024, 1, 1)  # leap year so 02-29 is included
    while d.year == 2024:
        key = d.strftime("%m-%d")
        result[key] = section(wikitext(f"{d.month}月{d.day}日"))
        d += timedelta(days=1)
        time.sleep(0.3)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(len(result), "days;", sum(1 for v in result.values() if not v), "empty")


if __name__ == "__main__":
    main(sys.argv[1])
