# WORKLOG.md — 作業ログ

> このプロジェクトに対して行った作業の履歴を記録します。  
> 他のアカウント・エージェントが引き継ぐ際はこのログを最初に読んでください。

> [!IMPORTANT]
> **引き継ぎ・作業記録の運用ルール**  
> 異なるAIモデル・エージェント・開発アカウント間でも作業を円滑に引き継げるよう、**コード変更・設定変更・機能追加の実行ごとに、必ず本ログ（`WORKLOG.md`）および仕様書（`SPEC.md`）へ作業内容と検証結果を更新記録してください。**

---


## セッション #1 — 2026-09-04

### 担当者
- アカウント: higowork.001@gmail.com
- 作業環境: Windows / PowerShell / Python 3.14

---

### 作業内容

#### ✅ MVP初回実装

**目標**: YouTube URLを入力すると `output/` にSEO記事が生成されるシステムをゼロから構築する。

**実装したファイル:**

| ファイル | 内容 |
|---|---|
| `requirements.txt` | 依存パッケージ定義 |
| `.env` | 環境変数テンプレート |
| `README.md` | セットアップ手順 |
| `config.py` | 設定の一元管理 |
| `main.py` | メインフロー制御（6→7ステップ） |
| `src/youtube.py` | yt-dlpによるメタデータ取得 |
| `src/transcript.py` | 字幕取得・クリーニング |
| `src/analyzer.py` | Gemini APIによるJSON分析 |
| `src/article_generator.py` | Gemini APIによるMarkdown記事生成 |
| `src/output.py` | ファイル保存処理 |
| `src/html_generator.py` | HTML変換・保存 |
| `src/template.html` | プレミアムHTMLデザインテンプレート |
| `prompts/analyze.txt` | 分析用システムプロンプト |
| `prompts/article.txt` | 記事生成用システムプロンプト |

---

#### ✅ OpenAI → Gemini API への移行

**理由**: コスト削減（Gemini APIは無料枠あり）とコンテキストウィンドウの大幅拡大（100万トークン）。

**変更点:**
- `openai` / `tiktoken` パッケージを削除、`google-generativeai` に置換
- チャンク分割処理を完全削除（Gemini 1.5+ は長文を一括処理可能）
- `.env` の `OPENAI_API_KEY` → `GEMINI_API_KEY` に変更
- デフォルトモデル: `gemini-1.5-flash` → `gemini-3.6-flash`（利用可能モデルを確認して変更）

---

#### 🐛 バグ修正 #1: youtube-transcript-api のAPIバージョン対応

**エラー内容:**
```
type object 'YouTubeTranscriptApi' has no attribute 'list_transcripts'
```

**原因**: `youtube-transcript-api` v1.2.4 から `list_transcripts()` クラスメソッドが廃止され、インスタンスメソッド `list()` に変更された。

**修正内容** (`src/transcript.py`):
```python
# 修正前（廃止）
transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

# 修正後
ytt_api = YouTubeTranscriptApi()
transcript_list = ytt_api.list(video_id)
```

---

#### 🐛 バグ修正 #2: Gemini APIモデル名の不一致

**エラー内容:**
```
404 models/gemini-1.5-flash is not found for API version v1beta
```

**原因**: 環境で `gemini-1.5-flash` が利用不可。`genai.list_models()` で利用可能なモデル一覧を確認して対応。

**修正内容**: `.env` および `config.py` のデフォルトモデルを `gemini-3.6-flash` に変更。

**利用可能なモデル確認コマンド:**
```bash
python -c "import os; from dotenv import load_dotenv; import google.generativeai as genai; load_dotenv(); genai.configure(api_key=os.getenv('GEMINI_API_KEY')); print([m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods])"
```

---

#### ✅ HTMLプレビュー機能の追加

**目標**: 生成されたMarkdown記事を、見栄えのいいHTML画面として出力する。

**実装内容:**
- `src/html_generator.py`: `python-frontmatter` でYAML解析 + `markdown` ライブラリでHTML変換
- `src/template.html`: グラスモーフィズムデザイン（Inter + Noto Sans JP / 青系グラデーション背景）
- `main.py` に `[7/7] HTMLプレビューを生成しています...` ステップを追加
- `requirements.txt` に `markdown`, `python-frontmatter` を追加

---

#### ✅ 概要欄商品リンク抽出機能の追加

