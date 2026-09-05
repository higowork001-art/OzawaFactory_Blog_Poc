import sys
from src.youtube import extract_video_id, get_video_info
from src.transcript import get_transcript, get_transcript_with_timestamps
from src.analyzer import analyze_transcript
from src.article_generator import generate_article
from src.output import save_transcript, save_analysis, save_article
from src.html_generator import generate_html_preview
from src.screenshot import extract_frames

def main():
    print("="*50)
    print("YouTube → AI SEO記事生成システム MVP")
    print("="*50)
    
    url = input("YouTube URLを入力してください: ").strip()
    if not url:
        print("エラー: URLが入力されていません。")
        sys.exit(1)
        
    try:
        # [1/8] YouTube動画情報取得
        print("\n[1/8] YouTube動画を解析しています...")
        video_id = extract_video_id(url)
        video_info = get_video_info(url)
        
        # [2/8] 字幕取得（プレーンテキスト）
        print("[2/8] 字幕を取得しています...")
        transcript = get_transcript(video_id)
        
        # タイムスタンプ付き字幕（AIシーン選定用・失敗してもOK）
        timed_transcript = get_transcript_with_timestamps(video_id)
        if timed_transcript:
            print(f"  → タイムスタンプ付き字幕 {len(timed_transcript)} 件取得")
        
        # [3/8] 字幕整理と保存
        print("[3/8] 字幕を整理して保存しています...")
        transcript_path = save_transcript(video_id, transcript)
        
        # [4/8] AI分析（重要シーン選定を含む）
        print("[4/8] AIで動画内容を分析しています...")
        analysis_result = analyze_transcript(transcript, video_info, timed_transcript)
        analysis_path = save_analysis(video_id, analysis_result)
        
        # 重要シーンを取得
        scenes = analysis_result.get("重要シーン", [])
        if scenes:
            print(f"  → 重要シーン {len(scenes)} 件を選定")
        
        # [5/8] スクリーンショット抽出
        print("[5/8] 動画からスクリーンショットを抽出しています...")
        if scenes:
            timestamps = [s.get("秒数", 0) for s in scenes if s.get("秒数") is not None]
            if timestamps:
                extracted_frames = extract_frames(url, video_id, timestamps)
                print(f"  → {len(extracted_frames)}/{len(timestamps)} フレーム抽出完了")
            else:
                print("  → タイムスタンプ情報がないためスキップ")
                extracted_frames = {}
        else:
            print("  → 重要シーン情報がないためスキップ")
            extracted_frames = {}
        
        # [6/8] 記事生成
        print("[6/8] SEO記事を生成しています...")
        article_markdown = generate_article(analysis_result, video_info, url)
        
        # [7/8] ファイル保存
        print("[7/8] ファイルを保存しています...")
        article_path = save_article(video_id, article_markdown)
        
        # [8/8] HTMLプレビュー生成（画像埋め込み含む）
        print("[8/8] HTMLプレビューを生成しています...")
        html_path = generate_html_preview(
            article_path,
            video_id=video_id,
            scenes=scenes if extracted_frames else None,
        )
        
        print("\n完了しました。")
        print("\n生成されたファイル:")
        print(f"字幕データ: {transcript_path}")
        print(f"分析データ: {analysis_path}")
        print(f"記事(Markdown): {article_path}")
        print(f"記事(HTMLプレビュー): {html_path}")
        if extracted_frames:
            print(f"スクリーンショット: output/{video_id}_frames/ ({len(extracted_frames)}枚)")
        
    except ValueError as e:
        print(f"\n処理を中断しました: {str(e)}")
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
