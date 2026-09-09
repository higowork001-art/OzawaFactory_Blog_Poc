import os
from dotenv import load_dotenv
import google.generativeai as genai

# .envファイルの読み込み
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEYが環境変数(.env)に設定されていません。")

# GeminiのAPIキーを設定
genai.configure(api_key=GEMINI_API_KEY)

# 使用するモデルの設定（デフォルトはgemini-3.6-flash）
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gemini-3.6-flash")
ARTICLE_MODEL = os.getenv("ARTICLE_MODEL", "gemini-3.6-flash")

# YouTubeチャンネル・一括処理設定
YOUTUBE_CHANNEL_URL = os.getenv("YOUTUBE_CHANNEL_URL", "")
MAX_BATCH_VIDEOS = int(os.getenv("MAX_BATCH_VIDEOS", "10"))
BATCH_DELAY_SECONDS = int(os.getenv("BATCH_DELAY_SECONDS", "10"))  # 一括処理時の動画間クールダウン秒数

# 定数設定
OUTPUT_DIR = "output"
PROMPTS_DIR = "prompts"

PROCESSED_LIST_PATH = os.path.join(OUTPUT_DIR, "processed_videos.txt")
ANALYZE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "analyze.txt")
ARTICLE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "article.txt")

# WordPress連携設定
WP_SITE_URL = os.getenv("WP_SITE_URL", "")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
WP_DEFAULT_STATUS = os.getenv("WP_DEFAULT_STATUS", "draft")

# サイト運営者情報（固定ページ生成時にAIへ渡す変数）
SITE_NAME = os.getenv("SITE_NAME", "").strip()
SITE_OPERATOR_NAME = os.getenv("SITE_OPERATOR_NAME", "").strip()
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "").strip()
SITE_LAUNCH_DATE = os.getenv("SITE_LAUNCH_DATE", "").strip()
SITE_GENRE = os.getenv("SITE_GENRE", "").strip()
USES_GOOGLE_ANALYTICS = os.getenv("USES_GOOGLE_ANALYTICS", "false").strip()

# 固定ページ用プロンプトパス
PAGE_ABOUT_PROMPT_PATH = os.path.join(PROMPTS_DIR, "page_about.txt")
PAGE_CONTACT_PROMPT_PATH = os.path.join(PROMPTS_DIR, "page_contact.txt")
PAGE_PRIVACY_PROMPT_PATH = os.path.join(PROMPTS_DIR, "page_privacy.txt")
PAGE_OPERATOR_PROMPT_PATH = os.path.join(PROMPTS_DIR, "page_operator.txt")

# カテゴリマッピング（AI分析の「動画テーマ」→ WordPressカテゴリ）
CATEGORY_MAP = {
    "料理": "レシピ・料理",
    "レシピ": "レシピ・料理",
    "調理器具": "レシピ・料理",
    "ガジェット": "ガジェット・テクノロジー",
    "レビュー": "レビュー",
}
DEFAULT_CATEGORY = "未分類"

