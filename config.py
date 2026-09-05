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

# 定数設定
OUTPUT_DIR = "output"
PROMPTS_DIR = "prompts"

ANALYZE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "analyze.txt")
ARTICLE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "article.txt")
