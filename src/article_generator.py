import json
import google.generativeai as genai
from config import ARTICLE_MODEL, ARTICLE_PROMPT_PATH

def generate_article(analysis_result: dict, video_info: dict, youtube_url: str) -> str:
    """
    分析結果のJSONを元に、SEO記事(Markdown)を生成する
    """
    
    # プロンプトの読み込み
    with open(ARTICLE_PROMPT_PATH, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
        
    model = genai.GenerativeModel(
        model_name=ARTICLE_MODEL,
        system_instruction=system_prompt,
        generation_config={"temperature": 0.7}
    )
        
    # 分析結果を文字列化
    analysis_json_str = json.dumps(analysis_result, ensure_ascii=False, indent=2)
    
    # メタデータもユーザープロンプトとして渡す
    user_content = f"""
【元動画情報】
URL: {youtube_url}
タイトル: {video_info.get('title')}
チャンネル名: {video_info.get('channel_name')}

【分析データ(JSON)】
{analysis_json_str}

上記の分析データを元に、指示に従ってMarkdown形式で記事を作成してください。フロントマターも含めてください。
"""

    response = model.generate_content(user_content)
    
    text = response.text.strip()
    # 先頭や末尾の ```yaml, ```markdown, ``` を除去
    import re
    text = re.sub(r'^```(?:yaml|markdown)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)
    text = text.strip()
    
    return text

