"""
make_assets.py ── サイトのアイコン／OGP画像を生成する一回きりのツール。

生成物（すべて docs/ 配下・GitHub Pages で配信）:
- favicon.ico          … レガシー用ファビコン（16/32/48px）
- apple-touch-icon.png … iOSホーム画面用（180px）
- ogp.png              … SNS共有カード用（1200x630）

※ このスクリプトは Pillow を使うが、サイトの自動更新（fetch_news.py / GitHub Actions）
   には不要。ローカルで画像を作り直したい時だけ実行する:  pip install pillow && python make_assets.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOCS = Path("docs")
FONT = "C:/Windows/Fonts/YuGothB.ttc"  # 游ゴシック Bold（日本語対応）

BG = (15, 17, 21)          # #0f1115
WHITE = (240, 242, 245)
MUTED = (154, 160, 170)
BLUE = (110, 168, 254)     # ドル円
GOLD = (245, 197, 24)      # ゴールド
ORANGE = (247, 147, 26)    # BTC


def draw_mark(size: int, rounded: bool = True) -> Image.Image:
    """上昇トレンド＋金色ドットのブランドマークを描く。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=BG)
    else:
        d.rectangle([0, 0, size - 1, size - 1], fill=BG)
    pts = [(0.19, 0.69), (0.375, 0.53), (0.53, 0.625), (0.81, 0.25)]
    line = [(x * size, y * size) for x, y in pts]
    d.line(line, fill=BLUE, width=max(2, int(size * 0.08)), joint="curve")
    cx, cy, r = 0.81 * size, 0.25 * size, size * 0.095
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    return img


def make_favicon() -> None:
    mark = draw_mark(256, rounded=True)
    mark.save(DOCS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


def make_apple_icon() -> None:
    draw_mark(180, rounded=False).save(DOCS / "apple-touch-icon.png")


def _pill(d: ImageDraw.ImageDraw, x: int, y: int, text: str, font, color) -> int:
    b = d.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    padx, pady = 24, 12
    w, h = tw + padx * 2, th + pady * 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=(32, 37, 46), outline=color, width=2)
    d.text((x + padx - b[0], y + pady - b[1]), text, font=font, fill=color)
    return x + w + 18


def make_ogp() -> None:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title = ImageFont.truetype(FONT, 76)
    tag = ImageFont.truetype(FONT, 30)
    chip = ImageFont.truetype(FONT, 30)
    url = ImageFont.truetype(FONT, 26)

    # ブランドマーク（左上）
    img.paste(draw_mark(120, rounded=True), (80, 60), draw_mark(120, rounded=True))

    # タイトル2行
    d.text((80, 210), "ドル円・ゴールド・BTC", font=title, fill=WHITE)
    d.text((80, 306), "ニュースまとめ", font=title, fill=WHITE)
    # タイトル下のアクセント
    d.rectangle([84, 404, 320, 410], fill=BLUE)

    # タグライン
    d.text((80, 440), "為替・金・ビットコインの値動きに関わる材料を自動でまとめてお届け",
           font=tag, fill=MUTED)

    # 銘柄チップ
    x = _pill(d, 80, 500, "ドル円", chip, BLUE)
    x = _pill(d, x, 500, "ゴールド", chip, GOLD)
    _pill(d, x, 500, "BTC", chip, ORANGE)

    # URL
    d.text((80, 574), "uni-git-364.github.io/market-pulse", font=url, fill=MUTED)

    img.save(DOCS / "ogp.png")


if __name__ == "__main__":
    make_favicon()
    make_apple_icon()
    make_ogp()
    print("生成しました: favicon.ico / apple-touch-icon.png / ogp.png")
