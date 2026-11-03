"""Kindle Paperwhite 3 (1072x1448) 向けの「今日の 天気 ＋ 今日は 何の日」画像を生成する。

上は天気、下は原稿用紙のマス目に縦書きで「今日は 何の日」を書く。
フォントは教科書の字に近い Klee One（fonts/ に置く。README 参照）。

使い方:
    python make_board.py                         # 今日（日本時間）、東京
    python make_board.py --date 2026-12-25       # 記念日の表示確認用（天気は取得できる範囲の予報）
    python make_board.py --lat 34.69 --lon 135.50 --name 大阪
"""
import argparse
import json
import math
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1072, 1448
M = 56                       # 左右の余白
JST = timezone(timedelta(hours=9))
HERE = Path(__file__).resolve().parent
WEEKDAYS = "月火水木金土日"

# e-ink は16階調。17の倍数の灰色だけを使う
INK, PENCIL, RULE = 0, 85, 153

# 原稿用紙：S ピクセルのマスを ROWS 行、右から COLS 列
S, ROWS, COLS = 72, 7, 13
GRID_TOP = H - M - S * ROWS
GRID_RIGHT = W - (W - S * COLS) // 2

FONTS = {"bold": HERE / "fonts" / "KleeOne-SemiBold.ttf", "regular": HERE / "fonts" / "KleeOne-Regular.ttf"}
_font_cache = {}

# WMO weather code -> (ことば, アイコン種別)。漢字は1・2年で習うものだけ
WMO = {
    0: ("晴れ", "sun"), 1: ("晴れ", "sun"), 2: ("晴れ ときどき くもり", "partly"), 3: ("くもり", "cloud"),
    45: ("きり", "fog"), 48: ("きり", "fog"),
    51: ("きりさめ", "rain"), 53: ("きりさめ", "rain"), 55: ("きりさめ", "rain"),
    61: ("小雨", "rain"), 63: ("雨", "rain"), 65: ("大雨", "rain"),
    66: ("つめたい 雨", "rain"), 67: ("つめたい 雨", "rain"),
    71: ("小雪", "snow"), 73: ("雪", "snow"), 75: ("大雪", "snow"), 77: ("雪", "snow"),
    80: ("にわか雨", "rain"), 81: ("にわか雨", "rain"), 82: ("はげしい にわか雨", "rain"),
    85: ("にわか雪", "snow"), 86: ("にわか雪", "snow"),
    95: ("かみなり", "thunder"), 96: ("かみなり", "thunder"), 99: ("かみなり", "thunder"),
}

# 縦書きで形や位置を変える文字
SMALL = set("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ")
PERIOD = set("、。")
ROTATE = set("ー～…「」『』（）=")
HANG = set("、。」』）")     # 列の下にはみ出して書いてよい文字（ぶら下げ）


def font(weight, size):
    key = (weight, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS[weight]), size)
    return _font_cache[key]


