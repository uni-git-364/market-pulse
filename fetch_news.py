"""
fetch_news.py ── ドル円・ゴールド・BTC ニュースまとめ

Google ニュースの無料 RSS から3銘柄のニュースを取得し、docs/index.html を生成する。

制約（このプロジェクト共通）:
- 著作権: 記事本文は取得・表示しない。見出し＋出典リンク＋出典名＋日時のみ扱う。
- セキュリティ: APIキー・トークンは使わない（このタスクでは不要）。
- 投資助言にしない: 事実の提示にとどめ、断定的な予想はしない。

Phase 3: スマホ最適化（タブ切替・相対時刻・ダークモード）。外部ライブラリ・JSは不使用。
"""

from __future__ import annotations

import html
from datetime import datetime, timezone, timedelta
from pathlib import Path
from string import Template
from urllib.parse import quote

import feedparser

# ---- ここを編集すれば銘柄・検索クエリを変えられます ----
QUERIES: dict[str, str] = {
    "ドル円": "ドル円 OR USDJPY 為替",
    "ゴールド": "金価格 OR ゴールド OR XAU",
    "BTC": "ビットコイン OR BTC 価格",
}

MAX_ITEMS = 10                       # 銘柄ごとに取得する最大件数
OUTPUT_PATH = Path("docs/index.html")  # GitHub Pages を /docs 公開にするため

JST = timezone(timedelta(hours=9))
RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"

DISCLAIMER = (
    "本サイトは情報提供を目的としたものであり、投資助言ではありません。"
    "投資判断はご自身の責任で行ってください。"
)


def build_rss_url(query: str) -> str:
    """検索クエリから Google ニュース RSS の URL を組み立てる。"""
    return RSS_TEMPLATE.format(query=quote(query))


def to_jst(struct_time) -> datetime | None:
    """feedparser の *_parsed（UTC の struct_time）を JST の datetime に変換する。"""
    if not struct_time:
        return None
    dt_utc = datetime(*struct_time[:6], tzinfo=timezone.utc)
    return dt_utc.astimezone(JST)


def get_source_name(entry) -> str:
    """記事の出典（媒体名）を取り出す。"""
    # Google ニュース RSS は <source> 要素に媒体名が入る
    source = entry.get("source")
    if source and source.get("title"):
        return source.get("title")
    # フォールバック: タイトル末尾の " - 媒体名"
    title = entry.get("title", "")
    if " - " in title:
        return title.rsplit(" - ", 1)[1].strip()
    return "出典不明"


def clean_title(entry) -> str:
    """見出しから末尾の " - 媒体名" を取り除く（媒体名は別に表示するため）。"""
    title = entry.get("title", "").strip()
    suffix = f" - {get_source_name(entry)}"
    if title.endswith(suffix):
        title = title[: -len(suffix)].strip()
    return title or "(無題)"


def fetch_items(query: str, limit: int) -> list[dict]:
    """1銘柄分のニュースを取得して、新しい順に limit 件返す。"""
    feed = feedparser.parse(build_rss_url(query))
    items: list[dict] = []
    for entry in feed.entries:
        items.append(
            {
                "title": clean_title(entry),
                "link": entry.get("link", ""),
                "source": get_source_name(entry),
                "published": to_jst(entry.get("published_parsed")),
            }
        )
    # 新しい順に並べる（日時不明は末尾へ）
    oldest = datetime.min.replace(tzinfo=JST)
    items.sort(key=lambda x: x["published"] or oldest, reverse=True)
    return items[:limit]


def format_dt(dt: datetime | None) -> str:
    """絶対時刻（YYYY-MM-DD HH:MM）。カードのツールチップ用。"""
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "日時不明"


def relative_time(dt: datetime | None, now: datetime) -> str:
    """now を基準にした相対時刻（例：2時間前）。1週間以上前は日付表示。"""
    if not dt:
        return "日時不明"
    secs = max((now - dt).total_seconds(), 0)
    mins = secs / 60
    if mins < 1:
        return "たった今"
    if mins < 60:
        return "%d分前" % int(mins)
    hours = mins / 60
    if hours < 24:
        return "%d時間前" % int(hours)
    days = int(hours / 24)
    if days < 7:
        return "%d日前" % days
    return dt.strftime("%Y-%m-%d")


