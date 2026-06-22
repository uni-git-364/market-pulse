# ドル円・ゴールド・BTC ニュースまとめサイト

通勤中に「今、何があったか」をサッと見られる、**ドル円・ゴールド・BTC に特化したニュースまとめサイト**。
Google ニュースの無料 RSS から見出しを集め、静的な `docs/index.html` を生成して GitHub Pages で公開します。

> 本サイトは情報提供を目的としたものであり、投資助言ではありません。投資判断はご自身の責任で行ってください。

詳細な方針・ロードマップは [`ROADMAP.md`](ROADMAP.md) と [`CLAUDE_CODE_BRIEF.md`](CLAUDE_CODE_BRIEF.md) を参照してください。

現在の到達点：**Phase 1（最小版 / MVP）** — ニュース取得 → HTML 生成まで。

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
    "ゴールド": "金価格 OR ゴールド OR XAU",
    "BTC": "ビットコイン OR BTC 価格",
}
```

`MAX_ITEMS`（銘柄ごとの件数）も同ファイル上部で変更できます。

---

## GitHub Pages で公開する手順

1. このリポジトリの **Settings → Pages** を開く
2. **Build and deployment** の Source を「Deploy from a branch」にする
3. **Branch** を `main`、フォルダを `/docs` に設定して **Save**
4. 数十秒〜数分後、表示される URL（`https://<ユーザー名>.github.io/<リポジトリ名>/`）でサイトが公開される

> `docs/index.html` を更新してコミット＆プッシュするたびに、公開ページも更新されます。
> 3時間ごとの自動更新は Phase 2（GitHub Actions）で追加します。

---

## このプロジェクトで守る制約

- **著作権**：記事本文はコピーしない。見出し＋出典リンク＋出典名＋日時のみ扱う。
- **セキュリティ**：API キー・トークンは GitHub Secrets を使い、コードや公開ファイルに直書きしない（Phase 1 では API キー不要）。
- **投資助言にしない**：「買え／売れ」「上がる／下がる」と断定しない。事実の提示にとどめ、免責表示を必ず置く。
