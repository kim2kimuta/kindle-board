"""Extract anniversary item names per day from the cached wiki sections.

    python wiki_titles.py wiki_days.json            -> titles.json {"MM-DD": [names...]}
"""
import json
import re
import sys

LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")


def clean(line):
    s = line.lstrip("*").strip()
    s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", s)
    s = TEMPLATE.sub("", s)
    s = LINK.sub(r"\1", s)
    s = re.split(r"[（(]", s)[0]
    return s.replace("'''", "").strip()


def titles(section):
    out = []
    for line in section.splitlines():
        if line.startswith("*") and not line.startswith("*:") and not line.startswith("**"):
            t = clean(line)
            if t:
                out.append(t)
    return out


if __name__ == "__main__":
    days = json.load(open(sys.argv[1], encoding="utf-8"))
    result = {k: titles(v) for k, v in days.items()}
    out = sys.argv[1].replace("wiki_days", "titles")
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(out, sum(len(v) for v in result.values()), "titles")
