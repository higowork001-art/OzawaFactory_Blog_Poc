import os
import sys
import glob
import json
import frontmatter
import markdown

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.html_generator import clean_markdown_text, _build_hero_image_html, _inject_scene_images

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/template.html', 'r', encoding='utf-8') as f:
    template = f.read()

# 既存のHTMLファイルをスキャンしてマッピング
html_files = glob.glob('output/202[0-9]-*.html')
print(f"検出した記事HTML: {len(html_files)} 件")

for h_path in html_files:
    fname = os.path.basename(h_path)
    # タイトル部分から該当するmdを探す、または全mdファイルをチェック
    matched_md = None
    matched_vid = None
    
    # 全mdをチェック
    for md_path in glob.glob('output/*_article.md'):
        vid = os.path.basename(md_path).replace('_article.md', '')
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as mf:
            m_text = mf.read()
        # ファイル名の一部またはvideo_idが含まれるか
        if vid in fname or (len(m_text) > 100 and fname[11:20] in m_text):
            matched_md = md_path
            matched_vid = vid
            break

    if not matched_md:
        # fallback: analysis.jsonから探す
        for j_path in glob.glob('output/*_analysis.json'):
            vid = os.path.basename(j_path).replace('_analysis.json', '')
            try:
                with open(j_path, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                # タイトル一致確認
                for cand in data.get('記事タイトル候補', []):
                    if cand[:10] in fname:
                        matched_md = f'output/{vid}_article.md'
                        matched_vid = vid
                        break
            except Exception:
                pass
            if matched_md:
                break

    if matched_md and os.path.exists(matched_md):
        json_path = f'output/{matched_vid}_analysis.json'
        analysis = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as jf:
                    analysis = json.load(jf)
            except Exception:
                pass

        with open(matched_md, 'r', encoding='utf-8') as mf:
            raw_content = mf.read()

        cleaned = clean_markdown_text(raw_content)
        post = frontmatter.loads(cleaned)

        display_title = fname.replace('.html', '')
        tags = post.get('tags', ['料理レシピ', '時短料理'])
        tags_html = ''.join(f'<span class="tag">#{t}</span>' for t in tags)
        source_url = f'https://www.youtube.com/watch?v={matched_vid}'
        source_html = f'<a href="{source_url}" target="_blank" class="source-link">▶ YouTubeで元動画を見る</a>'
        hero_html = _build_hero_image_html(matched_vid)

        body_html = markdown.markdown(post.content, extensions=['extra', 'tables', 'nl2br'])
        scenes = analysis.get('重要シーン', [])
        body_html = _inject_scene_images(body_html, matched_vid, scenes)

        rendered = template.replace('{{title}}', display_title)
        rendered = rendered.replace('{{description}}', post.get('description', ''))
        rendered = rendered.replace('{{tags_html}}', tags_html)
        rendered = rendered.replace('{{source_link_html}}', source_html)
        rendered = rendered.replace('{{hero_image_html}}', hero_html)
        rendered = rendered.replace('{{content}}', body_html)
        rendered = rendered.replace('{{site_name}}', config.SITE_NAME or "ステンレス鍋のための料理教室!大澤ブログ")
        rendered = rendered.replace('{{year}}', "2026")

        with open(h_path, 'w', encoding='utf-8') as hf:
            hf.write(rendered)
        print(f"  [更新完了] {fname} (ID: {matched_vid})")
    else:
        print(f"  [スキップ] 対応するmdが見つかりませんでした: {fname}")

print("全記事HTMLの更新完了！")
