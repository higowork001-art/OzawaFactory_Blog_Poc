# SPEC.md — YouTube → AI SEO記事生成システム 仕様書

> **バージョン**: 1.4.0  
> **最終更新**: 2026-09-09  
> **ステータス**: モバイル表示最適化（スマホレスポンシブ） & Google AdSense広告枠対応完了

---

> [!IMPORTANT]
> **引き継ぎ・作業記録の運用ルール**  
> 異なるAIモデル・エージェント・開発アカウント間でも作業内容を正確に引き継げるよう、**コード変更や機能追加を伴う実行ごとに、必ず本仕様書（`SPEC.md`）および作業ログ（`WORKLOG.md`）へ変更内容と検証結果を更新・追記すること**。

---

## 1. プロジェクト概要

YouTube URLを単体で指定するか、YouTubeチャンネルURLを設定して最新動画を最大10件自動取得し、字幕と概要欄からAIで分析・SEO向けブログ記事（Markdown + HTML）を一括生成するシステム。WordPress REST API連携により記事・アイキャッチ画像・固定ページ（AdSense用4種）の自動登録に対応しています。重複防止リストにより同じ動画の二重処理を防ぎます。

```
[単一入力] YouTube URL ──┐
                         ├──> [自動判定/一括] 未処理動画の抽出 ──> 動画情報取得 ──> 字幕取得 ──> AI分析 ──> 記事生成 ──> HTML生成 ──> [オプション] WP投稿 ──> 重複記録
[自動取得] チャンネルURL ──┘
```

---

## 2. ディレクトリ構成

```
youtube_article_ai/（プロジェクトルート: c:/AntiGravity/AIYouTublog/）
├── main.py                    # エントリーポイント（単一処理/一括自動処理/WP自動投稿）
├── config.py                  # 環境変数・定数・WPカテゴリ設定の一元管理
├── requirements.txt           # 依存パッケージ
├── .env                       # APIキー・チャンネルURL・WP接続・サイト情報設定
├── PLAN.md                    # AdSense対応 & WordPress連携 拡張計画書
├── README.md                  # セットアップ・実行手順
├── SPEC.md                    # 本仕様書（本ファイル）
├── WORKLOG.md                 # 作業ログ
├── src/
│   ├── youtube.py             # yt-dlpによるメタデータ取得・チャンネル一覧取得
│   ├── transcript.py          # 字幕取得・クリーニング
│   ├── analyzer.py            # AI分析（Gemini API / JSON出力）
│   ├── article_generator.py   # AI記事生成（Gemini API / Markdown出力）
│   ├── output.py              # ファイル保存処理
│   ├── html_generator.py      # MarkdownからHTMLへの変換・保存
│   ├── screenshot.py          # 重要シーンのスクショ自動抽出
│   ├── tracker.py             # 処理済み動画IDの重複防止トラッカー
│   ├── wordpress.py           # WordPress REST APIクライアント（記事/固定ページ/メディア/カテゴリ）
│   ├── page_generator.py      # 固定ページ4種のAI生成モジュール
│   ├── setup_pages.py         # 固定ページ一括生成・WP自動登録スクリプト
│   ├── build_portal.py        # ローカル確認用ブログポータル（index.html）生成
│   └── template.html          # HTMLデザインテンプレート
├── prompts/
│   ├── analyze.txt            # 分析用システムプロンプト
│   ├── article.txt            # 記事生成用システムプロンプト（AdSense独自性基準含む）
│   ├── page_about.txt         # 「このサイトについて」プロンプト
│   ├── page_contact.txt       # 「お問い合わせ」プロンプト
│   ├── page_privacy.txt       # 「プライバシーポリシー」プロンプト
│   └── page_operator.txt      # 「運営者情報」プロンプト
└── output/                    # 生成物の出力先（自動作成）
    ├── index.html             # ローカルブログポータル（トップページ）
    ├── {video_id}_transcript.txt
    ├── {video_id}_analysis.json
    ├── {video_id}_article.md
    ├── {upload_date}_{sanitized_title}.html # (例: 2026-09-06_動画タイトル.html)
    ├── {video_id}_frames/     # スクリーンショット抽出画像
    ├── pages/                 # AdSense用固定ページ（about.html, privacy_policy.html等）
    └── processed_videos.txt   # 重複防止用処理済み履歴リスト
```


---

## 3. 技術スタック