**背景**: 生成記事に商品名が表示されているが、概要欄のリンクURLが含まれていなかった。

**根本原因**: `analyzer.py` で `description[:500]` と500文字で切り捨てていたため、概要欄後半のURLが失われていた。

**修正内容:**

1. `src/analyzer.py`: `description[:500]` の切り捨てを撤廃 → 全文をAIに渡す
2. `prompts/analyze.txt`: 概要欄URLを `"商品リンク"` フィールドとして抽出するよう明示的に指示
3. `prompts/article.txt`: `商品リンク` フィールドのURLを `[商品名](URL)` 形式でMarkdownリンクとして記事に組み込む指示を追加

**結果**: 概要欄から22件のリンク（キッチンクラフト公式・Instagram・PayPayフリマ・楽天ROOM・Amazonリンク等）をすべて抽出し、記事にクリッカブルなリンクとして反映。

---

#### ✅ 動作確認済みのテスト

**テスト動画**: `https://www.youtube.com/watch?v=OaLbGnNo37M`  
**動画タイトル**: ステンレス鍋フル活用！ほったらかしで５品のおつまみ作り  
**チャンネル**: ステンレス鍋のための料理教室!大澤チャンネル

**確認済みの出力:**

```
output/
├── OaLbGnNo37M_transcript.txt   ✅ 字幕テキスト
├── OaLbGnNo37M_analysis.json    ✅ 構造化分析JSON（商品リンク22件含む）
├── OaLbGnNo37M_article.md       ✅ YAMLフロントマター付きMarkdown記事
└── OaLbGnNo37M_article.html     ✅ グラスモーフィズムデザインHTMLプレビュー
```

---

### 未解決の課題・TODO

- [ ] `google.generativeai` の非推奨警告（`FutureWarning`）への対応 → `google.genai` パッケージへの移行
- [ ] コンソール出力の文字化け（Windows PowerShellのエンコーディング問題）の修正
- [ ] Phase 2: Amazon商品連携の実装
- [ ] Phase 3: WordPress自動投稿の実装

---

### 引き継ぎ時の注意事項

1. **`.env` ファイルのAPIキー確認が必須** — `GEMINI_API_KEY` に有効なGemini APIキーを設定すること
2. **モデル名の確認** — Gemini APIのモデル提供状況は変動するため、エラー時は上記の確認コマンドで利用可能なモデルを確認し `.env` の `ANALYSIS_MODEL` / `ARTICLE_MODEL` を更新すること
3. **`youtube-transcript-api` のバージョン依存** — 字幕APIはバージョンによってAPIインターフェースが変わる。`pip show youtube-transcript-api` でバージョンを確認し、v1.2.4以降は `YouTubeTranscriptApi().list()` を使うこと
4. **出力ファイルの上書き** — 同じ `video_id` で再実行すると `output/` の該当ファイルは上書きされる

---

## セッション #2 — 2026-09-04

### 担当者
- 作業環境: Windows / PowerShell / Python 3.14
- AI: Antigravity IDE (Claude Sonnet 4.6 Thinking)

---

### 作業内容

#### ✅ YouTube動画スクリーンショット自動抽出・HTML埋め込み機能の追加

**目標**: 生成HTMLに動画関連の画像キャプチャを自動で埋め込み、視覚的に豊かな記事を生成する。

**実装内容:**

| ファイル | 変更内容 |
|---|---|
| `src/screenshot.py` | 【新規】yt-dlp + FFmpegによるフレーム抽出モジュール |
| `src/transcript.py` | `get_transcript_with_timestamps()` を追加（タイムスタンプ付き字幕取得） |
| `src/analyzer.py` | `timed_transcript` パラメータを追加・AIに渡す処理を実装 |
| `src/html_generator.py` | ヒーロー画像・セクション画像埋め込みロジックを追加 |
| `src/template.html` | `.hero-image`, `.scene-capture`, `.scene-caption` スタイルを追加 |
| `prompts/analyze.txt` | 「重要シーン」フィールド（秒数・説明）の抽出指示を追加 |
| `main.py` | 7→8ステップに拡張（スクリーンショット抽出ステップを追加） |

**処理フロー（追加部分）:**

