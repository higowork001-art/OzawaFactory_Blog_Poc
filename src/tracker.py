import os
from datetime import datetime
from config import PROCESSED_LIST_PATH, OUTPUT_DIR


def load_processed_video_ids() -> set:
    """
    処理済み動画IDのセットを読み込む。
    ファイルが存在しない場合は空のセットを返す。
    """
    if not os.path.exists(PROCESSED_LIST_PATH):
        return set()

    processed_ids = set()
    with open(PROCESSED_LIST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if parts:
                processed_ids.add(parts[0].strip())

    return processed_ids


def mark_video_as_processed(video_id: str, title: str = "") -> None:
    """
    指定された動画IDを処理済みとしてリストファイルに記録する。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_exists = os.path.exists(PROCESSED_LIST_PATH)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_title = title.replace("\t", " ").replace("\n", " ")

    with open(PROCESSED_LIST_PATH, "a", encoding="utf-8") as f:
        if not file_exists:
            f.write("# video_id\tprocessed_at\ttitle\n")
        f.write(f"{video_id}\t{now_str}\t{clean_title}\n")
