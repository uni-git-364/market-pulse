"""
blog.py ── 相場観ブログ（筆者の見解）を posts/*.md から生成する。

レイアウト:
- 記事が主役（左〜中央）＋ 右側に記事一覧のサイドバー（アーカイブ風）。スマホでは縦積み。
- docs/blog.html … 最新記事のページ
- docs/blog/<slug>.html … それ以外の各記事ページ（重複を避けるため最新はここに作らない）

方針:
- 記事は posts/ に Markdown で書く（フロントマター: title / tag / date）。
- 中身（相場観）はここでは生成しない。筆者が執筆する前提。
- 断定的な予想・売買推奨はしない。各ページに免責を表示する。
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path
from string import Template

import markdown

POSTS_DIR = Path("posts")
DOCS = Path("docs")
BLOG_INDEX = DOCS / "blog.html"
BLOG_DIR = DOCS / "blog"

SITE_URL = "https://uni-git-364.github.io/market-pulse/"
OG_IMAGE = SITE_URL + "ogp.png"
BADGE_COLOR = {
    "ドル円": "#6ea8fe",
    "ゴールド": "#f5c518",
    "BTC": "#f7931a",
    "今日の相場": "#0b5bd3",
    "今週の3市場": "#7c3aed",
}

BLOG_DISCLAIMER = (
    "本ページの記事は筆者個人の見解であり、特定の金融商品の売買を推奨・勧誘するものではありません。"
    "将来の価格や相場の動きを保証・約束するものではなく、内容の正確性・完全性も保証しません。"
    "投資の最終判断はご自身の責任で行ってください。"
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
    margin: 0; line-height: 1.8; color: var(--text); background: var(--bg);
    font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif;
    -webkit-text-size-adjust: 100%;
  }
  .wrap { max-width: 1040px; margin: 0 auto; padding: 0 16px 40px; }
  header { padding: 16px 2px 4px; }
  .brand a { color: var(--muted); text-decoration: none; font-weight: 700; font-size: 0.9rem; }
  .sub { margin: 6px 0 0; font-size: 0.82rem; color: var(--muted); }
  .sub a { color: var(--accent); text-decoration: none; font-weight: 600; }

  .layout { display: grid; grid-template-columns: minmax(0,1fr) 260px; gap: 28px; margin-top: 14px; align-items: start; }
  @media (max-width: 760px) { .layout { grid-template-columns: 1fr; } }

  .article { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 24px 26px; min-width: 0; }
  .post-meta { display: flex; gap: 10px; align-items: center; color: var(--muted); font-size: 0.78rem; }
  .badge { background: var(--chip-bg); border: 1px solid; border-radius: 6px; padding: 1px 8px; font-size: 0.74rem; font-weight: 700; }
  .post-title { font-size: 1.5rem; line-height: 1.5; margin: 6px 0 16px; }
  .article-body { font-size: 0.98rem; }
  .article-body h2 { font-size: 1.15rem; margin: 26px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
  .article-body h3 { font-size: 1.02rem; margin: 20px 0 8px; }
  .article-body p { margin: 12px 0; }
  .article-body a { color: var(--accent); }
  .article-body ul, .article-body ol { padding-left: 1.3em; }
  .article-body li { margin: 4px 0; }
  .article-body blockquote { margin: 14px 0; padding: 6px 16px; border-left: 3px solid var(--accent); color: var(--muted); }
  .article-body hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
  .article-body code { background: var(--chip-bg); padding: 1px 5px; border-radius: 5px; font-size: 0.9em; }
  .article-body em { color: var(--muted); }
  .table-scroll { overflow-x: auto; margin: 14px 0; }
  .article-body table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  .article-body th, .article-body td { border: 1px solid var(--border); padding: 7px 10px; text-align: left; }
  .article-body th { background: var(--chip-bg); white-space: nowrap; }

  .sidebar { position: sticky; top: 16px; align-self: start; }
  .sidebar h2 { font-size: 0.85rem; color: var(--muted); margin: 0 0 8px; padding: 0 2px; }
  .sb-list { list-style: none; margin: 0; padding: 0; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--card-bg); }
  .sb-item a { display: block; padding: 11px 14px; text-decoration: none; color: var(--text); border-bottom: 1px solid var(--border); }
  .sb-item:last-child a { border-bottom: none; }
  .sb-item a:hover { background: var(--chip-bg); }
  .sb-item.current a { background: var(--chip-bg); border-left: 3px solid var(--accent); }
  .sb-date { display: block; font-size: 0.72rem; color: var(--muted); }
  .sb-title { display: block; font-size: 0.86rem; font-weight: 600; margin-top: 2px; line-height: 1.4; }

  .empty { color: var(--muted); padding: 30px 4px; }
  .disclaimer { color: var(--muted); font-size: 0.78rem; line-height: 1.7; border-top: 1px solid var(--border); margin-top: 26px; padding: 16px 4px 0; }
  footer { color: var(--muted); font-size: 0.75rem; text-align: center; padding: 18px 8px 0; }
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
<link rel="icon" type="image/svg+xml" href="${site}favicon.svg">
<link rel="apple-touch-icon" href="${site}apple-touch-icon.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ドル円・ゴールド・BTC ニュースまとめ">
<meta property="og:title" content="$title">
<meta property="og:description" content="$desc">
<meta property="og:url" content="$canonical">
<meta property="og:image" content="$og_image">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="$title">
<meta name="twitter:description" content="$desc">
<meta name="twitter:image" content="$og_image">
<style>
$css
</style>
</head>
<body>
<div class="wrap">
<header>
<p class="brand"><a href="${home}">ドル円・ゴールド・BTC ニュースまとめ</a></p>
<p class="sub"><strong>📝 相場観ブログ</strong> ・ <a href="${home}">← トップ（最新ニュース）</a> ・ <a href="${archive}">📁 アーカイブ</a></p>
</header>
<div class="layout">
<main>
$article
<p class="disclaimer">$disclaimer</p>
</main>
<aside class="sidebar">
<h2>記事一覧</h2>
<ul class="sb-list">
$sidebar
</ul>
</aside>
</div>
<footer>最終更新：$updated（JST）</footer>
</div>
</body>
</html>
"""
)


