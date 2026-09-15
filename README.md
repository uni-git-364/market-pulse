# ドル円・ゴールド・BTC ニュースまとめサイト

**🌐 公開サイト：https://uni-git-364.github.io/market-pulse/**

通勤中に「今、何があったか」をサッと見られる、**ドル円・ゴールド・BTC に特化したニュースまとめサイト**。
Google ニュースの無料 RSS から見出しを集め、GitHub Actions で3時間ごとに自動更新して GitHub Pages で公開しています。

- [ニュースまとめ（トップ）](https://uni-git-364.github.io/market-pulse/)
- [相場観ブログ](https://uni-git-364.github.io/market-pulse/blog.html)
- [月別アーカイブ](https://uni-git-364.github.io/market-pulse/archive/index.html)
- [このサイトについて](https://uni-git-364.github.io/market-pulse/about.html)

> 本サイトは情報提供を目的としたものであり、投資助言ではありません。投資判断はご自身の責任で行ってください。

詳細な方針・ロードマップ・進捗は [`ROADMAP.md`](ROADMAP.md) と [`CLAUDE_CODE_BRIEF.md`](CLAUDE_CODE_BRIEF.md) を参照してください。

---

## ローカルでの実行方法

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

（仮想環境を使う場合の例）

```bash
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
pip install -r requirements.txt
```

### 2. ニュースを取得して HTML を生成

```bash
python fetch_news.py
```

実行すると `docs/index.html` が生成され、各銘柄が何件取れたかがコンソールに表示されます。

### 3. 表示を確認

`docs/index.html` をブラウザで開きます。

```bash
# Windows (PowerShell)
start docs/index.html
# macOS
open docs/index.html
```

3銘柄（ドル円・ゴールド・BTC）のニュースが、見出し＋出典リンク＋日時で新しい順に並んでいれば成功です。

---

## 銘柄・検索クエリの変更

`fetch_news.py` の冒頭にある `QUERIES` 辞書を編集すれば、銘柄名や検索キーワードを自由に変えられます。

```python
QUERIES = {
    "ドル円": "ドル円 OR USDJPY 為替",
    "ゴールド": "金価格 OR 金相場 OR 金先物 OR NY金 OR XAU",
    "BTC": "ビットコイン OR BTC 価格",
}
```

「ゴールド」単体の語は商品名・スポンサー名・競走馬の名前などに広く一致してしまうため、クエリには使っていません。
それでも混ざる無関係な記事は、同ファイルの `NOISE_SOURCES`（出典）と `NOISE_WORDS`（見出しの語）で除外しています。

`MAX_ITEMS`（銘柄ごとの件数）も同ファイル上部で変更できます。

---

## GitHub Pages で公開する手順

1. このリポジトリの **Settings → Pages** を開く
2. **Build and deployment** の Source を「Deploy from a branch」にする
3. **Branch** を `main`、フォルダを `/docs` に設定して **Save**
4. 数十秒〜数分後、表示される URL（`https://<ユーザー名>.github.io/<リポジトリ名>/`）でサイトが公開される

> `docs/` を更新してコミット＆プッシュするたびに、公開ページも更新されます。
> 通常は GitHub Actions（`.github/workflows/update.yml`）が3時間ごとに自動で生成・コミットします。

---

## このプロジェクトで守る制約

- **著作権**：記事本文はコピーしない。見出し＋出典リンク＋出典名＋日時のみ扱う。
- **セキュリティ**：API キー・トークンは GitHub Secrets を使い、コードや公開ファイルに直書きしない（Phase 1 では API キー不要）。
- **投資助言にしない**：「買え／売れ」「上がる／下がる」と断定しない。事実の提示にとどめ、免責表示を必ず置く。