```
字幕取得（既存）
  ↓ [追加] タイムスタンプ付き字幕も同時取得
AI分析（既存）
  ↓ [改良] タイムスタンプ付き字幕をAIに渡し「重要シーン」を選定
      → 分析JSONに "重要シーン": [{"秒数": 45, "説明": "..."}, ...] が追加
フレーム抽出 [新規ステップ]
  ↓ yt-dlp でストリームURL取得（動画本体はダウンロードしない）
  ↓ FFmpeg で指定秒数のフレームを抽出
  ↓ output/{video_id}_frames/ に保存
HTML生成（改良）
  ↓ ヒーロー画像: 最初のフレーム or YouTubeサムネイルURL
  ↓ セクション画像: 各h2の直後に対応シーン画像を挿入
```

**技術的ポイント:**

- **動画ダウンロード不要**: `yt-dlp --get-url` でストリームURLを取得し、FFmpegが直接ストリームに接続してフレームのみ抽出。ローカルに動画ファイルは残らない。
- **フォールバック機能**: フレーム抽出失敗時はYouTubeサムネイルURL（`img.youtube.com/vi/{id}/maxresdefault.jpg`）をそのまま使用するため、必ず画像が表示される。
- **FFmpegパス自動検出**: `_find_ffmpeg_in_winget()` がWingetインストール先を動的に検索するため、PATHに追加されていなくても動作する。

**インストール済みツール:**
- FFmpeg v9.0.1 (winget: Gyan.FFmpeg)

**出力追加:**
```
output/
└── {video_id}_frames/
    ├── frame_00030s.jpg
    ├── frame_00120s.jpg
    └── ...（重要シーンのフレーム画像）
```

---

## セッション #2 — 2026-09-06

### 担当者
- アカウント: AI Pair Programmer (Gemini 3.6 Flash / Antigravity Agent)
- 作業環境: Windows / PowerShell / Python 3.14

---

### 作業内容

#### ✅ YouTubeチャンネルからの最新動画（10件）自動一括ブログ化 ＆ 重複防止システムの実装

**目標**: 
YouTubeチャンネルURL（例: `https://www.youtube.com/@isamumumu1/videos`）から最新動画を最大10件自動抽出して、重複なしで順次自動ブログ記事化する。

**変更・追加したファイル:**

| ファイル | 内容 |
|---|---|
| `.env` | `YOUTUBE_CHANNEL_URL`, `MAX_BATCH_VIDEOS` 設定項目を追加 |
| `config.py` | `.env` から設定項目をロードし、`PROCESSED_LIST_PATH` を定義 |
| `src/youtube.py` | `get_channel_video_urls()` を追加。`yt-dlp` の `extract_flat` 機能でチャンネルから最新動画一覧を取得 |
| `src/tracker.py` | **【新規作成】** 重複防止トラッカー。`load_processed_video_ids()` で既処理リストを読み込み、`mark_video_as_processed()` で `output/processed_videos.txt` にID・日時・タイトルを記録 |
| `main.py` | 単一処理 `process_single_video()` と一括処理 `run_batch_mode()` へリファクタリング。空エンターで一括バッチ処理を実行するメニューUIを実装 |
| `README.md` | セットアップ方法・一括処理手順・重複防止履歴ファイルを追記 |
| `SPEC.md` | システム仕様を `v1.2.0` へ更新。引き継ぎルールおよび一括処理/重複防止の仕様を追加 |
| `WORKLOG.md` | 本作業ログセッションおよびAI引き継ぎルール注記を追加 |

**動作検証結果:**
- `yt-dlp` で `https://www.youtube.com/@isamumumu1/videos` から動画メタデータが正常抽出されることを確認。
- `output/processed_videos.txt` の読み書きテストにより、処理済み動画IDの判定および二重処理スキップが機能することを確認。

---

---

## セッション #3 — 2026-09-08

### 担当者
- アカウント: AI Pair Programmer (Gemini 3.6 Flash / Antigravity Agent)
- 作業環境: Windows / PowerShell / Python 3.14

---

### 作業内容

#### ✅ HTMLファイル名の「動画投稿日＋タイトル」への命名規則変更
**ユーザー要件**: 生成されるHTMLファイル名を `動画作成日付 + タイトル` の形式にする。

**実装内容:**
- `src/youtube.py`: `get_video_info()` で動画投稿日 `upload_date`（`YYYYMMDD` 形式）を取得・返却するよう拡張。
- `src/html_generator.py`:
  - ファイル名用サニタイズ関数 `sanitize_filename()` を実装（OS禁忌文字 `\ / : * ? " < > |` の置換と文字数制限）。
  - `generate_html_preview()` に `upload_date` と `title_text` パラメータを追加。
  - 出力ファイル名を `YYYY-MM-DD_{sanitized_title}.html` のフォーマットに変更。