| カテゴリ | ライブラリ/ツール | バージョン | 備考 |
|---|---|---|---|
| 言語 | Python | 3.11+ | |
| AI | google-generativeai | 0.8.6 | Gemini API |
| AIモデル | gemini-3.6-flash | latest | 無料枠あり |
| 字幕取得 | youtube-transcript-api | 1.2.4 | |
| 動画情報取得 | yt-dlp | 2026.8+ | APIキー不要 |
| 環境変数 | python-dotenv | 1.2.3 | |
| バリデーション | pydantic | 2.x | |
| MD→HTML変換 | markdown | 3.10+ | tables拡張使用 |
| フロントマター解析 | python-frontmatter | 1.3.0 | |
| HTTP通信 (WordPress) | requests | 2.34+ | WordPress REST API通信用 |

---

## 4. 環境変数（.env）

```env
# Gemini API Key
GEMINI_API_KEY=AIza...（Google AI Studioで取得）
ANALYSIS_MODEL=gemini-3.6-flash
ARTICLE_MODEL=gemini-3.6-flash

# YouTube Auto Fetch Settings
YOUTUBE_CHANNEL_URL=https://www.youtube.com/@channel/videos
MAX_BATCH_VIDEOS=10

# WordPress連携（セットアップ後に入力）
WP_SITE_URL=https://example.com
WP_USERNAME=username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
WP_DEFAULT_STATUS=draft

# サイト運営者情報（固定ページ生成時にAIへ渡す変数）
SITE_NAME=ブログ名
SITE_OPERATOR_NAME=運営者名
SITE_CONTACT_EMAIL=info@example.com
SITE_LAUNCH_DATE=2026-09-01
SITE_GENRE=ブログのジャンル
USES_GOOGLE_ANALYTICS=false
```

### APIキー取得方法
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にGoogleアカウントでログイン
2. 「APIキーを作成」をクリックしてキーを発行
3. `.env` の `GEMINI_API_KEY=` に貼り付ける

> ⚠️ **注意**: `.env` はGitリポジトリに含めないこと（`.gitignore` に追記すること）

---

## 5. 処理フローの詳細

### Step 1: YouTube情報取得（`src/youtube.py`）
- `yt-dlp` を使って動画メタデータを取得
- 取得情報: `video_id`, `title`, `channel_name`, `description`（**全文取得**）
- URLバリデーション: 通常URL・短縮URL・動画IDのみ に対応

### Step 2: 字幕取得（`src/transcript.py`）
- `youtube-transcript-api` を使用
- **優先順位**: 日本語字幕 → 他言語を日本語に翻訳
- v1.2.4以降はインスタンスを生成して使用: `ytt_api = YouTubeTranscriptApi(); ytt_api.list(video_id)`
- クリーニング: `TextFormatter` でプレーンテキスト化、連続空白を整理

### Step 3: AI分析（`src/analyzer.py`）
- **Gemini APIのJSONモード**（`response_mime_type: "application/json"`）を使用
- 概要欄（description）は**全文をAIに渡す**（500文字切り捨て禁止）
- 出力スキーマ（主要フィールド）:
  ```json
  {
    "動画テーマ": "...",
    "想定読者": "...",
    "読者の悩み": "...",
    "動画の主要な主張": "...",
    "重要ポイント": ["..."],
    "解決方法": ["..."],
    "具体例": ["..."],
    "商品・サービス": ["..."],
    "商品リンク": [
      {"名前": "...", "url": "https://...", "説明": "..."}
    ],
    "SEOキーワード": ["..."],
    "検索意図": "...",
    "記事タイトル候補": ["..."],
    "記事構成": [...],
    "FAQ候補": [...]
  }
  ```

### Step 4: 記事生成（`src/article_generator.py`）
- 分析JSONを受け取り、プロンプトに従ってMarkdown記事を生成
- 出力形式: YAMLフロントマター + Markdown本文
- **商品リンクがある場合**: `[商品名](URL)` のMarkdownリンク形式で記事に組み込む

### Step 5: ファイル保存（`src/output.py`）
- `output/` ディレクトリを自動作成
- ファイル名形式: `{video_id}_{type}.{ext}`

### Step 6: HTML生成（`src/html_generator.py`）
- `python-frontmatter` でYAMLを解析してメタデータを取得
- `markdown` ライブラリで本文をHTML化（`tables` 拡張有効）
- `src/template.html` テンプレートの `{{placeholder}}` に値を埋め込み