def _md(body: str) -> str:
    html_out = markdown.markdown(body.strip(), extensions=["extra", "sane_lists"])
    # 横スクロールできるよう、表を div で包む（スマホ対策）
    return html_out.replace("<table>", '<div class="table-scroll"><table>').replace(
        "</table>", "</table></div>"
    )


def parse_post(path: Path) -> dict:
    """1つの Markdown 記事を読み、フロントマターと本文HTMLを返す。"""
    raw = path.read_text(encoding="utf-8")
    meta = {"title": path.stem, "tag": "", "date": ""}
    body = raw
    if raw.lstrip().startswith("---"):
        parts = raw.split("---", 2)  # ['', frontmatter, body]（本文中の --- は残る）
        if len(parts) == 3:
            _, fm, body = parts
            for line in fm.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
    body_html = _md(body)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body_html)).strip()
    return {
        "title": meta.get("title", path.stem),
        "tag": meta.get("tag", meta.get("instrument", "")),
        "date": meta.get("date", ""),
        "slug": path.stem,
        "body_html": body_html,
        "excerpt": text[:100],
    }


def _href(post: dict, from_root: bool) -> str:
    """一覧から各記事へのリンク（ページの階層に応じて相対パスを変える）。

    最新記事も永続URL（blog/<slug>.html）を持つため、全記事とも同じ規則。
    ルート階層（blog.html）からは blog/<slug>.html、blog/ 配下からは <slug>.html。
    """
    return ("blog/" if from_root else "") + post["slug"] + ".html"


