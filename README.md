# kindle-board

Kindle Paperwhite 3（脱獄済み）に、毎朝「今日の 天気」と「今日は 何の日？」を表示するための画像を作ります。
文は小学1・2年で習う漢字までを使い、「何の日」は原稿用紙のマス目に縦書きで表示します。

- `make_board.py` … 天気（Open-Meteo）と `data/kinenbi.json` から 1072×1448 のグレースケールPNGを生成
- `.github/workflows/build.yml` … 毎朝 5:00 JST に生成して GitHub Pages に公開
- `kindle/extensions/dailyboard/` … Kindle 側の KUAL 拡張（毎朝 6:05 に起きて画像を取得・表示）
- `tools/` … 記念日データを Wikipedia の各日ページと照合し、2年生までの漢字だけかを確かめるスクリプト
- `fonts/` … [Klee One](https://github.com/fontworks-fonts/Klee)（SIL OFL）を置く。リポジトリには含めず、Actions が毎回ダウンロードする

手元で生成するときは、先に `fonts/` に KleeOne-Regular.ttf と KleeOne-SemiBold.ttf を入れてください（google/fonts の `ofl/kleeone/` にあります）。

画像: https://kim2kimuta.github.io/kindle-board/board.png
