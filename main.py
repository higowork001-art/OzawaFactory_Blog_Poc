import sys
import io

# Windowsコンソールでの特殊Unicode文字（感嘆符や絵文字等）出力時のCP932エンコードエラーを防止
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import markdown
import frontmatter
from config import (
    YOUTUBE_CHANNEL_URL,
    MAX_BATCH_VIDEOS,
    CATEGORY_MAP,
    DEFAULT_CATEGORY,
)
from src.youtube import extract_video_id, get_video_info, get_channel_video_urls
from src.transcript import get_transcript, get_transcript_with_timestamps
from src.analyzer import analyze_transcript
from src.article_generator import generate_article
from src.output import save_transcript, save_analysis, save_article
from src.html_generator import generate_html_preview
from src.screenshot import extract_frames
from src.tracker import load_processed_video_ids, mark_video_as_processed
from src.wordpress import WordPressClient



def process_single_video(url: str) -> bool:
    """単一のYouTube動画を処理し、記事とHTMLを生成する"""
    try:
        # [1/9] YouTube動画情報取得
        print(f"\n{'='*40}")
        print(f"対象動画: {url}")
        print(f"{'='*40}")
        print("[1/9] YouTube動画を解析しています...")
        video_id = extract_video_id(url)
        video_info = get_video_info(url)
        title = video_info.get("title", "")
        print(f"  タイトル: {title}")

        # [2/9] 字幕取得（プレーンテキスト）
        print("[2/9] 字幕を取得しています...")
        transcript = get_transcript(video_id)

        # タイムスタンプ付き字幕（AIシーン選定用・失敗してもOK）
        timed_transcript = get_transcript_with_timestamps(video_id)
        if timed_transcript:
            print(f"  → タイムスタンプ付き字幕 {len(timed_transcript)} 件取得")

        # [3/9] 字幕整理と保存
        print("[3/9] 字幕を整理して保存しています...")
        transcript_path = save_transcript(video_id, transcript)

        # [4/9] AI分析（重要シーン選定を含む）
        print("[4/9] AIで動画内容を分析しています...")
        analysis_result = analyze_transcript(transcript, video_info, timed_transcript)
        analysis_path = save_analysis(video_id, analysis_result)

        # 重要シーンを取得
        scenes = analysis_result.get("重要シーン", [])
        if scenes:
            print(f"  → 重要シーン {len(scenes)} 件を選定")

        # [5/9] スクリーンショット抽出
        print("[5/9] 動画からスクリーンショットを抽出しています...")
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

        # [6/9] 記事生成
        print("[6/9] SEO記事を生成しています...")
        article_markdown = generate_article(analysis_result, video_info, url)

        # [7/9] ファイル保存
        print("[7/9] ファイルを保存しています...")
        article_path = save_article(video_id, article_markdown)

        # [8/9] HTMLプレビュー生成（画像埋め込み含む）
        print("[8/9] HTMLプレビューを生成しています...")
        upload_date = video_info.get("upload_date", "")
        html_path = generate_html_preview(
            article_path,
            video_id=video_id,
            scenes=scenes if extracted_frames else None,
            upload_date=upload_date,
            title_text=title,
        )

        # [9/9] WordPress自動投稿（WP設定がある場合のみ実行）
        wp_post_info = None
        client = WordPressClient()
        if client.is_configured():
            print("[9/9] WordPressへ記事を自動投稿しています...")
            try:
                # 投稿用HTML本文とメタデータのパース
                post = frontmatter.loads(article_markdown)
                article_title = post.metadata.get("title") or title
                body_markdown = post.content if post.content else article_markdown
                html_body = markdown.markdown(body_markdown, extensions=["extra", "tables", "nl2br"])

                # アイキャッチ画像（抽出フレームの先頭）のアップロード
                featured_media_id = None
                if extracted_frames:
                    first_frame_path = list(extracted_frames.values())[0]
                    if os.path.isfile(first_frame_path):
                        featured_media_id = client.upload_media(first_frame_path, title=article_title)

                # カテゴリの自動決定
                video_theme = str(analysis_result.get("動画テーマ", ""))
                matched_category = None
                for key, cat_name in CATEGORY_MAP.items():
                    if key in video_theme or key in title:
                        matched_category = cat_name
                        break
                if not matched_category:
                    matched_category = DEFAULT_CATEGORY

                cat_id = client.get_or_create_category(matched_category)
                category_ids = [cat_id] if cat_id else None

                # タグの自動決定
                tag_names = post.metadata.get("keywords") or analysis_result.get("SEOキーワード", [])
                tag_ids = []
                if isinstance(tag_names, list):
                    for tag in tag_names[:5]:
                        if isinstance(tag, str) and tag.strip():
                            t_id = client.get_or_create_tag(tag.strip())
                            if t_id:
                                tag_ids.append(t_id)

                # 記事投稿
                wp_post_info = client.publish_post(
                    title=article_title,
                    html_content=html_body,
                    category_ids=category_ids,
                    tag_ids=tag_ids if tag_ids else None,
                    featured_media_id=featured_media_id
                )
            except Exception as e:
                print(f"  [!] WordPress投稿中にエラーが発生しました（ローカル出力は保持されます）: {e}")
        else:
            print("[9/9] WordPress接続情報が未設定のため、WP自動投稿をスキップしました。")

        # 重複防止リストへ記録
        mark_video_as_processed(video_id, title)

        print("\n[OK] 完了しました！")
        print("生成されたファイル:")
        print(f"  字幕データ: {transcript_path}")
        print(f"  分析データ: {analysis_path}")
        print(f"  記事(Markdown): {article_path}")
        print(f"  記事(HTMLプレビュー): {html_path}")
        if extracted_frames:
            print(f"  スクリーンショット: output/{video_id}_frames/ ({len(extracted_frames)}枚)")
        if wp_post_info:
            print(f"  WordPress投稿: {wp_post_info.get('link')} (Status: {wp_post_info.get('status')})")

        return True

    except ValueError as e:
        print(f"\n[!] 処理をスキップ/中断しました: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[x] 予期せぬエラーが発生しました: {str(e)}")
        return False


