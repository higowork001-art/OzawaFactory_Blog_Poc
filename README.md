# YouTube → AI SEO記事生成システム MVP (Gemini版)

YouTubeのURLを入力すると、動画の字幕を取得し、AI（Google Gemini API）を用いてSEO向けブログ記事を自動生成するシステムです。

## 特徴
- YouTubeからのメタデータと字幕の自動取得
- **YouTubeチャンネルからの最新動画（最大10件）の一括自動取得＆ブログ化**
- **重複処理防止機能**（一度作成した動画は `output/processed_videos.txt` に記録してスキップ）
- 字幕内容を元にしたGemini APIによる構造化分析
- 分析結果に基づく読みやすいSEO記事(Markdown)の自動生成（AdSense独自性基準対応）
- リッチなグラスモーフィズムデザインのプレビューHTML自動生成
- **WordPress REST API 自動連携**（記事自動投稿・アイキャッチ画像アップロード・カテゴリ自動分類）
- **AdSense必須固定ページ4種自動生成**（このサイトについて・お問い合わせ・プライバシーポリシー・運営者情報）

## 必須要件
- Python 3.11+
- Google Gemini API Key (Google AI Studioから無料で取得可能)
- (任意) WordPressサイト (REST API / Application Passwords)

## セットアップ手順

1. **リポジトリの展開**
   ファイルを任意のディレクトリに配置します。

2. **仮想環境の作成と有効化 (推奨)**
   ```bash
   python -m venv venv
   # Windowsの場合
   venv\Scripts\activate
   # macOS/Linuxの場合
   source venv/bin/activate
   ```

3. **依存パッケージのインストール**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数の設定**
   `.env` ファイルを編集し、Gemini APIキー、チャンネルURL、WordPress接続情報、サイト運営者情報を設定します。
   ```text
   # Gemini API
   GEMINI_API_KEY=your_actual_api_key_here

   # YouTubeチャンネル自動取得
   YOUTUBE_CHANNEL_URL=https://www.youtube.com/@channel_name/videos
   MAX_BATCH_VIDEOS=3

   # WordPress連携（未設定時はローカル生成のみ実行）
   WP_SITE_URL=https://your-site.com
   WP_USERNAME=your_username
   WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
   WP_DEFAULT_STATUS=draft

   # サイト情報（固定ページAI生成用）
   SITE_NAME=ブログタイトル
   SITE_OPERATOR_NAME=運営者名
   SITE_CONTACT_EMAIL=info@example.com
   SITE_LAUNCH_DATE=2026-09-01
   SITE_GENRE=料理レシピ・男飯
   USES_GOOGLE_ANALYTICS=false
   ```

## 実行方法

### 1. 記事の自動生成（＆WordPress投稿）
```bash
python main.py
```
- **一括自動ブログ化**: URLを入力せずそのまま `Enter` キーを押すと、未処理の最新動画を一括生成します。
- **単一動画の処理**: YouTube動画URLを入力すると、その動画1本のみを処理します。
- ※ `WP_SITE_URL` が設定されている場合は、記事生成後にWordPressへ下書き投稿（およびアイキャッチ設定）が自動実行されます。未設定の場合はローカルファイル生成のみで完了します。

### 2. AdSense用固定ページの初回セットアップ
```bash
python -m src.setup_pages
# 再生成したい場合は --regenerate を付与
python -m src.setup_pages --regenerate
```
- 「このサイトについて」「お問い合わせ」「プライバシーポリシー」「運営者情報」の4ページを一括生成し、`output/pages/` にMarkdownを保存した上でWordPressに固定ページとして公開（または更新）します。
- WordPressの管理画面から、グローバルメニューやフッターメニューにこれらの固定ページを追加してください。

## 生成ファイル構成
- `{video_id}_transcript.txt` : 字幕のクリーニング済みテキスト
- `{video_id}_analysis.json` : AIによる分析結果のJSON
- `{video_id}_article.md` : 最終的なSEO記事のMarkdown
- `{upload_date}_{sanitized_title}.html` : プレビューHTML
- `output/pages/` : 固定ページのMarkdown（about.md, contact.md, privacy_policy.md, operator_info.md）
- `processed_videos.txt` : 処理済み動画IDの履歴記録

