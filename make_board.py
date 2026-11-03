"""Kindle Paperwhite 3 (1072x1448) 向けの「きょうの てんき ＋ きょうは なんの日」画像を生成する。

使い方:
    python make_board.py                         # 今日（日本時間）、東京
    python make_board.py --date 2026-12-25       # 記念日の表示確認用（天気は取得できる範囲の予報）
    python make_board.py --lat 34.69 --lon 135.50 --name おおさか
"""
import argparse
import json
import math
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1072, 1448
BODY_SIZE, BODY_LINES = 42, 4  # 「なんの日」説明文の文字サイズと最大行数
JST = timezone(timedelta(hours=9))
HERE = Path(__file__).resolve().parent
WEEKDAYS = "月火水木金土日"

# 太字・通常の順に探す（Windows: BIZ UDゴシック / Ubuntu: Noto Sans CJK）
FONT_CANDIDATES = {
    "bold": ["C:/Windows/Fonts/BIZ-UDGothicB.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"],
    "regular": ["C:/Windows/Fonts/BIZ-UDGothicR.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"],
}

# WMO weather code -> (子ども向けの ことば, アイコン種別)
WMO = {
    0: ("はれ", "sun"), 1: ("はれ", "sun"), 2: ("はれ ときどき くもり", "partly"), 3: ("くもり", "cloud"),
    45: ("きり", "fog"), 48: ("きり", "fog"),
    51: ("きりさめ", "rain"), 53: ("きりさめ", "rain"), 55: ("きりさめ", "rain"),
    61: ("こさめ", "rain"), 63: ("あめ", "rain"), 65: ("おおあめ", "rain"),
    66: ("つめたい あめ", "rain"), 67: ("つめたい あめ", "rain"),
    71: ("こゆき", "snow"), 73: ("ゆき", "snow"), 75: ("おおゆき", "snow"), 77: ("ゆき", "snow"),
    80: ("にわかあめ", "rain"), 81: ("にわかあめ", "rain"), 82: ("はげしい にわかあめ", "rain"),
    85: ("にわかゆき", "snow"), 86: ("にわかゆき", "snow"),
    95: ("かみなり", "thunder"), 96: ("かみなり", "thunder"), 99: ("かみなり", "thunder"),
}


def font(weight, size):
    for path in FONT_CANDIDATES[weight]:
        if os.path.exists(path):
            # Noto CJK の .ttc は index 0 が JP
            return ImageFont.truetype(path, size, index=0)
    raise FileNotFoundError(f"no {weight} CJK font found")


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


def wrap(d, text, f, width):
    """分かち書きの空白で折り返す。1語が幅を超えるときは文字単位で折る。"""
    lines, cur = [], ""
    for word in text.split(" "):
        cand = f"{cur} {word}" if cur else word
        if d.textlength(cand, font=f) <= width:
            cur = cand
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:
            if d.textlength(cur + ch, font=f) > width:
                lines.append(cur)
                cur = ""
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def advice(tmax, tmin, rain):
    if rain >= 50:
        return "かさを もって いこう"
    if tmax >= 30:
        return "すいぶんを しっかり とろう"
    if tmin <= 5:
        return "あたたかく して でかけよう"
    if rain >= 30:
        return "おりたたみがさが あると あんしん"
    return "げんきに いってらっしゃい！"


def render(day, data, kinenbi, name):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    daily, hourly = data["daily"], data["hourly"]
    di = daily["time"].index(day.isoformat()) if day.isoformat() in daily["time"] else None

    # ヘッダー：日付
    d.text((56, 40), f"{day.month}月{day.day}日", font=font("bold", 120), fill=0)
    x = 56 + d.textlength(f"{day.month}月{day.day}日", font=font("bold", 120)) + 20
    d.text((x, 92), f"{WEEKDAYS[day.weekday()]}よう日", font=font("bold", 60), fill=0)
    d.line((56, 200, W - 56, 200), fill=0, width=5)

    # きょうの てんき
    if di is not None:
        label, kind = WMO.get(daily["weather_code"][di], ("", "cloud"))
        tmax, tmin = daily["temperature_2m_max"][di], daily["temperature_2m_min"][di]
        rain = daily["precipitation_probability_max"][di] or 0
        draw_icon(d, kind, 250, 410, 170)
        d.text((500, 222), f"{name}の てんき", font=font("regular", 34), fill=0)
        d.text((500, 262), label, font=font("bold", 64), fill=0)
        d.text((500, 360), "さいこう", font=font("regular", 40), fill=0)
        d.text((680, 332), f"{tmax:.0f}°", font=font("bold", 92), fill=0)
        d.text((500, 465), "さいてい", font=font("regular", 40), fill=0)
        d.text((680, 437), f"{tmin:.0f}°", font=font("bold", 92), fill=0)
        d.text((500, 560), f"あめの かくりつ  {rain}%", font=font("regular", 42), fill=0)
        d.rounded_rectangle((56, 620, W - 56, 700), radius=40, outline=0, width=4)
        d.text((W / 2, 660), advice(tmax, tmin, rain), font=font("bold", 46), fill=0, anchor="mm")

        # 3時間ごと（6時〜21時）
        top = 720
        col_w = (W - 112) / 6
        for c, hour in enumerate(range(6, 24, 3)):
            i = hourly["time"].index(f"{day.isoformat()}T{hour:02d}:00")
            cx = 56 + col_w * (c + 0.5)
            d.text((cx, top + 28), f"{hour}じ", font=font("regular", 36), fill=0, anchor="mm")
            draw_icon(d, WMO.get(hourly["weather_code"][i], ("", "cloud"))[1], cx, top + 105, 48)
            d.text((cx, top + 190), f"{hourly['temperature_2m'][i]:.0f}°", font=font("bold", 48), fill=0, anchor="mm")
            d.text((cx, top + 240), f"{hourly['precipitation_probability'][i]}%", font=font("regular", 30), fill=0, anchor="mm")
    else:
        d.text((W / 2, 500), "てんきよほうが ありません", font=font("bold", 56), fill=0, anchor="mm")

    # きょうは なんの日？
    top = 1020
    d.line((56, top - 20, W - 56, top - 20), fill=0, width=5)
    d.rounded_rectangle((56, top, 456, top + 66), radius=33, fill=0)
    d.text((256, top + 33), "きょうは なんの日？", font=font("bold", 38), fill=255, anchor="mm")
    k = kinenbi.get(day.strftime("%m-%d"))
    if k:
        title_font = font("bold", 72)
        while d.textlength(k["title"], font=title_font) > W - 112 and title_font.size > 48:
            title_font = font("bold", title_font.size - 4)
        d.text((56, top + 82), k["title"], font=title_font, fill=0)
        body = font("regular", BODY_SIZE)
        y = top + 180
        for line in wrap(d, k["text"], body, W - 112)[:BODY_LINES]:
            d.text((56, y), line, font=body, fill=0)
            y += 58

    return img


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", type=date.fromisoformat, default=datetime.now(JST).date())
    p.add_argument("--lat", type=float, default=35.68)
    p.add_argument("--lon", type=float, default=139.76)
    p.add_argument("--name", default="とうきょう")
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