def run_batch_mode(channel_url: str, max_count: int = 10):
    """チャンネルURLから最新の未処理動画を取得し、指定件数を一括生成する"""
    print("\n" + "="*50)
    print("YouTubeチャンネル自動一括ブログ化モード")
    print(f"対象チャンネル: {channel_url}")
    print(f"最大処理件数: {max_count} 件")
    print("="*50)

    print("\n[ステップ 1/2] 処理済みリストの読み込み...")
    processed_ids = load_processed_video_ids()
    print(f"  → 現在記録されている処理済み動画数: {len(processed_ids)} 件")

    print("\n[ステップ 2/2] チャンネルから最新動画リストを取得中...")
    # 未処理動画を10件集めるため、多め（30件）に動画一覧を取得
    all_videos = get_channel_video_urls(channel_url, limit=max_count * 3)

    if not all_videos:
        print("動画が見つかりませんでした。チャンネルURLを確認してください。")
        return

    # 未処理動画のみ抽出
    unprocessed_videos = [v for v in all_videos if v["video_id"] not in processed_ids]
    target_videos = unprocessed_videos[:max_count]

    print(f"\n取得できた全動画: {len(all_videos)} 件")
    print(f"うち未処理の動画: {len(unprocessed_videos)} 件")
    print(f"今回処理対象とする動画: {len(target_videos)} 件")

    if not target_videos:
        print("\n[OK] 新しい未処理の動画はありません。すべて生成済みです。")
        return

    # 順次処理を実行
    success_count = 0
    fail_count = 0

    for idx, video in enumerate(target_videos, 1):
        print(f"\n----------------------------------------")
        print(f" 進行状況: [{idx}/{len(target_videos)}] 件目を処理中")
        print(f"----------------------------------------")

        success = process_single_video(video["url"])
        if success:
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "="*50)
    print("[完了] 一括処理が完了しました！")
    print(f"  成功: {success_count} 件")
    print(f"  スキップ/失敗: {fail_count} 件")
    print("="*50)



def main():
    print("="*50)
    print("YouTube → AI SEO記事生成システム MVP (一括自動連携機能付き)")
    print("="*50)

    print("\n【モード選択】")
    if YOUTUBE_CHANNEL_URL:
        print(f"・[Enter] キーを押すと、.envで設定されたチャンネル({YOUTUBE_CHANNEL_URL})から未処理の最新{MAX_BATCH_VIDEOS}件を一括処理します。")
    print("・特定の動画URLを入力すると、その動画1本のみを処理します。")

    url_input = input("\nYouTube URLを入力してください (空エンターで一括処理): ").strip()

    if url_input:
        process_single_video(url_input)
    else:
        if not YOUTUBE_CHANNEL_URL:
            print("エラー: .env に YOUTUBE_CHANNEL_URL が設定されていません。")
            sys.exit(1)
        run_batch_mode(YOUTUBE_CHANNEL_URL, MAX_BATCH_VIDEOS)


if __name__ == "__main__":
    main()

