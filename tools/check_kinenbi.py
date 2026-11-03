"""Verify data/kinenbi.json: 366 days, required fields, and each "wiki" name appears
in that day's ja.wikipedia 記念日 list (titles.json from wiki_titles.py)."""
import json
import re
import sys
from datetime import date, timedelta

data = json.load(open(sys.argv[1], encoding="utf-8"))
titles = json.load(open(sys.argv[2], encoding="utf-8"))

# 小学1・2年で習う漢字（学年別漢字配当表）。これ以外の漢字は「」の中（作品名など）だけ許す
GRADE12 = set(
    "一右雨円王音下火花貝学気九休玉金空月犬見五口校左三山子四糸字耳七車手十出女小上森人水正生青夕石赤千川先"
    "早草足村大男竹中虫町天田土二日入年白八百文木本名目立力林六"
    "引羽雲園遠何科夏家歌画回会海絵外角楽活間丸岩顔汽記帰弓牛魚京強教近兄形計元言原戸古午後語工公広交光考行"
    "高黄合谷国黒今才細作算止市矢姉思紙寺自時室社弱首秋週春書少場色食心新親図数西声星晴切雪船線前組走多太体"
    "台地池知茶昼長鳥朝直通弟店点電刀冬当東答頭同道読内南肉馬売買麦半番父風分聞米歩母方北毎妹万明鳴毛門夜野"
    "友用曜来里理話"
)


def hard_kanji(text):
    outside = re.sub(r"「[^」]*」", "", text)
    return sorted({c for c in outside if "一" <= c <= "鿿" and c not in GRADE12})


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
    elif hard_kanji(e["title"] + e["text"]):
        problems.append(f"{k}: kanji above grade 2: {''.join(hard_kanji(e['title'] + e['text']))}")
    d += timedelta(days=1)
extra = set(data) - set(titles)
problems += [f"{k}: unexpected key" for k in sorted(extra)]
with open(sys.argv[3], "w", encoding="utf-8") as f:
    f.write("\n".join(problems) or "OK")
print(len(data), "entries,", len(problems), "problems")