---

## 6. HTMLテンプレートのデザイン仕様

| 要素 | 仕様 |
|---|---|
| デザインテーマ | モダン・クリーンライトテーマ |
| グラスモーフィズム | `backdrop-filter: blur(12px)` + 半透明白背景 |
| 背景 | 青系グラデーション（`linear-gradient(135deg, #a1c4fd, #c2e9fb)`）|
| フォント | Google Fonts: Inter + Noto Sans JP |
| アニメーション | ページフェードイン、タグホバーアニメーション |
| レスポンシブ・スマホ最適化 | 768px未満でピル型チップ式横スクロールナビ、コンパクトヒーロー、1カラムカード、テーブル横スクロールに対応 |
| Google AdSense 広告枠 | ①トップ記事間（インフィード）、②サイドバー（300x250レクタングル）、③記事上部（レスポンシブ）、④記事下部（まとめ下） |

---

## 7. プロンプト設計方針

### `prompts/analyze.txt`（分析用）
- **役割**: SEOコンテンツ戦略家として動画を構造化分析
- **重要事項**: 概要欄URLを丁寧に確認し「商品リンク」フィールドに抽出する
- **出力形式**: JSON（`response_mime_type: application/json` で強制）

### `prompts/article.txt`（記事生成用）
- **役割**: 日本語SEOライターとして記事を執筆
- **重要事項**: 字幕の単純な言い換えを禁止。情報を整理し読者視点で再構成
- **リンク処理**: `商品リンク` にURLがある場合、`[商品名](URL)` で記事に組み込む
- **出力形式**: YAMLフロントマター + Markdown本文

---

## 8. エラーハンドリング一覧

| エラー種別 | 対処 |
|---|---|
| 不正なURL | `extract_video_id()` で `ValueError` を送出 |
| 動画が存在しない/非公開 | `yt_dlp.DownloadError` をキャッチして日本語メッセージ表示 |
| 字幕なし | `NoTranscriptFound` / `TranscriptsDisabled` をキャッチ |
| APIキー未設定 | `config.py` 読み込み時に `ValueError` |
| API認証失敗 | Gemini SDK の例外をキャッチして日本語メッセージ表示 |
| JSON解析失敗 | `json.JSONDecodeError` をキャッチして `ValueError` に変換 |
| 出力ディレクトリなし | `output.py` の `ensure_output_dir()` で自動作成 |

---

## 9. 将来の拡張計画

### Phase 1.5: AdSense対応固定ページ自動生成【✅実装済み】
- 詳細計画: `PLAN.md` 参照
- 成果物: `prompts/page_*.txt`, `src/page_generator.py`, `src/setup_pages.py`
- サイト情報から「このサイトについて」「お問い合わせ」「プライバシーポリシー」「運営者情報」をAI生成し、WordPressへ固定ページ自動登録。

### Phase 3: WordPress自動投稿【✅実装済み】
- 詳細計画: `PLAN.md` 参照
- 成果物: `src/wordpress.py`, `main.py [9/9]`
- WordPress REST API (Application Passwords) を介した記事下書き/公開投稿、アイキャッチ自動登録、カテゴリ・タグ自動マッピング。

### Phase 2: Amazon商品連携
```
分析JSONのキーワードから関連Amazon商品を検索
→ 記事の「商品紹介」セクションに自動挿入
→ Amazonアソシエイトリンクを付与
```

### Phase 4: Google Search Console連携
```
投稿後の検索順位・CTRを定期取得
→ AI分析でリライト指示を生成
→ 記事を自動リライト・再投稿
```

### Phase 5: 複数チャンネル・収益管理
```
YouTuberアカウント管理ダッシュボード
→ 動画リスト自動取得・バッチ記事生成
→ 収益管理と YouTuber への分配機能
```

---

## 10. 既知の注意事項

1. **`google.generativeai` の非推奨警告**: `FutureWarning` が表示されるが動作には影響しない。将来的に `google.genai` パッケージへの移行が必要。
2. **コンソール表示の文字化け**: Windows環境でPowerShellのデフォルトエンコーディングが原因。生成ファイル（UTF-8）は正常。
3. **字幕APIのバージョン対応**: `youtube-transcript-api` v1.2.4以降は `YouTubeTranscriptApi().list(video_id)` のインスタンスメソッドを使用（クラスメソッド `list_transcripts()` は廃止）。
