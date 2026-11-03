# kindle-board

Kindle Paperwhite 3（脱獄済み）に、毎朝「きょうの てんき」と「きょうは なんの日？」を表示するための画像を作ります。

- `make_board.py` … 天気（Open-Meteo）と `data/kinenbi.json` から 1072×1448 のグレースケールPNGを生成
- `.github/workflows/build.yml` … 毎朝 5:00 JST に生成して GitHub Pages に公開
- `kindle/extensions/dailyboard/` … Kindle 側の KUAL 拡張（毎朝 6:05 に起きて画像を取得・表示）
- `tools/` … 記念日データを Wikipedia の各日ページと照合するスクリプト

画像: https://kim2kimuta.github.io/kindle-board/board.png
