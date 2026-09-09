import os
import re
import frontmatter
import markdown
from config import OUTPUT_DIR


def _build_hero_image_html(video_id: str) -> str:
    """
    記事の見出し画像（ヒーロー画像）のHTMLを生成する。
    YouTubeの公式サムネイル画像（文字や完成品写真入りの公式画像）を最優先で使用する。
    ローカルにダウンロード済みサムネイルがあればそれを使い、なければYouTubeサムネイルURLを参照する。
    """
    # 1. ローカルにダウンロードされたサムネイルファイルを確認
    thumb_filename = f"{video_id}_thumb.jpg"
    thumb_path = os.path.join(OUTPUT_DIR, thumb_filename)
    if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 1000:
        return (
            f'<div class="hero-image">'
            f'<img src="{thumb_filename}" alt="YouTube動画サムネイル" loading="lazy">'
            f'</div>'
        )

    # 2. frames ディレクトリ内のサムネイル画像を確認
    frames_thumb = os.path.join(OUTPUT_DIR, f"{video_id}_frames", "thumbnail.jpg")
    if os.path.exists(frames_thumb) and os.path.getsize(frames_thumb) > 1000:
        rel_path = f"{video_id}_frames/thumbnail.jpg"
        return (
            f'<div class="hero-image">'
            f'<img src="{rel_path}" alt="YouTube動画サムネイル" loading="lazy">'
            f'</div>'
        )

    # 3. YouTube公式サムネイルURLを直接参照（フォールバック付き）
    thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    fallback_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return (
        f'<div class="hero-image">'
        f'<img src="{thumb_url}" alt="YouTube動画サムネイル" loading="lazy" '
        f'onerror="this.src=\'{fallback_url}\'">'
        f'</div>'
    )


def _inject_scene_images(html_content: str, video_id: str, scenes: list) -> str:
    """
    HTML本文中の <h2> タグの直後に、対応するシーン画像を挿入する。
    
    scenes: analysis_result["重要シーン"] のリスト
            [{"秒数": 45, "説明": "..."}, ...]
    """
    frames_dir = os.path.join(OUTPUT_DIR, f"{video_id}_frames")
    if not os.path.isdir(frames_dir) or not scenes:
        return html_content

    # フレームファイルを秒数でインデックス化
    frame_files = {}
    for f in os.listdir(frames_dir):
        if f.endswith(".jpg") and f.startswith("frame_"):
            # "frame_00045s.jpg" → 45
            try:
                sec = int(f.replace("frame_", "").replace("s.jpg", ""))
                frame_files[sec] = os.path.join(f"{video_id}_frames", f).replace("\\", "/")
            except ValueError:
                pass

    if not frame_files:
        return html_content

    # シーンを秒数順にソート（見出し画像はYouTube公式サムネイルなので、シーン画像は先頭からh2に順次挿入）
    sorted_scenes = sorted(scenes, key=lambda s: s.get("秒数", 0))

    # h2タグを順番に見つけて、各々の直後にシーン画像を挿入
    h2_pattern = re.compile(r'(<h2[^>]*>.*?</h2>)', re.DOTALL)
    h2_positions = [(m.start(), m.end(), m.group(0)) for m in h2_pattern.finditer(html_content)]

    if not h2_positions:
        return html_content

    usable_scenes = sorted_scenes

    result = html_content
    offset = 0  # 挿入によるインデックスのずれ

    for i, (start, end, h2_tag) in enumerate(h2_positions):
        if i >= len(usable_scenes):
            break

        scene = usable_scenes[i]
        sec = scene.get("秒数", 0)
        caption = scene.get("説明", "")

        # 最も近いフレームファイルを探す
        available_secs = list(frame_files.keys())
        if not available_secs:
            break
        closest_sec = min(available_secs, key=lambda s: abs(s - sec))
        rel_path = frame_files[closest_sec]

        img_html = (
            f'\n<div class="scene-capture">'
            f'<img src="{rel_path}" alt="{caption}" loading="lazy">'
            f'<div class="scene-caption">{caption}</div>'
            f'</div>\n'
        )

        # h2タグの直後に挿入
        insert_pos = start + offset + len(h2_tag)
        result = result[:insert_pos] + img_html + result[insert_pos:]
        offset += len(img_html)

    return result


