# WORKLOG.md — 作業ログ

> このプロジェクトに対して行った作業の履歴を記録します。  
> 他のアカウント・エージェントが引き継ぐ際はこのログを最初に読んでください。

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

