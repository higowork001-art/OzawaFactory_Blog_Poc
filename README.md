# YouTube → AI SEO記事生成システム MVP (Gemini版)

YouTubeのURLを入力すると、動画の字幕を取得し、AI（Google Gemini API）を用いてSEO向けブログ記事を自動生成するシステムです。

## 特徴
- YouTubeからのメタデータと字幕の自動取得
- 字幕内容を元にしたGemini APIによる構造化分析
- 分析結果に基づく読みやすいSEO記事(Markdown)の自動生成
- 100万トークン対応の `gemini-1.5-flash` モデルによる長時間の動画の一括処理

## 必須要件
- Python 3.11+
- Google Gemini API Key (Google AI Studioから無料で取得可能)

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
   `.env` ファイルを編集し、自身のGemini APIキーを設定します。
   ```text
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## 実行方法

1. メインスクリプトを実行します。
   ```bash
   python main.py
   ```

2. プロンプトに従って、YouTubeのURLを入力します。
   ```text
   YouTube URLを入力してください: https://www.youtube.com/watch?v=XXXXXXXXXXX
   ```

3. 処理の進捗がコンソールに表示され、完了すると `output/` ディレクトリに以下のファイルが生成されます。
   - `{video_id}_transcript.txt` : 字幕のクリーニング済みテキスト
   - `{video_id}_analysis.json` : AIによる分析結果のJSON
   - `{video_id}_article.md` : 最終的なSEO記事のMarkdown
