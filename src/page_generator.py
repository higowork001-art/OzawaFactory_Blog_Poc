"""
src/page_generator.py
固定ページ（このサイトについて・お問い合わせ・プライバシーポリシー・運営者情報）の
Markdownコンテンツを Gemini API で生成するモジュール。
"""
import os
import sys
import re

# WindowsコンソールでのCP932文字化け防止
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import google.generativeai as genai
from config import (
    ARTICLE_MODEL,
    OUTPUT_DIR,
    SITE_NAME,
    SITE_OPERATOR_NAME,
    SITE_CONTACT_EMAIL,
    SITE_LAUNCH_DATE,
    SITE_GENRE,
    USES_GOOGLE_ANALYTICS,
    PAGE_ABOUT_PROMPT_PATH,
    PAGE_CONTACT_PROMPT_PATH,
    PAGE_PRIVACY_PROMPT_PATH,
    PAGE_OPERATOR_PROMPT_PATH,
)

PAGES_DIR = os.path.join(OUTPUT_DIR, "pages")

# 固定ページの定義: (プロンプトパス, 出力ファイル名, ページタイトル, WPスラッグ)
PAGE_DEFINITIONS = [
    (PAGE_ABOUT_PROMPT_PATH,    "about.md",           "このサイトについて",       "about"),
    (PAGE_CONTACT_PROMPT_PATH,  "contact.md",         "お問い合わせ",             "contact"),
    (PAGE_PRIVACY_PROMPT_PATH,  "privacy_policy.md",  "プライバシーポリシー",     "privacy-policy"),
    (PAGE_OPERATOR_PROMPT_PATH, "operator_info.md",   "運営者情報",               "operator-info"),
]


def _replace_placeholders(template: str) -> str:
    """プロンプトテンプレート内の {{変数}} を .env の実値に置換する"""
    replacements = {
        "{{SITE_NAME}}": SITE_NAME,
        "{{SITE_OPERATOR_NAME}}": SITE_OPERATOR_NAME,
        "{{SITE_CONTACT_EMAIL}}": SITE_CONTACT_EMAIL,
        "{{SITE_LAUNCH_DATE}}": SITE_LAUNCH_DATE,
        "{{SITE_GENRE}}": SITE_GENRE,
        "{{USES_GOOGLE_ANALYTICS}}": USES_GOOGLE_ANALYTICS,
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value or "（未設定）")
    return result


def _clean_response(text: str) -> str:
    """Gemini APIレスポンスからコードブロック囲みを除去する"""
    text = text.strip()
    text = re.sub(r'^```(?:markdown|yaml)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def generate_page(prompt_path: str, page_title: str) -> str:
    """
    指定されたプロンプトファイルを使って固定ページのMarkdownを生成する。

    Args:
        prompt_path: プロンプトファイルのパス
        page_title: ページタイトル（生成指示に含める）

    Returns:
        生成されたMarkdownテキスト
    """
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # プレースホルダーを実値に置換
    system_prompt = _replace_placeholders(prompt_template)

    model = genai.GenerativeModel(
        model_name=ARTICLE_MODEL,
        system_instruction=system_prompt,
        generation_config={"temperature": 0.7}
    )

    user_content = f"「{page_title}」ページの本文をMarkdown形式で作成してください。"
    response = model.generate_content(user_content)

    return _clean_response(response.text)


def generate_all_pages(force: bool = False) -> dict:
    """
    全固定ページ（4種）のMarkdownを一括生成し、output/pages/ に保存する。

    Args:
        force: True の場合、既存ファイルがあっても上書きする

    Returns:
        {ページスラッグ: 保存パス} の辞書
    """
    pages_dir = os.path.join(OUTPUT_DIR, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    results = {}
    for prompt_path, filename, title, slug in PAGE_DEFINITIONS:
        output_path = os.path.join(pages_dir, filename)

        if os.path.exists(output_path) and not force:
            print(f"  [page_generator] スキップ（既存）: {filename}")
            results[slug] = output_path
            continue

        print(f"  [page_generator] 生成中: {title} ...")
        try:
            content = generate_page(prompt_path, title)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [page_generator] 完了: {output_path}")
            results[slug] = output_path
        except Exception as e:
            print(f"  [page_generator] エラー（{title}）: {e}")
            results[slug] = None

    return results