def fetch(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,precipitation_probability,weather_code"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Asia%2FTokyo&forecast_days=16"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def draw_icon(d, kind, cx, cy, s):
    """簡単な図形で天気アイコンを描く。s はおおよその半径。"""
    def sun(x, y, r):
        w = max(3, int(r // 8))
        d.ellipse((x - r, y - r, x + r, y + r), outline=0, width=w)
        for i in range(8):
            a = math.pi * i / 4
            d.line((x + math.cos(a) * r * 1.35, y + math.sin(a) * r * 1.35,
                    x + math.cos(a) * r * 1.75, y + math.sin(a) * r * 1.75), fill=0, width=w)

    def cloud(x, y, r, fill=255):
        w = max(3, int(r // 8))
        parts = ((x - r * 0.55, y + r * 0.1, r * 0.55), (x + r * 0.1, y - r * 0.25, r * 0.75),
                 (x + r * 0.75, y + r * 0.15, r * 0.5))
        for bx, by, br in parts:
            d.ellipse((bx - br, by - br, bx + br, by + br), fill=fill, outline=0, width=w)
        # 輪郭の重なりを消して下辺を平らにする
        for bx, by, br in parts:
            d.ellipse((bx - br + w, by - br + w, bx + br - w, by + br - w), fill=fill)
        d.rectangle((x - r * 0.55, y + r * 0.1, x + r * 0.75, y + r * 0.65 - w), fill=fill)
        d.line((x - r * 0.55, y + r * 0.65 - w // 2, x + r * 0.75, y + r * 0.65 - w // 2), fill=0, width=w)

    if kind == "sun":
        sun(cx, cy, s * 0.55)
    elif kind == "partly":
        sun(cx - s * 0.3, cy - s * 0.3, s * 0.4)
        cloud(cx + s * 0.1, cy + s * 0.15, s * 0.6)
    elif kind == "cloud":
        cloud(cx, cy, s * 0.75)
    elif kind == "fog":
        cloud(cx, cy - s * 0.2, s * 0.6)
        for i in range(3):
            y = cy + s * 0.35 + i * s * 0.18
            d.line((cx - s * 0.7, y, cx + s * 0.7, y), fill=0, width=max(3, int(s // 12)))
    elif kind in ("rain", "snow", "thunder"):
        cloud(cx, cy - s * 0.25, s * 0.65)
        for i in range(3):
            x = cx - s * 0.45 + i * s * 0.45
            y = cy + s * 0.45
            if kind == "rain":
                d.line((x, y, x - s * 0.12, y + s * 0.3), fill=0, width=max(3, int(s // 10)))
            elif kind == "snow":
                r = s * 0.08
                d.ellipse((x - r, y - r + s * 0.12, x + r, y + r + s * 0.12), fill=0)
        if kind == "thunder":
            pts = [(cx + s * 0.05, cy + s * 0.3), (cx - s * 0.2, cy + s * 0.65), (cx, cy + s * 0.65),
                   (cx - s * 0.15, cy + s * 0.95), (cx + s * 0.25, cy + s * 0.5), (cx + s * 0.05, cy + s * 0.5)]
            d.polygon(pts, fill=0)


def advice(tmax, tmin, rain):
    if rain >= 50:
        return "かさを もって 行こう"
    if tmax >= 30:
        return "水を しっかり のもう"
    if tmin <= 5:
        return "あたたかく して 出かけよう"
    if rain >= 30:
        return "おりたたみがさが あると あんしん"
    return "元気に 行ってらっしゃい！"


def tokens(text):
    """マス目1つ分ずつに分ける。分かち書きの空白はつめ、数字は2けたで1マスにする。"""
    text = text.replace(" ", "").replace("(", "（").replace(")", "）")
    return re.findall(r"\d{1,2}|.", text)


def layout(title, text):
    """(列, 行, 文字, 太字か) のリストを返す。列は右から0。題名は1マス下げ、本文は1行あけて1マス下げで始める。"""
    cells, col, row = [], 0, 1
    for t in tokens(title):
        if row == ROWS:
            col, row = col + 1, 1
        cells.append((col, row, t, True))
        row += 1
    col, row = col + 2, 1
    for t in tokens(text):
        if row == ROWS and t not in HANG:
            col, row = col + 1, 0
        cells.append((col, row, t, False))
        row += 1
    return cells


def draw_cell(img, d, col, row, t, bold):
    cx = GRID_RIGHT - S * (col + 0.5)
    cy = GRID_TOP + S * (row + 0.5)
    size = int(S * 0.72)
    f = font("bold" if bold else "regular", size)
    if len(t) == 2:  # 2けたの数字は横にならべて1マスに入れる
        d.text((cx, cy), t, font=font("bold" if bold else "regular", int(size * 0.7)), fill=INK, anchor="mm")
    elif t in SMALL:
        d.text((cx + size * 0.26, cy - size * 0.3), t, font=f, fill=INK, anchor="mm")
    elif t in PERIOD:
        d.text((cx + size * 0.58, cy - size * 0.58), t, font=f, fill=INK, anchor="mm")
    elif t in ROTATE:
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).text((S / 2, S / 2), t, font=f, fill=255, anchor="mm")
        img.paste(INK, (int(cx - S / 2), int(cy - S / 2)), mask.rotate(-90))
    else:
        d.text((cx, cy), t, font=f, fill=INK, anchor="mm")


def draw_paper(img, d, kinenbi):
    """原稿用紙のマス目と、縦書きの「今日は 何の日」。"""
    d.text((GRID_RIGHT, GRID_TOP - 18), "今日は 何の日？", font=font("bold", 44), fill=INK, anchor="rs")
    left = GRID_RIGHT - S * COLS
    for c in range(COLS + 1):
        x = GRID_RIGHT - S * c
        d.line((x, GRID_TOP, x, GRID_TOP + S * ROWS), fill=RULE, width=2)
    for r in range(ROWS + 1):
        y = GRID_TOP + S * r
        d.line((left, y, GRID_RIGHT, y), fill=RULE, width=2)
    d.rectangle((left, GRID_TOP, GRID_RIGHT, GRID_TOP + S * ROWS), outline=PENCIL, width=3)
    if kinenbi:
        for cell in layout(kinenbi["title"], kinenbi["text"]):
            draw_cell(img, d, *cell)


def render(day, data, kinenbi, name):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    daily, hourly = data["daily"], data["hourly"]
    di = daily["time"].index(day.isoformat()) if day.isoformat() in daily["time"] else None

    # 日付
    date_text = f"{day.month}月{day.day}日"
    d.text((M, 150), date_text, font=font("bold", 132), fill=INK, anchor="ls")
    x = M + d.textlength(date_text, font=font("bold", 132)) + 28
    d.text((x, 150), f"{WEEKDAYS[day.weekday()]}曜日", font=font("bold", 64), fill=INK, anchor="ls")
    d.line((M, 184, W - M, 184), fill=INK, width=4)

    if di is not None:
        label, kind = WMO.get(daily["weather_code"][di], ("", "cloud"))
        tmax, tmin = daily["temperature_2m_max"][di], daily["temperature_2m_min"][di]
        rain = daily["precipitation_probability_max"][di] or 0
        draw_icon(d, kind, 240, 350, 150)
        tx = 480
        d.text((tx, 250), f"{name}の 天気", font=font("regular", 38), fill=PENCIL, anchor="ls")
        size = 72
        while d.textlength(label, font=font("bold", size)) > W - M - tx:
            size -= 4
        d.text((tx, 328), label, font=font("bold", size), fill=INK, anchor="ls")
        for y, word, t in ((432, "さいこう", tmax), (522, "さいてい", tmin)):
            d.text((tx, y), word, font=font("regular", 40), fill=INK, anchor="ls")
            d.text((tx + 190, y + 6), f"{t:.0f}°", font=font("bold", 88), fill=INK, anchor="ls")
        d.text((240, 522), f"雨 {rain}%", font=font("bold", 56), fill=INK, anchor="ms")

        d.rounded_rectangle((M, 552, W - M, 624), radius=36, outline=INK, width=3)
        d.text((W / 2, 588), advice(tmax, tmin, rain), font=font("bold", 46), fill=INK, anchor="mm")

        # 3時間ごと（6時〜21時）
        top = 640
        col_w = (W - 2 * M) / 6
        for c, hour in enumerate(range(6, 24, 3)):
            i = hourly["time"].index(f"{day.isoformat()}T{hour:02d}:00")
            cx = M + col_w * (c + 0.5)
            d.text((cx, top + 20), f"{hour}時", font=font("regular", 34), fill=PENCIL, anchor="mm")
            draw_icon(d, WMO.get(hourly["weather_code"][i], ("", "cloud"))[1], cx, top + 80, 38)
            d.text((cx, top + 144), f"{hourly['temperature_2m'][i]:.0f}°", font=font("bold", 44), fill=INK, anchor="mm")
    else:
        d.text((W / 2, 450), "天気よほうが ありません", font=font("bold", 56), fill=INK, anchor="mm")

    draw_paper(img, d, kinenbi.get(day.strftime("%m-%d")))
    return img


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", type=date.fromisoformat, default=datetime.now(JST).date())
    p.add_argument("--lat", type=float, default=35.68)
    p.add_argument("--lon", type=float, default=139.76)
    p.add_argument("--name", default="東京")
    p.add_argument("--out", default=str(HERE / "public" / "board.png"))
    a = p.parse_args()

    kinenbi = json.loads((HERE / "data" / "kinenbi.json").read_text(encoding="utf-8"))
    img = render(a.date, fetch(a.lat, a.lon), kinenbi, a.name)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    # Kindle の eips は 8bit グレースケール PNG を想定
    img.save(a.out, optimize=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
