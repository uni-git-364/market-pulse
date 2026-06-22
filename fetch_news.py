"""
fetch_news.py ── ドル円・ゴールド・BTC ニュースまとめ（MVP / Phase 1）

Google ニュースの無料 RSS から3銘柄のニュースを取得し、docs/index.html を生成する。

制約（このプロジェクト共通）:
- 著作権: 記事本文は取得・表示しない。見出し＋出典リンク＋出典名＋日時のみ扱う。
- セキュリティ: APIキー・トークンは使わない（このタスクでは不要）。
- 投資助言にしない: 事実の提示にとどめ、断定的な予想はしない。
"""

from __future__ import annotations

import html
from datetime import datetime, timezone, timedelta
from pathlib import Path
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
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "日時不明"


def render_html(data: dict[str, list[dict]], updated_at: datetime) -> str:
    """取得結果から index.html の中身を組み立てる。"""
    sections = []
    for name, items in data.items():
        if items:
            cards = "".join(
                f"""
        <li class="card">
          <a class="headline" href="{html.escape(it['link'])}" target="_blank" rel="noopener noreferrer">{html.escape(it['title'])}</a>
          <div class="meta">{html.escape(it['source'])}・{format_dt(it['published'])}</div>
        </li>"""
                for it in items
            )
        else:
            cards = '\n        <li class="empty">ニュースを取得できませんでした。</li>'
        sections.append(
            f"""
    <section class="instrument">
      <h2>{html.escape(name)}</h2>
      <ul class="news">{cards}
      </ul>
    </section>"""
        )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ドル円・ゴールド・BTC ニュースまとめ</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif;
      line-height: 1.7;
      color: #1a1a1a;
      background: #f5f5f7;
    }}
    .wrap {{ max-width: 720px; margin: 0 auto; padding: 16px; }}
    header h1 {{ font-size: 1.25rem; margin: 8px 0 4px; }}
    .updated {{ color: #666; font-size: 0.85rem; margin: 0 0 16px; }}
    .instrument {{ background: #fff; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; }}
    .instrument h2 {{
      font-size: 1.1rem; margin: 4px 0 12px;
      padding-bottom: 8px; border-bottom: 2px solid #eee;
    }}
    ul.news {{ list-style: none; margin: 0; padding: 0; }}
    .card {{ padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
    .card:last-child {{ border-bottom: none; }}
    .headline {{ color: #0b5bd3; text-decoration: none; font-weight: 600; }}
    .headline:hover {{ text-decoration: underline; }}
    .meta {{ color: #777; font-size: 0.8rem; margin-top: 4px; }}
    .empty {{ color: #999; list-style: none; padding: 8px 0; }}
    footer {{ color: #888; font-size: 0.8rem; text-align: center; padding: 24px 8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>ドル円・ゴールド・BTC ニュースまとめ</h1>
      <p class="updated">最終更新：{updated_at.strftime('%Y-%m-%d %H:%M')}（JST）</p>
    </header>
{''.join(sections)}
    <footer>{html.escape(DISCLAIMER)}</footer>
  </div>
</body>
</html>
"""


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
