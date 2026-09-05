import yt_dlp
import re

def extract_video_id(url: str) -> str:
    """YouTube URLから動画IDを抽出する"""
    # 短縮URL(youtu.be)や通常のURL(youtube.com/watch?v=)などに対応
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    # URL自体が11文字のIDである場合へのフォールバック
    if len(url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", url):
        return url
        
    raise ValueError("YouTube URLから動画IDを取得できませんでした。不正なURLの可能性があります。")

def get_video_info(url: str) -> dict:
    """yt-dlpを使用して動画のメタデータを取得する"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True, # 動画自体はダウンロードしない
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("動画情報の取得に失敗しました。")
                
            return {
                "video_id": info.get("id"),
                "title": info.get("title"),
                "channel_name": info.get("uploader"),
                "description": info.get("description", "")
            }
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"動画情報が取得できません。URLが間違っているか、動画が存在しないか非公開の可能性があります。詳細: {str(e)}")
