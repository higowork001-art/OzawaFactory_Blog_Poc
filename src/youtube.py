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
                "title": info.get("title", ""),
                "upload_date": info.get("upload_date", ""),
                "channel_name": info.get("uploader", ""),
                "description": info.get("description", "")
            }
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"動画情報が取得できません。URLが間違っているか、動画が存在しないか非公開の可能性があります。詳細: {str(e)}")



def get_channel_video_urls(channel_url: str, limit: int = 30) -> list:
    """
    YouTubeチャンネルまたは再生リストから最新動画のURL・メタデータリストを取得する。

    Args:
        channel_url: チャンネルまたは動画一覧のURL
        limit: 取得する最大動画数

    Returns:
        [{"video_id": "...", "url": "...", "title": "..."}, ...]
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlistend': limit,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if not info:
                raise ValueError("チャンネル情報の取得に失敗しました。")

            entries = info.get("entries", [])
            if not entries and "id" in info:
                entries = [info]

            video_list = []
            for entry in entries:
                if not entry:
                    continue
                v_id = entry.get("id")
                title = entry.get("title", "")
                url = entry.get("url") or f"https://www.youtube.com/watch?v={v_id}"
                if v_id:
                    video_list.append({
                        "video_id": v_id,
                        "url": url,
                        "title": title,
                    })
            return video_list
    except Exception as e:
        raise ValueError(f"チャンネルからの動画一覧取得に失敗しました: {str(e)}")

