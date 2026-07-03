# プロジェクト方針

このリポジトリは「**ドル円・ゴールド・BTC ニュースまとめサイト**」です。
通勤中にスマホで「今、何があったか」をサッと見られる、3銘柄特化のニュースまとめを、
無料RSS＋GitHub Actions＋GitHub Pages で自動更新・公開します。

詳細な背景は [ROADMAP.md](ROADMAP.md) と [CLAUDE_CODE_BRIEF.md](CLAUDE_CODE_BRIEF.md) を参照。

- 公開URL（GitHub Pages, /docs 公開）: https://uni-git-364.github.io/market-pulse/

## 常に守る制約

- **著作権**：ニュース本文をコピーしない。見出し＋出典リンク＋出典名＋（将来は）自分の言葉での要約に徹する。
- **セキュリティ**：APIキー・トークンは GitHub Secrets を使い、コードや公開ファイルに直書きしない。
- **投資助言にしない**：「買え／売れ」「上がる／下がる」と断定しない。事実の提示にとどめ、免責表示を必ず置く。
- **1タスクずつ**：指示されたタスクのみ行い、勝手に先のフェーズを進めない。各ステップでローカル確認方法も伝える。

## 進捗（フェーズ）

- [x] Phase 1 (MVP)：RSS取得 → `docs/index.html` 生成
- [x] Phase 2：GitHub Actions で3時間ごと自動更新＋自動コミット
- [x] Phase 3：モバイル最適化（タブ・相対時刻・ダークモード）
- [x] アーカイブ：`docs/data/archive.json` に追記蓄積＋一覧ページ `docs/archive.html`（検索・銘柄フィルタ・重複統合・もっと見る）
- [x] Phase 5（一部）：取得失敗時に GitHub Issue を自動作成
- [ ] **Phase 4（次・有料）**：AI要約＋時間軸タグ。`ANTHROPIC_API_KEY` を Secrets に登録して使う（コードに直書き禁止）
- [ ] Phase 5（残り）：表紙の重複除去、ノイズ記事フィルタ など
- [ ] Phase 6：SEO・集客（※マネタイズは金商法に注意）

## 主要ファイル

- `fetch_news.py` … RSS取得 → `docs/index.html` 生成 ＋ `docs/data/archive.json` へ追記。銘柄/クエリは冒頭 `QUERIES` 辞書で編集。
- `docs/index.html` … 生成物（**手で編集しない**。`fetch_news.py` を直す）。
- `docs/archive.html` … 静的ページ。`data/archive.json` を fetch して表示。
- `docs/data/archive.json` … 追記のみの履歴（link で重複判定。消えた記事も残す）。
- `.github/workflows/update.yml` … cron(3h)＋手動実行。`docs` をコミット、取得失敗時に Issue 作成。
- `requirements.txt` … feedparser。

## ローカル実行

```bash
pip install -r requirements.txt
python fetch_news.py          # docs/index.html と docs/data/archive.json を更新
start docs/index.html         # 表紙は直開きでOK
```

`docs/archive.html` はJSが `data/archive.json` を読むため **file:// 直開き不可**。
確認は `python -m http.server`（docs内）か公開URLで。

## 運用上の注意

- **コミット署名**：このリポジトリのコミットは noreply メール `292066536+uni-git-364@users.noreply.github.com`（リポジトリ単位の設定）。自動更新のコミット者は `github-actions[bot]`。
- **push 前に rebase**：3時間ごとに bot が `docs/` を自動コミットするため、ローカル `main` は remote より遅れがち。push が弾かれたら `git pull --rebase origin main`。`docs/index.html` の衝突は **`python fetch_news.py` で再生成して解決**する（生成物のため）。
- **コミットは指示があってから**：作業 → ローカル確認 → ユーザーが「コミットして」と言ったら commit & push、の順で進める。