- `main.py`: `generate_html_preview` の呼び出し時に `upload_date` と `title` を引き渡すよう改修。

#### ✅ 最新YouTube動画3件の再自動ブログ化
- `processed_videos.txt` クリア後の状態から、チャンネル最新の未処理動画3件を一括ブログ化実行。


---

## セッション #4 — 2026-09-08

### 担当者
- アカウント: AI Pair Programmer (Gemini 3.6 Flash / Antigravity Agent)
- 作業環境: Windows / PowerShell / Python 3.14

---

### 作業内容

#### 🐛 バグ修正 ＆ 表示最適化: 「無題のSEO記事」タイトル問題 ＆ Markdownコードブロック漏れ修正

**背景・不具合内容:**
1. HTML生成時に H1 / title が「無題のSEO記事」と表示されてしまう現象。
2. 生成されたHTMLに ` ```yaml ` などのコードブロック記法や、YAMLフロントマターの一部 (`title: ...`, `description: ...`) がテキストとして直出し・埋め込まれてしまう現象。

**原因:**
- Gemini APIがMarkdown出力時に、レスポンス全体を ```yaml ... ``` というコードブロック記法で囲んで出力していた。
- `python-frontmatter` が ` ```yaml ` で始まるファイルをYAMLフロントマターとして読み込めずパース失敗し、デフォルトの "無題のSEO記事" が設定されていた。
- パース失敗したため `post.content` に YAMLテキストが含まれてしまい、MarkdownコンバーターでそのままコードブロックとしてHTML化されていた。

**修正内容:**

| ファイル | 変更内容 |
|---|---|
| `prompts/article.txt` | 出力フォーマット指示から ```yaml のコードブロック囲みを排除し、ファイルの先頭を直接 `---` から始めるよう厳密指示を追加 |
| `src/article_generator.py` | APIレスポンスから ` ```yaml ` や ` ```markdown ` や ` ``` ` を自動除去するクレンジング処理 (`re.sub`) を追加 |
| `src/html_generator.py` | 読み込み時のクレンジング関数 `clean_markdown_text()` を追加し、フロントマターの安全な解析を実施。H1/title に HTMLファイル名（拡張子なし）を適用するよう改修 |
| `scratch/rebuild_html.py` | 既存の `.md` および `.html` 生成物をすべてクレンジング・再生成 |

**検証結果:**
- `output/` 配下の全5件のMarkdown・HTMLプレビューが再クレンジングされ、余計なコードブロック・フロントマター直出しが完全消失。
- H1および `<title>` タグに HTMLファイル名（`2026-08-21_圧倒的に美味しい！バター醤油とうもろこしおこわ` 等）が正しく適用されることを確認。

---

## セッション #5 — 2026-09-08

### 担当者
- アカウント: AI Pair Programmer (Gemini / Antigravity Agent)
- 作業環境: Windows / PowerShell / Python 3.14

---

### 作業内容

#### ✅ AdSense対応（固定ページ自動生成）＆ WordPress REST API 自動連携の実装 (Phase 1.5 + Phase 3)

**背景・目的**:
生成された記事をローカル生成のみで終わらせず、独自ドメイン＋WordPressで一般公開し、Google AdSenseの審査に通せる状態（体系的なサイト構造・必須固定ページ整備・独自性向上）をワンストップで実現する。

**変更・追加したファイル:**

