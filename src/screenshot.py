"""
src/screenshot.py
YouTube動画からフレームを抽出するモジュール。
yt-dlp で動画を部分ダウンロードし、FFmpeg でフレームを切り出す。
"""
import os
import subprocess
import shutil
import sys
from config import OUTPUT_DIR


import requests

def get_thumbnail_url(video_id: str) -> str:
    """
    YouTubeサムネイルのURLを返す（ダウンロード不要）。
    maxresdefault → hqdefault の順にフォールバックする。
    """
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


def download_thumbnail(video_id: str) -> str:
    """
    YouTube動画の公式サムネイル画像をダウンロードしてローカルに保存する。
    maxresdefault.jpg を試し、取得できない場合は hqdefault.jpg を取得する。
    
    Returns:
        保存したサムネイル画像のローカルファイルパス（失敗時はサムネイルURL）
    """
    out_path = os.path.join(OUTPUT_DIR, f"{video_id}_thumb.jpg")
    
    # 既にダウンロード済みならそのパスを返す
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return out_path

    urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]

    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            # YouTubeは存在しないmaxresdefaultに対してステータス404または小さいプレースホルダーを返すことがある
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                print(f"  [screenshot] YouTubeサムネイルをダウンロード完了: {os.path.basename(out_path)} ({len(resp.content)} bytes)")
                return out_path
        except Exception as e:
            continue

    # ダウンロード失敗時のフォールバックURL
    return get_thumbnail_url(video_id)


def _get_ffmpeg_path() -> str:
    """ffmpegの実行パスを返す。PATHになければWingetの既定インストール先を探す。"""
    # まずPATHから探す
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    # winget インストール先の候補
    candidates = [
        r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "ffmpeg"  # 最終フォールバック（エラーになる可能性あり）


def _find_ffmpeg_in_winget() -> str:
    """wingetパッケージディレクトリからffmpegを動的に探す。"""
    base = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages")
    if not os.path.isdir(base):
        return None
    for pkg in os.listdir(base):
        if "Gyan.FFmpeg" in pkg or "ffmpeg" in pkg.lower():
            pkg_path = os.path.join(base, pkg)
            for root, dirs, files in os.walk(pkg_path):
                if "ffmpeg.exe" in files:
                    return os.path.join(root, "ffmpeg.exe")
    return None


def extract_frames(
    video_url: str,
    video_id: str,
    timestamps_sec: list[float],
    quality: int = 2,
) -> dict[float, str]:
    """
    指定されたタイムスタンプ（秒数）でYouTube動画のフレームを抽出する。

    Args:
        video_url: YouTube動画のURL
        video_id: 動画ID（出力ディレクトリ名に使用）
        timestamps_sec: 抽出する秒数のリスト [45.0, 120.0, ...]
        quality: FFmpegのq:vパラメータ (1=最高品質, 5=標準)

    Returns:
        {秒数: 画像ファイルパス} の辞書。失敗した秒数はスキップされる。
    """
    if not timestamps_sec:
        return {}

    # 出力先ディレクトリ
    frames_dir = os.path.join(OUTPUT_DIR, f"{video_id}_frames")
    os.makedirs(frames_dir, exist_ok=True)

    # ffmpegのパスを決定
    ffmpeg_exe = _get_ffmpeg_path()
    if ffmpeg_exe == "ffmpeg":
        # 動的検索も試みる
        found = _find_ffmpeg_in_winget()
        if found:
            ffmpeg_exe = found

    # yt-dlp で動画の直リンクURLを取得（ダウンロードせず）
    print(f"  [screenshot] 動画ストリームURLを取得中...")
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                "--get-url",
                "--format", "bestvideo[height<=720][ext=mp4]/bestvideo[height<=720]/best[height<=720]",
                "--no-playlist",
                video_url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        stream_url = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
    except Exception as e:
        print(f"  [screenshot] ストリームURL取得失敗: {e}")
        stream_url = None

    if not stream_url:
        print("  [screenshot] 動画ストリームURLを取得できませんでした。スキップします。")
        return {}

    print(f"  [screenshot] {len(timestamps_sec)}件のフレームを抽出中...")
    extracted = {}

    for sec in timestamps_sec:
        out_path = os.path.join(frames_dir, f"frame_{int(sec):05d}s.jpg")
        if os.path.exists(out_path):
            extracted[sec] = out_path
            continue

        try:
            cmd = [
                ffmpeg_exe,
                "-ss", str(sec),          # シーク（入力前指定で高速）
                "-i", stream_url,
                "-frames:v", "1",          # 1フレームのみ
                "-q:v", str(quality),
                "-vf", "scale=960:-2",     # 960px幅でリサイズ
                "-y",                      # 上書き許可
                out_path,
            ]
            subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                check=True,
            )
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                extracted[sec] = out_path
                print(f"  [screenshot] {int(sec)}s → {os.path.basename(out_path)}")
            else:
                print(f"  [screenshot] {int(sec)}s: 画像が生成されませんでした")
        except subprocess.TimeoutExpired:
            print(f"  [screenshot] {int(sec)}s: タイムアウト、スキップ")
        except subprocess.CalledProcessError as e:
            print(f"  [screenshot] {int(sec)}s: FFmpegエラー、スキップ")
        except Exception as e:
            print(f"  [screenshot] {int(sec)}s: エラー ({e})、スキップ")

    print(f"  [screenshot] 抽出完了: {len(extracted)}/{len(timestamps_sec)} フレーム")
    return extracted