def sanitize_filename(text: str) -> str:
    """ファイル名として使用不可な文字を除去し、安全な文字列にする"""
    if not text:
        return "untitled"
    # Windows/Linux禁忌文字 \ / : * ? " < > | および制御文字を除去
    clean = re.sub(r'[\\/:*?"<>|\r\n\t]', '_', text)
    # 連続スペースを1つに整理
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:100]


def clean_markdown_text(raw_text: str) -> str:
    """Markdownテキストから余計なコードブロック囲みや壊れたフロントマター指定を除去する"""
    text = raw_text.strip()
    # 先頭の ```yaml や ```markdown を除去
    text = re.sub(r'^```(?:yaml|markdown)?\s*\n', '', text, flags=re.IGNORECASE)
    # 末尾の ``` を除去
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def generate_html_preview(
    markdown_path: str,
    video_id: str = None,
    scenes: list = None,
    upload_date: str = None,
    title_text: str = None,
) -> str:
    """
    生成されたMarkdownファイル（YAMLフロントマター付き）を読み込み、
    リッチなHTMLテンプレートに埋め込んでプレビュー用HTMLを生成・保存する。

    Args:
        markdown_path: Markdownファイルのパス
        video_id: 動画ID（画像埋め込みに使用、省略可）
        scenes: analysis_result["重要シーン"] のリスト（省略可）
        upload_date: 動画投稿日 (例: "20260906" または "2026-09-06")
        title_text: 動画タイトル
    """
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Markdownファイルが見つかりません: {markdown_path}")

    # テンプレートの読み込み
    template_path = os.path.join(os.path.dirname(__file__), 'template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Markdownとフロントマターの解析
    with open(markdown_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    cleaned_text = clean_markdown_text(raw_text)
    post = frontmatter.loads(cleaned_text)

    # 本文に残ったフロントマターのゴミ（--- など）やコードブロックをクレンジング
    content_body = post.content.strip()
    content_body = re.sub(r'^```(?:yaml|markdown)?\s*\n', '', content_body, flags=re.IGNORECASE)
    content_body = re.sub(r'\n```\s*$', '', content_body)

    # 記事本文をMarkdownからHTMLに変換 (テーブル拡張を有効化)
    html_content = markdown.markdown(content_body, extensions=['tables'])

    # フロントマターからメタデータを取得
    title = post.get('title') or title_text or '無題のSEO記事'
    description = post.get('description', '')
    keywords = post.get('keywords', [])
    source_url = post.get('source_youtube_url', '')

    # video_idがない場合、ファイル名から推測する
    if not video_id:
        base_name = os.path.basename(markdown_path)
        video_id = base_name.split('_')[0] if '_' in base_name else None

    # タグ(キーワード)のHTML生成
    tags_html = "".join([f'<span class="tag">{kw}</span>' for kw in keywords])

    # ソースリンクのHTML生成
    source_link_html = ""
    if source_url:
        source_link_html = f'<a href="{source_url}" target="_blank" class="source-link">🔗 元のYouTube動画を見る</a>'

    # ヒーロー画像のHTML生成
    hero_image_html = ""
    if video_id:
        hero_image_html = _build_hero_image_html(video_id)

    # セクション画像の注入
    if video_id and scenes:
        html_content = _inject_scene_images(html_content, video_id, scenes)

    # 保存ファイル名の決定 (投稿日 + タイトル または従来通りのfallback)
    target_title = title_text or post.get('title')
    if upload_date and target_title:
        if len(upload_date) == 8 and upload_date.isdigit():
            date_prefix = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        else:
            date_prefix = upload_date
        clean_name = sanitize_filename(target_title)
        html_file_name = f"{date_prefix}_{clean_name}.html"
    else:
        base_name = os.path.basename(markdown_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        html_file_name = f"{file_name_without_ext}.html"

    # 表示タイトル（ユーザー指示: 「htmlファイル名と同じでよい」）
    display_title = os.path.splitext(html_file_name)[0]

    # テンプレートに埋め込み
    final_html = html_template
    final_html = final_html.replace('{{title}}', display_title)
    final_html = final_html.replace('{{description}}', description)
    final_html = final_html.replace('{{tags_html}}', tags_html)
    final_html = final_html.replace('{{source_link_html}}', source_link_html)
    final_html = final_html.replace('{{hero_image_html}}', hero_image_html)
    final_html = final_html.replace('{{content}}', html_content)

    html_output_path = os.path.join(OUTPUT_DIR, html_file_name)

    # HTMLの保存
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    return html_output_path


