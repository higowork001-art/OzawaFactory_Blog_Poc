"""
scratch/update_thumbnails_and_rebuild_html.py
既存の動画5件のYouTube公式サムネイル画像をダウンロードし、
HTMLプレビューおよびポータルindex.htmlを再生成するスクリプト。
"""
import os
import sys
import json
import glob

# パス追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.screenshot import download_thumbnail
from src.html_generator import generate_html_preview
from src.build_portal import build_portal

def main():
    print("=== YouTube公式サムネイルダウンロード & HTML再生成 ===")
    
    # 既存の analysis.json ファイルを探索
    analysis_files = glob.glob(os.path.join(config.OUTPUT_DIR, "*_analysis.json"))
    
    for af in analysis_files:
        video_id = os.path.basename(af).replace("_analysis.json", "")
        print(f"\n[処理中] video_id: {video_id}")
        
        # 1. YouTube公式サムネイルのダウンロード
        thumb_path = download_thumbnail(video_id)
        print(f"  → サムネイル保存: {thumb_path}")
        
        # 2. analysis.json 読み込み
        with open(af, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
            
        scenes = analysis_data.get("重要シーン", [])
        
        # 3. 対応する Markdown 記事ファイルを探索
        md_path = os.path.join(config.OUTPUT_DIR, f"{video_id}_article.md")
        if not os.path.exists(md_path):
            print(f"  ⚠️ Markdownファイルが見つかりません: {md_path}")
            continue
            
        # 4. 既存HTMLファイルから日付とタイトルを特定
        # 命名規則: YYYY-MM-DD_タイトル.html
        matching_htmls = [
            f for f in glob.glob(os.path.join(config.OUTPUT_DIR, "202*-*.html"))
        ]
        
        # タイトルの特定
        target_html = None
        for h in matching_htmls:
            with open(h, "r", encoding="utf-8", errors="ignore") as f:
                c = f.read()
                if f"watch?v={video_id}" in c or f"/{video_id}_" in c or f"{video_id}" in c:
                    target_html = h
                    break
        
        if target_html:
            fname = os.path.basename(target_html)
            # 例: 2026-09-06_うまさ大爆発‼ フライパン１つで出来る鶏ももとあさりの酒蒸し.html
            parts = fname.replace(".html", "").split("_", 1)
            upload_date = parts[0]
            title_text = parts[1] if len(parts) > 1 else ""
            print(f"  → 検出されたHTML: {fname} (日付: {upload_date}, タイトル: {title_text})")
        else:
            upload_date = "2026-09-01"
            title_text = None
            print(f"  → 既存HTML特定できず。標準設定で生成します")
            
        # 5. HTML再生成
        out_html = generate_html_preview(
            markdown_path=md_path,
            video_id=video_id,
            scenes=scenes,
            upload_date=upload_date,
            title_text=title_text
        )
        print(f"  → HTML再生成完了: {os.path.basename(out_html)}")
        
        # 旧形式の {video_id}_article.html も存在すれば更新
        legacy_html = os.path.join(config.OUTPUT_DIR, f"{video_id}_article.html")
        if os.path.exists(legacy_html):
            generate_html_preview(
                markdown_path=md_path,
                video_id=video_id,
                scenes=scenes,
                upload_date=None,
                title_text=None
            )
            print(f"  → 旧形式HTML更新: {os.path.basename(legacy_html)}")

    # 6. ポータルトップページ（index.html）の再ビルド
    print("\n[ポータル再構築] build_portal() 実行中...")
    build_portal()
    print("\n✅ 全てのHTMLおよびサムネイルの更新が完了しました！")

if __name__ == "__main__":
    main()
