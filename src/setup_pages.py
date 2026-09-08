"""
src/setup_pages.py
固定ページ（このサイトについて、お問い合わせ、プライバシーポリシー、運営者情報）を
Gemini APIで生成（または既存ファイルを読み込み）し、WordPressに自動登録・公開するセットアップスクリプト。
"""
import os
import sys

# WindowsコンソールでのCP932文字化け防止
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import markdown
from typing import Dict

# プロジェクトルートをsys.pathに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from src.wordpress import WordPressClient
from src.page_generator import generate_all_pages, PAGES_DIR

PAGE_DEFINITIONS = [
    {
        "key": "about",
        "title": "このサイトについて",
        "slug": "about",
        "filename": "about.md"
    },
    {
        "key": "contact",
        "title": "お問い合わせ",
        "slug": "contact",
        "filename": "contact.md"
    },
    {
        "key": "privacy_policy",
        "title": "プライバシーポリシー",
        "slug": "privacy-policy",
        "filename": "privacy_policy.md"
    },
    {
        "key": "operator_info",
        "title": "運営者情報",
        "slug": "operator-info",
        "filename": "operator_info.md"
    }
]

def setup_pages(regenerate: bool = False) -> Dict[str, bool]:
    """
    固定ページの生成とWordPressへの投稿を実行する。
    """
    print("\n" + "=" * 50)
    print(" [Setup Pages] 固定ページセットアップ開始")
    print("=" * 50)

    # 1. Markdownファイルの確認・生成
    os.makedirs(PAGES_DIR, exist_ok=True)
    all_exist = all(
        os.path.exists(os.path.join(PAGES_DIR, p["filename"]))
        for p in PAGE_DEFINITIONS
    )

    if regenerate or not all_exist:
        print("[Setup Pages] Gemini APIで固定ページMarkdownを生成します...")
        generate_all_pages(force=regenerate)
    else:
        print("[Setup Pages] 既存のMarkdownファイルを使用します。")

    markdown_contents = {}
    for p in PAGE_DEFINITIONS:
        file_path = os.path.join(PAGES_DIR, p["filename"])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_contents[p["key"]] = f.read()

    # 2. WordPressClientの確認
    client = WordPressClient()
    if not client.is_configured():
        print("\n[Setup Pages] 警告: WordPress接続情報が未設定です。")
        print("  .env の WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD を設定してください。")
        print("  ローカルのMarkdownファイル(output/pages/)の生成のみ完了しました。")
        return {p["key"]: False for p in PAGE_DEFINITIONS}

    # 接続確認
    ok, msg = client.test_connection()
    if not ok:
        print(f"\n[Setup Pages] エラー: {msg}")
        return {p["key"]: False for p in PAGE_DEFINITIONS}

    print(f"\n[Setup Pages] {msg}")
    print("[Setup Pages] WordPressへの固定ページ投稿を開始します...")

    results = {}
    for p in PAGE_DEFINITIONS:
        key = p["key"]
        title = p["title"]
        slug = p["slug"]
        md_text = markdown_contents.get(key, "")

        if not md_text:
            print(f"[Setup Pages] スキップ: {title} (内容が空です)")
            results[key] = False
            continue

        # Markdown -> HTML変換
        html_body = markdown.markdown(md_text, extensions=["extra", "tables", "nl2br"])

        print(f"\n[Setup Pages] 投稿処理中: '{title}' (slug: {slug})")
        res = client.publish_page(
            title=title,
            html_content=html_body,
            status="publish",
            slug=slug
        )

        if res:
            results[key] = True
            print(f"[Setup Pages] 成功: '{title}' -> {res.get('link')}")
        else:
            results[key] = False
            print(f"[Setup Pages] 失敗: '{title}'")

    print("\n" + "=" * 50)
    print(" [Setup Pages] 固定ページセットアップ完了")
    print("=" * 50)
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="固定ページ（AdSense用）を生成してWordPressに投稿します")
    parser.add_argument("--regenerate", action="store_true", help="既存のMarkdownを破棄して再生成する")
    args = parser.parse_args()

    setup_pages(regenerate=args.regenerate)
