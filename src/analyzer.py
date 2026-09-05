import json
import google.generativeai as genai
from config import ANALYSIS_MODEL, ANALYZE_PROMPT_PATH

def analyze_transcript(transcript: str, video_info: dict, timed_transcript: list = None) -> dict:
    """字幕を分析し、JSON形式の構造化データを返す。
    
    timed_transcript: タイムスタンプ付き字幕リスト（get_transcript_with_timestamps()の結果）
                      渡した場合、AIが「重要シーン」をタイムスタンプで選定する。
    """
    
    # プロンプトの読み込み
    with open(ANALYZE_PROMPT_PATH, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
        
    model = genai.GenerativeModel(
        model_name=ANALYSIS_MODEL,
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json", "temperature": 0.5}
    )

    # タイムスタンプ付き字幕データのフォーマット（最大400件に絞り、AIへの負荷を抑制）
    timed_section = ""
    if timed_transcript:
        trimmed = timed_transcript[:400]
        lines = [f"[{int(e['start'])}s] {e['text']}" for e in trimmed if e.get('text')]
        timed_section = "\n\n【タイムスタンプ付き字幕（重要シーン選定に使用）】\n" + "\n".join(lines)

    # メタデータを付与（概要欄はURLリンク含め全文を渡す）
    user_content = f"""
【動画情報】
タイトル: {video_info.get('title')}
チャンネル: {video_info.get('channel_name')}
概要（全文）: {video_info.get('description')}

【字幕データ】
{transcript}{timed_section}
"""

    response = model.generate_content(user_content)
    
    result_text = response.text
    try:
        result_json = json.loads(result_text)
        return result_json
    except json.JSONDecodeError:
        raise ValueError("AIからの応答をJSONとして解析できませんでした。")
