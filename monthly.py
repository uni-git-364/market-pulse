"""
monthly.py ── 月次アーカイブページを生成する。

docs/data/archive.json に貯めたニュース履歴を月ごとのページにまとめ直す。
「2026年8月に何があったか」を後から振り返れる形にするのが狙いで、
他サイトが持っていない自前の履歴を活かすための入口でもある。

出力:
- docs/archive/<YYYY-MM>.html … その月のまとめ
- docs/archive/index.html      … 月の一覧

方針:
- 冒頭にその月の相場観ブログ（筆者の文章）を置き、リンクの羅列だけにしない。
- 件数が多い月は間引く。月末に偏らないよう、月全体へ均等に散らして選ぶ。
- 見出しの重複（同じ記事が複数媒体から届く）はまとめる。
- 断定的な予想はしない。各ページに免責を表示する。
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from string import Template

ARCHIVE_JSON = Path("docs/data/archive.json")
DOCS = Path("docs")
MONTHLY_DIR = DOCS / "archive"

SITE_URL = "https://uni-git-364.github.io/market-pulse/"
OG_IMAGE = SITE_URL + "ogp.png"

PER_INSTRUMENT = 50          # 1ページに載せる銘柄あたりの件数
INSTRUMENTS = ("ドル円", "ゴールド", "BTC")

DISCLAIMER = (
    "本ページは過去に配信されたニュースの見出しと出典リンクをまとめたものです。"
    "情報提供を目的としており、投資助言ではありません。"
    "内容の正確性・完全性を保証するものではなく、投資判断はご自身の責任で行ってください。"
)

CSS = """
  * { box-sizing: border-box; }
  :root {
    --bg: #f5f5f7; --card-bg: #ffffff; --text: #1a1a1a; --muted: #6b7280;
    --accent: #0b5bd3; --border: #e5e7eb; --chip-bg: #eef2f7;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1115; --card-bg: #181b21; --text: #e8eaed; --muted: #9aa0aa;
      --accent: #6ea8fe; --border: #262b33; --chip-bg: #232934;
    }
  }
  body {
    margin: 0; line-height: 1.7; color: var(--text); background: var(--bg);
    font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif;
    -webkit-text-size-adjust: 100%;
  }
  .wrap { max-width: 720px; margin: 0 auto; padding: 0 14px 40px; }
  header { padding: 16px 2px 4px; }
  .brand a { color: var(--muted); text-decoration: none; font-weight: 700; font-size: 0.9rem; }
  .nav { margin: 6px 0 0; font-size: 0.82rem; }
  .nav a { color: var(--accent); text-decoration: none; font-weight: 600; }
  h1 { font-size: 1.3rem; line-height: 1.5; margin: 16px 0 8px; }
  .lead { color: var(--muted); font-size: 0.85rem; margin: 0 0 18px; }

  .posts { background: var(--card-bg); border: 1px solid var(--border);
           border-radius: 12px; padding: 14px 16px; margin: 0 0 22px; }
  .posts h2 { font-size: 0.9rem; margin: 0 0 8px; color: var(--accent); }
  .posts ul { list-style: none; margin: 0; padding: 0; }
  .posts li { margin: 7px 0; font-size: 0.88rem; line-height: 1.6; }
  .posts a { color: var(--text); text-decoration: none; font-weight: 600; }
  .posts a:hover { color: var(--accent); }
  .posts .d { color: var(--muted); font-size: 0.76rem; margin-right: 6px; }

  h2.inst { font-size: 1.05rem; margin: 26px 0 10px; padding-bottom: 6px;
            border-bottom: 1px solid var(--border); }
  ul.news { list-style: none; margin: 0; padding: 0; }
  ul.news li { border-bottom: 1px solid var(--border); padding: 9px 2px; }
  ul.news li:last-child { border-bottom: none; }
  .d { color: var(--muted); font-size: 0.76rem; }
  .news a { color: var(--accent); text-decoration: none; font-size: 0.92rem;
            font-weight: 600; display: block; margin: 2px 0; }
  .src { color: var(--muted); font-size: 0.75rem; }

  .months { list-style: none; margin: 0; padding: 0;
            display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
  .months a { display: block; background: var(--card-bg); border: 1px solid var(--border);
              border-radius: 10px; padding: 12px 14px; text-decoration: none; color: var(--text); }
  .months a:hover { border-color: var(--accent); }
  .months .n { display: block; color: var(--muted); font-size: 0.76rem; margin-top: 2px; }

  .pager { display: flex; justify-content: space-between; gap: 12px; margin: 26px 0 0; font-size: 0.85rem; }
  .pager a { color: var(--accent); text-decoration: none; font-weight: 600; }
  .disclaimer { color: var(--muted); font-size: 0.76rem; line-height: 1.7;
                border-top: 1px solid var(--border); margin-top: 24px; padding: 14px 4px 0; }
  footer { color: var(--muted); font-size: 0.75rem; text-align: center; padding: 18px 8px 0; }
  footer a { color: var(--accent); text-decoration: none; }
"""

PAGE = Template(
    """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="description" content="$desc">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#0f1115">
<link rel="canonical" href="$canonical">
<link rel="icon" href="${site}favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="${site}apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="$title">
<meta property="og:description" content="$desc">
<meta property="og:url" content="$canonical">
<meta property="og:image" content="$og_image">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<style>
$css
</style>
<!-- GoatCounter（Cookieなしの非公開アクセス解析。数字は市場運営者のみが管理画面で閲覧） -->
<script data-goatcounter="https://market-pulse.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
</head>
<body>
<div class="wrap">
<header>
<p class="brand"><a href="${site}">ドル円・ゴールド・BTC ニュースまとめ</a></p>
<p class="nav"><a href="${site}">← トップ</a> ・ <a href="${site}blog.html">📝 相場観ブログ</a> ・ <a href="${site}archive.html">🔍 記事を検索</a></p>
</header>
$body
<p class="disclaimer">$disclaimer</p>
<footer>最終更新：$updated（JST）<br><a href="${site}about.html">このサイトについて・免責事項</a></footer>
</div>
</body>
</html>
"""
)


def _norm(text: str) -> str:
    """見出しの重複判定用に、全角半角・空白・記号のゆれをならす。"""
    t = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"[\s　\-–—:：|｜/]+", "", t)


def _month_label(ym: str) -> str:
    """'2026-08' → '2026年8月'。"""
    y, m = ym.split("-")
    return "%s年%d月" % (y, int(m))


def _spread(items: list[dict], limit: int) -> list[dict]:
    """月末に偏らないよう、全体へ均等に散らして limit 件選ぶ（古い順のまま返す）。"""
    if len(items) <= limit:
        return items
    step = len(items) / limit
    return [items[int(i * step)] for i in range(limit)]


def _dedupe(items: list[dict]) -> list[dict]:
    """同じ見出しが複数媒体から届くことがあるため、先に見たものだけ残す。"""
    seen: set[str] = set()
    out: list[dict] = []
    for it in items:
        key = _norm(it.get("title"))
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def _load_months() -> dict[str, dict[str, list[dict]]]:
    """アーカイブを {月: {銘柄: [記事...]}} に組み替える（各リストは古い順）。"""
    if not ARCHIVE_JSON.exists():
        return {}
    records = json.loads(ARCHIVE_JSON.read_text(encoding="utf-8"))
    months: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for rec in records:
        published = rec.get("published") or ""
        inst = rec.get("instrument")
        if len(published) < 7 or inst not in INSTRUMENTS:
            continue
        months[published[:7]][inst].append(rec)
    for by_inst in months.values():
        for lst in by_inst.values():
            lst.sort(key=lambda x: x.get("published") or "")
    return months


def _posts_by_month() -> dict[str, list[dict]]:
    """相場観ブログの記事を月ごとにまとめる（無ければ空）。"""
    out: dict[str, list[dict]] = defaultdict(list)
    try:
        import blog
    except Exception:  # noqa: BLE001  markdown 未導入などでも月次生成は続ける
        return out
    if not blog.POSTS_DIR.exists():
        return out
    for path in sorted(blog.POSTS_DIR.glob("*.md")):
        try:
            post = blog.parse_post(path)
        except Exception:  # noqa: BLE001  1本壊れていても他を止めない
            continue
        date = post.get("date") or ""
        if len(date) >= 7:
            out[date[:7]].append(post)
    for lst in out.values():
        lst.sort(key=lambda x: x["date"], reverse=True)
    return out


def _news_section(inst: str, items: list[dict]) -> str:
    rows = []
    for it in items:
        date = (it.get("published") or "")[:10]
        rows.append(
            '<li><span class="d">%s</span>'
            '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
            '<span class="src">%s</span></li>'
            % (
                html.escape(date),
                html.escape(it.get("link") or ""),
                html.escape(it.get("title") or ""),
                html.escape(it.get("source") or ""),
            )
        )
    return '<h2 class="inst">%s</h2>\n<ul class="news">\n%s\n</ul>' % (
        html.escape(inst),
        "\n".join(rows),
    )


def _posts_section(posts: list[dict], ym: str) -> str:
    if not posts:
        return ""
    rows = "".join(
        '<li><span class="d">%s</span><a href="%sblog/%s.html">%s</a></li>'
        % (
            html.escape(p["date"]),
            SITE_URL,
            html.escape(p["slug"]),
            html.escape(p["title"]),
        )
        for p in posts
    )
    return (
        '<div class="posts"><h2>%sの相場観ブログ</h2><ul>%s</ul></div>'
        % (html.escape(_month_label(ym)), rows)
    )


def _render_month(ym: str, by_inst: dict, posts: list[dict], prev_ym, next_ym, now) -> str:
    label = _month_label(ym)
    counts = {inst: len(by_inst.get(inst, [])) for inst in INSTRUMENTS}
    total = sum(counts.values())

    body = [
        "<h1>%sのドル円・ゴールド・BTCニュース</h1>" % html.escape(label),
        '<p class="lead">%sに記録した相場ニュース%s件（%s）から抜粋してまとめています。</p>'
        % (
            html.escape(label),
            f"{total:,}",
            html.escape("・".join(f"{k}{v:,}" for k, v in counts.items())),
        ),
        _posts_section(posts, ym),
    ]
    for inst in INSTRUMENTS:
        items = _dedupe(by_inst.get(inst, []))
        if items:
            body.append(_news_section(inst, _spread(items, PER_INSTRUMENT)))

    pager = []
    if prev_ym:
        pager.append('<a href="%s.html">← %s</a>' % (prev_ym, _month_label(prev_ym)))
    else:
        pager.append("<span></span>")
    if next_ym:
        pager.append('<a href="%s.html">%s →</a>' % (next_ym, _month_label(next_ym)))
    else:
        pager.append("<span></span>")
    body.append('<nav class="pager">%s</nav>' % "".join(pager))
    body.append('<p class="nav" style="margin-top:16px"><a href="index.html">📁 月別アーカイブ一覧</a></p>')

    desc = "%sのドル円（USD/JPY）・ゴールド（金価格）・ビットコインの相場ニュースを月単位で振り返るページ。" % label
    return PAGE.substitute(
        title="%sの相場ニュース振り返り｜ドル円・ゴールド・BTC" % label,
        desc=html.escape(desc),
        canonical="%sarchive/%s.html" % (SITE_URL, ym),
        og_image=OG_IMAGE,
        site=SITE_URL,
        css=CSS,
        body="\n".join(b for b in body if b),
        disclaimer=html.escape(DISCLAIMER),
        updated=now.strftime("%Y-%m-%d %H:%M"),
    )


def _render_index(months: list[str], months_data: dict, now) -> str:
    cards = []
    for ym in months:
        total = sum(len(v) for v in months_data[ym].values())
        cards.append(
            '<li><a href="%s.html">%s<span class="n">ニュース%s件</span></a></li>'
            % (ym, html.escape(_month_label(ym)), f"{total:,}")
        )
    body = (
        "<h1>月別アーカイブ</h1>\n"
        '<p class="lead">ドル円・ゴールド・BTCのニュースを月ごとに振り返れます。'
        "見出しと出典リンクのみを掲載しています。</p>\n"
        '<ul class="months">%s</ul>' % "".join(cards)
    )
    return PAGE.substitute(
        title="月別アーカイブ｜ドル円・ゴールド・BTC ニュースまとめ",
        desc=html.escape(
            "ドル円・ゴールド・ビットコインの相場ニュースを月ごとに振り返る月別アーカイブの一覧。"
        ),
        canonical=SITE_URL + "archive/index.html",
        og_image=OG_IMAGE,
        site=SITE_URL,
        css=CSS,
        body=body,
        disclaimer=html.escape(DISCLAIMER),
        updated=now.strftime("%Y-%m-%d %H:%M"),
    )


def build_monthly(now: datetime) -> list[str]:
    """月次アーカイブを生成し、作ったページの相対URL一覧を返す。"""
    months_data = _load_months()
    if not months_data:
        return []

    months = sorted(months_data)          # 古い順
    posts = _posts_by_month()
    MONTHLY_DIR.mkdir(parents=True, exist_ok=True)

    # 消した月・改名の残骸を防ぐため、生成済みページを一度消してから作り直す
    for old in MONTHLY_DIR.glob("*.html"):
        old.unlink()

    urls: list[str] = []
    for i, ym in enumerate(months):
        prev_ym = months[i - 1] if i > 0 else None
        next_ym = months[i + 1] if i + 1 < len(months) else None
        page = _render_month(ym, months_data[ym], posts.get(ym, []), prev_ym, next_ym, now)
        (MONTHLY_DIR / f"{ym}.html").write_text(page, encoding="utf-8")
        urls.append(f"archive/{ym}.html")

    (MONTHLY_DIR / "index.html").write_text(
        _render_index(list(reversed(months)), months_data, now), encoding="utf-8"
    )
    urls.append("archive/index.html")
    return urls