def _sidebar(posts: list[dict], current_slug: str, from_root: bool) -> str:
    items = []
    for p in posts:
        cur = " current" if p["slug"] == current_slug else ""
        items.append(
            '<li class="sb-item%s"><a href="%s">'
            '<span class="sb-date">%s</span>'
            '<span class="sb-title">%s</span></a></li>'
            % (cur, _href(p, from_root), html.escape(p["date"]), html.escape(p["title"]))
        )
    return "\n".join(items)


def _article_html(post: dict) -> str:
    tag = post["tag"]
    color = BADGE_COLOR.get(tag, "#9aa0aa")
    badge = (
        '<span class="badge" style="color:%s;border-color:%s">%s</span>'
        % (color, color, html.escape(tag))
        if tag
        else ""
    )
    return (
        '<article class="article">\n'
        '<div class="post-meta"><time>%s</time>%s</div>\n'
        '<h1 class="post-title">%s</h1>\n'
        '<div class="article-body">%s</div>\n'
        "</article>"
    ) % (html.escape(post["date"]), badge, html.escape(post["title"]), post["body_html"])


def _render(post, posts, from_root, canonical, now) -> str:
    site = SITE_URL  # favicon/OGP は絶対URL（サブ階層でも壊れない）
    home = "index.html" if from_root else "../index.html"
    archive = "archive.html" if from_root else "../archive.html"
    if post is None:
        article = '<article class="article"><h1 class="post-title">📝 相場観ブログ</h1>' \
                  '<p class="empty">まだ記事がありません。posts/ に Markdown を追加してください。</p></article>'
        title = "相場観ブログ｜ドル円・ゴールド・BTCニュースまとめ"
        desc = "ドル円・ゴールド・ビットコインの相場を筆者の視点で読み解くブログ。"
        current_slug = ""
    else:
        article = _article_html(post)
        title = post["title"] + "｜相場観ブログ"
        desc = post["excerpt"] or "ドル円・ゴールド・ビットコインの相場観。"
        current_slug = post["slug"]
    return PAGE.substitute(
        title=html.escape(title),
        desc=html.escape(desc),
        canonical=canonical,
        og_image=OG_IMAGE,
        site=site,
        home=home,
        archive=archive,
        css=CSS,
        article=article,
        sidebar=_sidebar(posts, current_slug, from_root),
        disclaimer=html.escape(BLOG_DISCLAIMER),
        updated=now.strftime("%Y-%m-%d %H:%M"),
    )


def build_blog(now: datetime) -> list[str]:
    """posts/*.md から blog.html と blog/<slug>.html を生成し、生成ページの相対URL一覧を返す。"""
    posts: list[dict] = []
    if POSTS_DIR.exists():
        for p in sorted(POSTS_DIR.glob("*.md")):
            posts.append(parse_post(p))
    posts.sort(key=lambda x: (x["date"], x["slug"]), reverse=True)  # 新しい順

    # 生成済みの記事ページを一旦クリア（削除・改名した記事の残骸を防ぐ）
    if BLOG_DIR.exists():
        for f in BLOG_DIR.glob("*.html"):
            f.unlink()

    urls: list[str] = []
    if not posts:
        BLOG_INDEX.write_text(_render(None, [], True, SITE_URL + "blog.html", now), encoding="utf-8")
        return ["blog.html"]

    latest = posts[0]

    # 全記事（最新を含む）を blog/<slug>.html に出力する。
    # → 最新記事も固定URLを持ち、翌日以降も同じリンクで参照できる。
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    for post in posts:
        rel = "blog/" + post["slug"] + ".html"
        (DOCS / rel).write_text(
            _render(post, posts, False, SITE_URL + rel, now), encoding="utf-8"
        )
        urls.append(rel)

    # blog.html は最新記事を載せる入口ページ。canonical は最新記事の永続URLを
    # 指し、blog.html と実体ページの重複コンテンツ判定を避ける。
    latest_permalink = SITE_URL + "blog/" + latest["slug"] + ".html"
    BLOG_INDEX.write_text(
        _render(latest, posts, True, latest_permalink, now), encoding="utf-8"
    )
    urls.insert(0, "blog.html")

    return urls