# ---- 見た目（CSS）。外部依存なし。ダークモードは prefers-color-scheme で自動切替 ----
CSS = """
    * { box-sizing: border-box; }
    :root {
      --bg: #f5f5f7;
      --card-bg: #ffffff;
      --text: #1a1a1a;
      --muted: #6b7280;
      --accent: #0b5bd3;
      --border: #e5e7eb;
      --tabbar-bg: rgba(245,245,247,0.92);
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0f1115;
        --card-bg: #181b21;
        --text: #e8eaed;
        --muted: #9aa0aa;
        --accent: #6ea8fe;
        --border: #262b33;
        --tabbar-bg: rgba(15,17,21,0.92);
      }
    }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif;
      line-height: 1.7;
      color: var(--text);
      background: var(--bg);
      -webkit-text-size-adjust: 100%;
    }
    .wrap { max-width: 680px; margin: 0 auto; padding: 0 14px 32px; }
    header { padding: 18px 2px 6px; }
    header h1 { font-size: 1.15rem; margin: 0 0 4px; }
    .updated { color: var(--muted); font-size: 0.8rem; margin: 0; }

    /* タブ：CSSのみで切替（ラジオボタン方式・JS不使用） */
    .tab-radio { display: none; }
    .tablist {
      position: sticky; top: 0; z-index: 10;
      display: flex; gap: 4px;
      background: var(--tabbar-bg);
      backdrop-filter: blur(8px);
      padding: 8px 0 0; margin: 8px 0 6px;
      border-bottom: 1px solid var(--border);
    }
    .tab-label {
      flex: 1; text-align: center;
      padding: 11px 6px;
      font-size: 0.95rem; font-weight: 600;
      color: var(--muted);
      border-bottom: 2px solid transparent;
      cursor: pointer; user-select: none;
    }
    .tab-label:active { background: rgba(127,127,127,0.12); }

    .panel { display: none; }
    ul.news { list-style: none; margin: 0; padding: 0; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 13px 15px; margin: 10px 0;
    }
    .headline {
      color: var(--accent); text-decoration: none;
      font-weight: 600; font-size: 1.02rem; display: block;
    }
    .headline:active { opacity: 0.7; }
    .meta {
      display: flex; justify-content: space-between; gap: 10px;
      color: var(--muted); font-size: 0.78rem; margin-top: 7px;
    }
    .meta .source { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .meta .time { flex-shrink: 0; }
    .empty { color: var(--muted); padding: 16px 4px; }
    footer {
      color: var(--muted); font-size: 0.76rem;
      text-align: center; padding: 26px 10px 0; line-height: 1.6;
    }
"""

PAGE = Template(
    """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ドル円・ゴールド・BTC ニュースまとめ</title>
<style>
$css
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>ドル円・ゴールド・BTC ニュースまとめ</h1>
<p class="updated">最終更新：$updated（JST）</p>
</header>
<div class="tabs">
$radios<nav class="tablist">
$labels</nav>
$panels</div>
<footer>$disclaimer</footer>
</div>
</body>
</html>
"""
)


def card_html(it: dict, now: datetime) -> str:
    return (
        '<li class="card">'
        '<a class="headline" href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
        '<div class="meta"><span class="source">%s</span>'
        '<span class="time" title="%s">%s</span></div>'
        "</li>\n"
    ) % (
        html.escape(it["link"]),
        html.escape(it["title"]),
        html.escape(it["source"]),
        format_dt(it["published"]),
        relative_time(it["published"], now),
    )


def render_html(data: dict[str, list[dict]], updated_at: datetime) -> str:
    """取得結果から index.html を組み立てる。"""
    names = list(data.keys())

    radios = "".join(
        '<input type="radio" name="tab" id="tab-%d" class="tab-radio"%s>\n'
        % (i, " checked" if i == 0 else "")
        for i in range(len(names))
    )
    labels = "".join(
        '<label for="tab-%d" class="tab-label">%s</label>\n' % (i, html.escape(name))
        for i, name in enumerate(names)
    )
    panels = ""
    for i, name in enumerate(names):
        items = data[name]
        if items:
            cards = "".join(card_html(it, updated_at) for it in items)
        else:
            cards = '<li class="empty">ニュースを取得できませんでした。</li>\n'
        panels += (
            '<section class="panel" id="panel-%d">\n<ul class="news">\n%s</ul>\n</section>\n'
            % (i, cards)
        )

    # タブの表示切替CSS（チェックされたラジオに対応するパネル／ラベルを強調）
    tab_css = "\n".join(
        "    #tab-%d:checked ~ #panel-%d { display: block; }\n"
        '    #tab-%d:checked ~ .tablist label[for="tab-%d"]'
        " { color: var(--accent); border-bottom-color: var(--accent); }"
        % (i, i, i, i)
        for i in range(len(names))
    )

    return PAGE.substitute(
        css=CSS + "\n" + tab_css,
        updated=updated_at.strftime("%Y-%m-%d %H:%M"),
        radios=radios,
        labels=labels,
        panels=panels,
        disclaimer=html.escape(DISCLAIMER),
    )


def main() -> None:
    data: dict[str, list[dict]] = {}
    for name, query in QUERIES.items():
        items = fetch_items(query, MAX_ITEMS)
        data[name] = items
        print(f"{name}: {len(items)} 件取得")

    html_text = render_html(data, datetime.now(JST))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html_text, encoding="utf-8")
    print(f"生成しました → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