| ファイル | 内容 |
|---|---|
| `PLAN.md` | 【新規】ユーザー提示の AdSense対応 & WordPress連携 拡張計画書をプロジェクトルートに保存 |
| `prompts/page_about.txt` | 【新規】「このサイトについて」生成用プロンプト（800〜1200字、一人称執筆） |
| `prompts/page_contact.txt` | 【新規】「お問い合わせ」リード文生成用プロンプト（Contact Form 7連携想定） |
| `prompts/page_privacy.txt` | 【新規】「プライバシーポリシー」生成用プロンプト（AdSense審査必須：Cookie、AdSense明記、オプトアウトリンク、Analytics対応） |
| `prompts/page_operator.txt` | 【新規】「運営者情報」生成用プロンプト（定義テーブル＋自己紹介） |
| `src/page_generator.py` | 【新規】環境変数（`.env`）からサイト情報を動的置換し、Gemini APIで固定ページMarkdownを生成・`output/pages/` に保存するモジュール |
| `src/wordpress.py` | 【新規】WordPress REST API (Application Passwords Basic認証) クライアント。記事投稿、固定ページ投稿・更新、メディア（アイキャッチ）アップロード、カテゴリ・タグ自動マッピング・生成、接続テスト |
| `src/setup_pages.py` | 【新規】固定ページ4種を一括生成し、WordPressへ固定ページとして登録・公開するCLIスクリプト（`--regenerate` オプション付き） |
| `config.py` | WordPress接続設定、サイト運営者情報、固定ページプロンプトパス、カテゴリマッピング（`CATEGORY_MAP`）を追加 |
| `.env` | WordPress接続情報およびサイト運営者情報のプレースホルダーを追加 |
| `requirements.txt` | `requests`（WordPress REST API通信用）を追加 |
| `prompts/article.txt` | AdSense審査基準に合わせた品質担保指示（独自視点・アドバイス追加、運営者一言コメント、独自順序での再構成）を追記 |
| `src/build_portal.py` | 【新規】ローカル確認用のブログポータル（`output/index.html`）および固定ページHTMLを自動生成するモジュール |
| `SPEC.md` | バージョン 1.3.0 へ更新。新規モジュール構成、環境変数、Phase 1.5 / Phase 3 実装済み反映 |
| `README.md` | WordPress連携の設定手順、固定ページの初期セットアップコマンド、機能一覧を更新 |

**検証結果:**
1. **固定ページAI生成テスト**:
   - `page_generator.py` を実行し、Gemini APIを用いて4つの固定ページ（`about.md`, `contact.md`, `privacy_policy.md`, `operator_info.md`）が `output/pages/` 配下に高精度で生成されることを確認。
   - プライバシーポリシーにおいて、AdSense審査要件（Cookie利用、広告オプトアウトリンク、免責事項、問い合わせ先等）が網羅されていることを確認。
2. **WordPressクライアント接続テスト**:
   - `WordPressClient` において、接続情報未設定時に安全なフォールバックと分かりやすいガイダンスメッセージが出力されることを確認。
   - `src/setup_pages.py` の単体CLI実行において、WP未設定時にローカルMarkdown保存のみ完了しエラーなく終了することを確認。
3. **ローカルブログサイト全体の確認（Chrome）**:
   - `build_portal.py` により、トップページ [`output/index.html`](file:///c:/AntiGravity/AIYouTublog/output/index.html) と固定ページ4種のHTMLを生成。
   - グローバルナビ（ホーム・このサイトについて・お問い合わせ・プライバシーポリシー・運営者情報）、記事カード一覧、サイドバー（プロフィール・カテゴリ・AdSense審査対策状況）、フッターが綺麗に連動し、ローカルのChromeブラウザからサイト全体の導線・デザインを完全確認できる状態を構築。
4. **Windowsコンソール文字化け対策**:
   - `page_generator.py`, `setup_pages.py`, `build_portal.py` に `sys.stdout.reconfigure(encoding='utf-8')` を導入し、日本語ログの正常出力を担保。
5. **🐛 カテゴリ絞り込み機能の修正・実装**:
   - 不具合: サイドバーのカテゴリリンクが静的リンク（`href="#"`）になっており、クリックしても該当記事に絞り込まれなかった点、および「フライパン」の文字優先により耐久実験記事が「レビュー・検証」ではなく「調理器具」に誤分類されていた点を修正。
   - 修正: `determine_category()` で「実験・検証・レビュー」を最優先判定するように改善。
   - 機能追加: 記事上部へのカテゴリフィルタータブ（すべて/レシピ/調理器具/レビュー検証）、サイドバーリンク、記事カードのバッジクリックによる即時絞り込みJavaScriptを実装。URLハッシュ（`#category=...`）にも完全同期。
6. **🎨 サイドバー＆バナーのUI調整・公式ショップ導線追加**:
   - ヘッダーおよびサイドバーから「AdSense必須」「サイト審査対策状況」の文言・ウィジェットを完全削除。
   - サイト情報枠のすぐ下段に、別枠として「🛍️ オリジナル商品」枠を新設（大澤チャンネルのオリジナル商品サイト: `https://ozawachannnel.stores.jp` への外部リンクボタンを配置）。
