import os
import json
from config import OUTPUT_DIR

def ensure_output_dir():
    """出力先ディレクトリの存在確認・作成"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def save_transcript(video_id: str, transcript: str):
    """字幕テキストの保存"""
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, f"{video_id}_transcript.txt")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(transcript)
    return filepath

def save_analysis(video_id: str, analysis_data: dict):
    """分析結果(JSON)の保存"""
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, f"{video_id}_analysis.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    return filepath
    
def save_article(video_id: str, article_markdown: str):
    """生成された記事(Markdown)の保存"""
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, f"{video_id}_article.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(article_markdown)
    return filepath
