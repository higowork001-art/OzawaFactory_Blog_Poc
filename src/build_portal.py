"""
src/build_portal.py
ローカルでブログサイト全体の構成・デザイン（トップページ、記事一覧、固定ページ4種）を
Chromeなどのブラウザでプレビュー確認するためのポータルHTML生成スクリプト。
任意文字でのキーワード検索（複数単語AND検索対応）およびカテゴリ絞り込みに完全対応。
"""
import os
import sys
import re
import glob
import html
from collections import Counter
import markdown
from datetime import datetime

# Windowsコンソール文字化け対策
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_clean_markdown(text: str) -> str:
    """Markdownからコードブロック囲みや余計な記号を除去"""
    text = text.strip()
    text = re.sub(r'^```(?:markdown|yaml)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()

def extract_searchable_text(html_content: str) -> str:
    """HTMLからスクリプトやタグを除去し、検索用プレーンテキストを抽出"""
    # script/styleの除去
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
    # HTMLタグの除去
    text = re.sub(r'<[^>]+>', ' ', text)
    # HTMLエンティティのアンエスケープ
    text = html.unescape(text)
    # 余分な空白の整理
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def build_static_page_html(md_path: str, title: str, nav_prefix: str = "../") -> str:
    """固定ページ用のHTMLを生成"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned = get_clean_markdown(content)
    body_html = markdown.markdown(cleaned, extensions=['extra', 'tables', 'nl2br'])

    site_name = config.SITE_NAME or "ステンレス鍋のための料理教室!大澤ブログ"

    html_out = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {site_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #f0f4fd 0%, #e2ebf8 100%);
            --glass-bg: rgba(255, 255, 255, 0.85);
            --glass-border: rgba(255, 255, 255, 0.7);
            --text-main: #1f2937;
            --text-muted: #4b5563;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --card-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
        }}
        body {{
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
            color: var(--text-main);
            background: var(--bg-gradient);
            background-attachment: fixed;
            margin: 0;
            padding: 0;
            line-height: 1.8;
            min-height: 100vh;
        }}
        nav.global-nav {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(229, 231, 235, 0.8);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        }}
        .nav-inner {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .site-logo {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #111827;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .nav-links {{
            display: flex;
            gap: 20px;
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .nav-links a {{
            text-decoration: none;
            color: var(--text-muted);
            font-size: 0.95rem;
            font-weight: 600;
            transition: color 0.2s;
        }}
        .nav-links a:hover, .nav-links a.active {{
            color: var(--accent);
        }}
        .container {{
            max-width: 860px;
            margin: 40px auto;
            padding: 48px;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            box-shadow: var(--card-shadow);
        }}
        .page-header {{
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .page-header h1 {{
            margin: 0 0 10px 0;
            font-size: 2rem;
            color: #111827;
        }}
        .page-body h2 {{
            font-size: 1.5rem;
            color: #1f2937;
            margin-top: 36px;
            margin-bottom: 16px;
            border-left: 5px solid var(--accent);
            padding-left: 14px;
        }}
        .page-body table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .page-body th, .page-body td {{
            padding: 14px 18px;
            border: 1px solid #e5e7eb;
            text-align: left;
        }}
        .page-body th {{
            background: #f9fafb;
            font-weight: 600;
            width: 25%;
        }}
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 40px;
            padding: 10px 22px;
            background: #ffffff;
            color: var(--accent);
            border: 1px solid #d1d5db;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .back-btn:hover {{
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
            transform: translateY(-2px);
        }}
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        /* 固定ページ スマホ最適化 */
        @media (max-width: 768px) {{
            .nav-inner {{
                padding: 12px 16px;
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
            }}
            .site-logo {{
                font-size: 1.2rem;
                justify-content: center;
            }}
            .nav-links {{
                display: flex;
                gap: 8px;
                overflow-x: auto;
                white-space: nowrap;
                -webkit-overflow-scrolling: touch;
                padding-bottom: 4px;
                scrollbar-width: none;
            }}
            .nav-links::-webkit-scrollbar {{
                display: none;
            }}
            .nav-links a {{
                padding: 6px 14px;
                background: rgba(0, 0, 0, 0.04);
                border-radius: 18px;
                font-size: 0.85rem;
                display: inline-block;
                flex-shrink: 0;
            }}
            .nav-links a.active {{
                background: var(--accent);
                color: #ffffff;
            }}
            .container {{
                margin: 16px 12px;
                padding: 24px 18px;
                border-radius: 16px;
            }}
            .page-header h1 {{
                font-size: 1.5rem;
            }}
            .page-body table {{
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }}
        }}
    </style>
</head>
<body>
    <nav class="global-nav">
        <div class="nav-inner">
            <a href="{nav_prefix}index.html" class="site-logo">🍳 {site_name}</a>
            <ul class="nav-links">
                <li><a href="{nav_prefix}index.html">ホーム</a></li>
                <li><a href="{nav_prefix}pages/about.html" {'class="active"' if 'about' in md_path else ''}>このサイトについて</a></li>
                <li><a href="{nav_prefix}pages/contact.html" {'class="active"' if 'contact' in md_path else ''}>お問い合わせ</a></li>
                <li><a href="{nav_prefix}pages/privacy_policy.html" {'class="active"' if 'privacy' in md_path else ''}>プライバシーポリシー</a></li>
                <li><a href="{nav_prefix}pages/operator_info.html" {'class="active"' if 'operator' in md_path else ''}>運営者情報</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <div class="page-header">
            <h1>{title}</h1>
        </div>
        <div class="page-body">
            {body_html}
        </div>
        <a href="{nav_prefix}index.html" class="back-btn">← トップページに戻る</a>
    </div>

    <footer>
        <p>© {datetime.now().year} {site_name} All Rights Reserved.</p>
    </footer>
</body>
</html>
"""
    return html_out

def determine_category(title: str, description: str) -> str:
    """記事タイトルと概要から最適なカテゴリを判定（検証・レビューを最優先判定）"""
    combined = f"{title} {description}"
    # 1. レビュー・検証系キーワード（最優先）
    if any(k in combined for k in ["実験", "検証", "レビュー", "比較", "耐久", "1年つかったら", "１年つかったら", "使ったらどうなった"]):
        return "レビュー・検証"
    # 2. 調理器具系（鍋の活用など）
    elif any(k in combined for k in ["ステンレス鍋フル活用", "フライパン選び", "鍋磨き", "調理器具"]):
        return "調理器具・器具活用"
    # 3. その他はレシピ・料理
    else:
        return "レシピ・料理"

def build_portal():
    output_dir = config.OUTPUT_DIR
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    site_name = config.SITE_NAME or "ステンレス鍋のための料理教室!大澤ブログ"
    site_operator = config.SITE_OPERATOR_NAME or "大澤　勇"
    site_genre = config.SITE_GENRE or "ステンレス鍋・簡単おうちごはん・料理レシピ"

    print("=" * 50)
    print(" [Build Portal] ローカルブログサイト生成開始")
    print("=" * 50)

    # 1. 固定ページのHTML化
    page_specs = [
        ("about.md", "about.html", "このサイトについて"),
        ("contact.md", "contact.html", "お問い合わせ"),
        ("privacy_policy.md", "privacy_policy.html", "プライバシーポリシー"),
        ("operator_info.md", "operator_info.html", "運営者情報"),
    ]

    for md_file, html_file, page_title in page_specs:
        md_path = os.path.join(pages_dir, md_file)
        if os.path.exists(md_path):
            html_path = os.path.join(pages_dir, html_file)
            rendered = build_static_page_html(md_path, page_title, nav_prefix="../")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"  [固定ページHTML作成] {html_file}")

    # 2. 記事一覧の収集
    html_files = sorted(glob.glob(os.path.join(output_dir, "202[0-9]-*.html")), reverse=True)
    
    articles = []
    for h_path in html_files:
        filename = os.path.basename(h_path)
        date_match = re.match(r"^(\d{4}-\d{2}-\d{2})_(.+)\.html$", filename)
        if date_match:
            pub_date = date_match.group(1)
            raw_title = date_match.group(2)
        else:
            pub_date = "2026-09-01"
            raw_title = filename.replace(".html", "")

        with open(h_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', content)
        description = desc_match.group(1) if desc_match else "動画から抽出した詳しいレシピと調理のポイントを分かりやすく解説します。"

        img_match = re.search(r'<div class="hero-image">\s*<img\s+src="([^"]+)"', content)
        if img_match:
            img_src = img_match.group(1)
        else:
            img_src = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"

        # 正確なカテゴリ判定
        category = determine_category(raw_title, description)

        # 全文検索用のテキスト抽出
        searchable_body = extract_searchable_text(content)
        # タイトル、カテゴリ、概要、本文を統合した検索用文字列
        combined_search_text = f"{raw_title} {category} {description} {searchable_body}".lower()

        articles.append({
            "filename": filename,
            "title": raw_title,
            "date": pub_date,
            "description": description[:110] + "..." if len(description) > 110 else description,
            "image": img_src,
            "category": category,
            "search_text": html.escape(combined_search_text, quote=True),
        })

    total_articles = len(articles)
    cat_counts = Counter(a["category"] for a in articles)
    print(f"  [記事検出] {total_articles} 件の記事を検出しました。")
    for cat_name, count in cat_counts.items():
        print(f"    - {cat_name}: {count} 件")

    # 定義カテゴリリスト（出現順を安定化）
    all_categories = ["レシピ・料理", "調理器具・器具活用", "レビュー・検証"]
    for c in cat_counts.keys():
        if c not in all_categories:
            all_categories.append(c)

    # 3. 記事カード HTML 生成（data-category, data-search-text 属性付き）
    article_cards_html = ""
    for idx, a in enumerate(articles):
        article_cards_html += f"""
        <article class="post-card" data-category="{a['category']}" data-title="{html.escape(a['title'], quote=True)}" data-search-text="{a['search_text']}">
            <a href="{a['filename']}" class="post-card-thumb-link">
                <img src="{a['image']}" alt="{html.escape(a['title'])}" class="post-card-thumb" onerror="this.src='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80'">
                <button type="button" class="category-badge" data-filter="{a['category']}" title="{a['category']}で絞り込む">{a['category']}</button>
            </a>
            <div class="post-card-content">
                <div class="post-meta">
                    <span class="post-date">📅 {a['date']}</span>
                </div>
                <h2 class="post-title"><a href="{a['filename']}">{a['title']}</a></h2>
                <p class="post-desc">{a['description']}</p>
                <div class="post-card-footer">
                    <a href="{a['filename']}" class="read-more">記事を読む <span>→</span></a>
                </div>
            </div>
        </article>
        """
        # 2記事目の後にAdSenseインフィード広告スロットを配置
        if idx == 1:
            article_cards_html += """
        <div class="ad-container ad-infeed">
            <span class="ad-notice">スポンサーリンク</span>
            <div class="ad-box">
                <!-- Google AdSense In-feed Ad Code Here -->
                <span>広告スペース（AdSense インフィード広告）</span>
            </div>
        </div>
        """

    # 4. カテゴリフィルタータブ HTML
    filter_tabs_html = f'<button type="button" class="filter-btn active" data-filter="all">すべて ({total_articles})</button>'
    for cat in all_categories:
        count = cat_counts.get(cat, 0)
        filter_tabs_html += f'<button type="button" class="filter-btn" data-filter="{cat}">{cat} ({count})</button>'

    # 5. サイドバー カテゴリリンク HTML
    sidebar_cat_html = f'<li><a href="javascript:void(0)" class="cat-link active" data-filter="all">すべて表示 <span>{total_articles}</span></a></li>'
    for cat in all_categories:
        count = cat_counts.get(cat, 0)
        sidebar_cat_html += f'<li><a href="javascript:void(0)" class="cat-link" data-filter="{cat}">{cat} <span>{count}</span></a></li>'

    index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_name} | 公式ブログ</title>
    <meta name="description" content="{site_name} - YouTube動画からお届けする時短＆美味しいおうちごはんレシピと調理器具の使い方レビュー">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #eef4fc 0%, #e0ebf9 100%);
            --glass-bg: rgba(255, 255, 255, 0.85);
            --glass-border: rgba(255, 255, 255, 0.7);
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --card-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        }}
        * {{
            box-sizing: border-box;
        }}
        html, body {{
            overflow-x: hidden;
            max-width: 100vw;
        }}
        body {{
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
            color: var(--text-main);
            background: var(--bg-gradient);
            background-attachment: fixed;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        /* ナビゲーションバー */
        nav.global-nav {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(229, 231, 235, 0.8);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        }}
        .nav-inner {{
            max-width: 1140px;
            margin: 0 auto;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .site-logo {{
            font-size: 1.35rem;
            font-weight: 800;
            color: #111827;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.02em;
        }}
        .nav-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px 18px;
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .nav-links a {{
            text-decoration: none;
            color: #4b5563;
            font-size: 0.95rem;
            font-weight: 600;
            transition: color 0.2s;
            white-space: nowrap;
        }}
        .nav-links a:hover, .nav-links a.active {{
            color: var(--accent);
        }}

        /* ヒーローセクション */
        .hero-banner {{
            max-width: 1140px;
            margin: 32px auto 20px;
            padding: 44px 32px;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.92) 0%, rgba(30, 64, 175, 0.95) 100%);
            border-radius: 24px;
            color: #ffffff;
            text-align: center;
            box-shadow: 0 15px 35px rgba(37, 99, 235, 0.2);
            backdrop-filter: blur(8px);
            overflow: hidden;
            word-break: break-word;
        }}
        .hero-banner h1 {{
            margin: 0 0 12px 0;
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -0.01em;
        }}
        .hero-banner p {{
            margin: 0 auto;
            font-size: 1.1rem;
            max-width: 680px;
            opacity: 0.92;
            line-height: 1.7;
        }}

        /* メインレイアウト */
        .main-layout {{
            max-width: 1140px;
            margin: 30px auto 60px;
            padding: 0 20px;
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 36px;
        }}
        @media (max-width: 920px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        /* 検索バーセクション */
        .search-section {{
            margin-bottom: 20px;
        }}
        .search-bar-wrap {{
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1.5px solid #d1d5db;
            border-radius: 24px;
            padding: 6px 10px 6px 16px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
            transition: all 0.25s ease;
        }}
        .search-bar-wrap:focus-within {{
            border-color: var(--accent);
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15), 0 4px 18px rgba(37, 99, 235, 0.1);
        }}
        .search-icon {{
            font-size: 1.15rem;
            margin-right: 10px;
            color: #6b7280;
            user-select: none;
        }}
        .search-input {{
            flex: 1;
            border: none;
            outline: none;
            background: transparent;
            font-size: 0.96rem;
            font-family: inherit;
            color: var(--text-main);
            padding: 8px 4px;
        }}
        .search-input::placeholder {{
            color: #9ca3af;
        }}
        .clear-search-btn {{
            background: #e5e7eb;
            border: none;
            color: #4b5563;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            cursor: pointer;
            margin-right: 8px;
            transition: all 0.2s;
        }}
        .clear-search-btn:hover {{
            background: #d1d5db;
            color: #111827;
        }}
        .search-btn {{
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
            color: #ffffff;
            border: none;
            border-radius: 18px;
            padding: 8px 18px;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
        }}
        .search-btn:hover {{
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
            transform: translateY(-1px);
        }}

        /* カテゴリフィルタータブ */
        .category-filter-section {{
            margin-bottom: 24px;
        }}
        .category-filter-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(8px);
            padding: 10px 14px;
            border-radius: 16px;
            border: 1px solid var(--glass-border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }}
        .filter-btn {{
            background: #ffffff;
            border: 1px solid #d1d5db;
            color: #4b5563;
            padding: 7px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{
            background: #f3f4f6;
            color: var(--accent);
            border-color: var(--accent);
        }}
        .filter-btn.active {{
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }}

        /* 絞り込み状態表示バナー */
        .filter-status-banner {{
            display: none;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 0.95rem;
            color: #1e40af;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .filter-status-banner strong {{
            font-weight: 700;
            color: #1d4ed8;
        }}
        .reset-filter-btn {{
            background: none;
            border: 1px solid #fca5a5;
            color: #dc2626;
            font-weight: 700;
            cursor: pointer;
            font-size: 0.85rem;
            padding: 5px 12px;
            border-radius: 8px;
            background: #ffffff;
            transition: all 0.2s;
        }}
        .reset-filter-btn:hover {{
            background: #fee2e2;
            border-color: #ef4444;
        }}

        /* 該当記事なしメッセージ */
        .no-results {{
            display: none;
            text-align: center;
            padding: 60px 20px;
            background: var(--glass-bg);
            border-radius: 20px;
            color: var(--text-muted);
            border: 1px dashed #cbd5e1;
        }}
        .no-results h3 {{
            margin: 10px 0;
            color: #1f2937;
        }}
        .no-results p {{
            margin: 8px 0 18px 0;
            font-size: 0.95rem;
        }}

        /* 記事一覧 */
        .posts-grid {{
            display: flex;
            flex-direction: column;
            gap: 28px;
        }}
        .post-card {{
            display: flex;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            overflow: hidden;
            box-shadow: var(--card-shadow);
            transition: transform 0.25s, box-shadow 0.25s;
        }}
        .post-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.09);
        }}
        .post-card-thumb-link {{
            width: 280px;
            min-width: 280px;
            position: relative;
            overflow: hidden;
            display: block;
        }}
        @media (max-width: 640px) {{
            .post-card {{
                flex-direction: column;
            }}
            .post-card-thumb-link {{
                width: 100%;
                min-width: 100%;
                height: 200px;
            }}
        }}
        .post-card-thumb {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }}
        .post-card:hover .post-card-thumb {{
            transform: scale(1.04);
        }}
        .category-badge {{
            position: absolute;
            top: 14px;
            left: 14px;
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(6px);
            color: #ffffff;
            padding: 5px 14px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid rgba(255,255,255,0.25);
            cursor: pointer;
            transition: all 0.2s;
        }}
        .category-badge:hover {{
            background: var(--accent);
            transform: scale(1.05);
        }}
        .post-card-content {{
            padding: 24px 28px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex-grow: 1;
        }}
        .post-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        .post-title {{
            margin: 0 0 10px 0;
            font-size: 1.3rem;
            line-height: 1.45;
            font-weight: 700;
        }}
        .post-title a {{
            color: #111827;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .post-title a:hover {{
            color: var(--accent);
        }}
        .post-desc {{
            color: #4b5563;
            font-size: 0.95rem;
            margin: 0 0 16px 0;
            line-height: 1.65;
        }}
        .post-card-footer {{
            display: flex;
            justify-content: flex-end;
        }}
        .read-more {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
            font-size: 0.9rem;
            transition: gap 0.2s;
        }}
        .read-more:hover {{
            gap: 8px;
            color: var(--accent-hover);
        }}

        /* サイドバー */
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 28px;
        }}
        .sidebar-widget {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            padding: 24px;
            box-shadow: var(--card-shadow);
        }}
        .widget-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #111827;
            margin: 0 0 16px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .profile-card {{
            text-align: center;
        }}
        .profile-avatar {{
            width: 76px;
            height: 76px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            font-size: 2rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }}
        .profile-name {{
            font-size: 1.15rem;
            font-weight: 700;
            margin: 0 0 4px 0;
        }}
        .profile-role {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 12px;
        }}
        .profile-bio {{
            font-size: 0.9rem;
            color: #4b5563;
            line-height: 1.6;
            margin-bottom: 14px;
        }}
        .widget-links {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .widget-links li {{
            margin-bottom: 8px;
        }}
        .widget-links a {{
            color: #374151;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            border-radius: 10px;
            transition: all 0.2s;
        }}
        .widget-links a span {{
            background: rgba(0,0,0,0.06);
            color: #6b7280;
            font-size: 0.8rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }}
        .widget-links a:hover {{
            background: rgba(37, 99, 235, 0.08);
            color: var(--accent);
        }}
        .widget-links a.active {{
            background: var(--accent);
            color: #ffffff;
        }}
        .widget-links a.active span {{
            background: rgba(255,255,255,0.25);
            color: #ffffff;
        }}

        /* 公式ストア・ショップウィジェット */
        .shop-widget {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(240, 247, 255, 0.92));
            border: 1.5px solid #bfdbfe;
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.08);
        }}
        .shop-card {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .shop-label {{
            font-size: 1rem;
            font-weight: 700;
            color: #1e3a8a;
            margin: 0;
            line-height: 1.4;
        }}
        .shop-desc {{
            font-size: 0.88rem;
            color: #4b5563;
            line-height: 1.6;
            margin: 0;
        }}
        .shop-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-top: 6px;
            padding: 11px 18px;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            text-decoration: none;
            border-radius: 12px;
            font-size: 0.92rem;
            font-weight: 700;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);
            transition: all 0.25s ease;
        }}
        .shop-btn:hover {{
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38);
            color: #ffffff;
        }}

        /* ページネーション */
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 28px;
            padding: 16px 0;
        }}
        .page-btn {{
            background: #ffffff;
            border: 1px solid #d1d5db;
            color: #4b5563;
            padding: 10px 20px;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .page-btn:hover:not(:disabled) {{
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
        }}
        .page-btn:disabled {{
            opacity: 0.4;
            cursor: default;
        }}
        .page-info {{
            font-size: 0.88rem;
            color: var(--text-muted);
            font-weight: 600;
        }}

        /* レスポンシブ & モバイル最適化 */
        @media (max-width: 768px) {{
            .nav-inner {{
                padding: 12px 16px;
                flex-direction: column;
                align-items: stretch;
                gap: 8px;
            }}
            .site-logo {{
                font-size: 1.15rem;
                justify-content: center;
            }}
            .nav-links {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 6px;
                padding-bottom: 2px;
            }}
            .nav-links a {{
                padding: 5px 12px;
                background: rgba(0, 0, 0, 0.04);
                border-radius: 16px;
                font-size: 0.78rem;
                display: inline-block;
            }}
            .nav-links a.active {{
                background: var(--accent);
                color: #ffffff;
            }}
            .hero-banner {{
                margin: 12px 12px 10px;
                padding: 20px 16px;
                border-radius: 16px;
            }}
            .hero-banner h1 {{
                font-size: 1.3rem;
                margin-bottom: 6px;
            }}
            .hero-banner p {{
                font-size: 0.82rem;
                line-height: 1.5;
            }}
            .main-layout {{
                margin: 12px auto 32px;
                padding: 0 12px;
                gap: 20px;
            }}
            .search-bar-wrap {{
                padding: 4px 8px 4px 12px;
            }}
            .search-input {{
                font-size: 0.88rem;
            }}
            .search-btn {{
                padding: 6px 14px;
                font-size: 0.82rem;
            }}
            .category-filter-bar {{
                padding: 8px 10px;
                gap: 6px;
            }}
            .filter-btn {{
                padding: 5px 10px;
                font-size: 0.76rem;
                border-radius: 14px;
            }}
            .post-card {{
                flex-direction: column;
                border-radius: 14px;
            }}
            .post-card-thumb-link {{
                width: 100%;
                min-width: 100%;
                height: 180px;
            }}
            .post-card-content {{
                padding: 14px 16px;
            }}
            .post-title {{
                font-size: 1.05rem;
                line-height: 1.4;
            }}
            .post-desc {{
                font-size: 0.84rem;
                line-height: 1.5;
                margin-bottom: 10px;
            }}
            .sidebar-widget {{
                padding: 18px 14px;
                border-radius: 14px;
            }}
            .container {{
                margin: 12px 10px;
                padding: 20px 14px;
                border-radius: 14px;
            }}
            .page-header h1 {{
                font-size: 1.4rem;
            }}
        }}

        /* Google AdSense 広告枠スタイル */
        .ad-container {{
            margin: 24px 0;
            text-align: center;
        }}
        .ad-notice {{
            font-size: 0.72rem;
            color: #9ca3af;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
            display: block;
            text-transform: uppercase;
        }}
        .ad-box {{
            background: rgba(255, 255, 255, 0.75);
            border: 1px dashed #cbd5e1;
            border-radius: 14px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 0.82rem;
            min-height: 110px;
            transition: all 0.2s;
        }}
        .ad-box:hover {{
            border-color: #94a3b8;
            background: rgba(255, 255, 255, 0.95);
        }}
        .ad-infeed {{
            margin: 16px 0;
        }}
        .ad-infeed .ad-box {{
            min-height: 100px;
        }}
        .ad-sidebar .ad-box {{
            min-height: 240px;
        }}

        /* フッター */
        footer.site-footer {{
            background: #ffffff;
            border-top: 1px solid #e5e7eb;
            padding: 36px 16px;
            margin-top: 50px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.88rem;
        }}
        .footer-nav {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }}
        .footer-nav a {{
            color: #4b5563;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: color 0.2s;
        }}
        .footer-nav a:hover {{
            color: var(--accent);
        }}
    </style>
</head>
<body>
    <!-- ヘッダーグローバルナビ -->
    <nav class="global-nav">
        <div class="nav-inner">
            <a href="index.html" class="site-logo">🍳 {site_name}</a>
            <ul class="nav-links">
                <li><a href="index.html" class="active">ホーム</a></li>
                <li><a href="pages/about.html">このサイトについて</a></li>
                <li><a href="pages/contact.html">お問い合わせ</a></li>
                <li><a href="pages/privacy_policy.html">プライバシーポリシー</a></li>
                <li><a href="pages/operator_info.html">運営者情報</a></li>
                <li><a href="#shop-section" style="color: #d97706;">🛍️ オリジナル商品</a></li>
            </ul>
        </div>
    </nav>

    <!-- ヒーローヘッダー -->
    <header class="hero-banner">
        <h1>{site_name}</h1>
        <p>{site_genre}の最新記事をお届け。毎日の料理がグッと楽しくなるノウハウや調理器具の検証結果を体系的にお届けします。</p>
    </header>

    <!-- メインレイアウト -->
    <div class="main-layout">
        <!-- 記事一覧コンテナ -->
        <main>
            <!-- 任意文字キーワード検索バー -->
            <div class="search-section">
                <div class="search-bar-wrap">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="keyword-search-input" class="search-input" placeholder="料理名・食材・器具で検索（例: 鯛 ポワレ、鶏肉、フライパン...）" autocomplete="off">
                    <button type="button" id="clear-search-btn" class="clear-search-btn" title="検索ワードをクリア" style="display: none;">✕</button>
                    <button type="button" id="submit-search-btn" class="search-btn">検索</button>
                </div>
            </div>

            <!-- カテゴリ絞り込みタブ -->
            <div class="category-filter-section">
                <div class="category-filter-bar">
                    {filter_tabs_html}
                </div>
            </div>

            <!-- 絞り込み状況バナー -->
            <div id="filter-status-banner" class="filter-status-banner">
                <span id="filter-status-text"></span>
                <button type="button" id="reset-filter-btn" class="reset-filter-btn">✕ 絞り込みを解除</button>
            </div>

            <!-- 記事一覧 -->
            <div class="posts-grid" id="posts-container">
                {article_cards_html}
            </div>

            <!-- ページネーション -->
            <div class="pagination" id="pagination">
                <button type="button" class="page-btn" id="prev-page-btn" disabled>← 前のページ</button>
                <span class="page-info" id="page-info"></span>
                <button type="button" class="page-btn" id="next-page-btn">次のページ →</button>
            </div>

            <!-- 0件時の表示 -->
            <div id="no-results-msg" class="no-results">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">🔍</div>
                <h3>該当する記事が見つかりませんでした</h3>
                <p id="no-results-desc">検索キーワードを変更するか、絞り込みを解除してください。</p>
                <button type="button" id="no-results-reset-btn" class="reset-filter-btn" style="display: inline-block;">絞り込みをリセット</button>
            </div>
        </main>

        <!-- サイドバー -->
        <aside class="sidebar">
            <!-- 運営者プロフィール -->
            <div class="sidebar-widget profile-card">
                <div class="profile-avatar">👨‍🍳</div>
                <h3 class="profile-name">{site_operator}</h3>
                <div class="profile-role">ブログ管理人 / 料理愛好家</div>
                <p class="profile-bio">ステンレス鍋やフライパンを活用した男の手抜き時短料理を発信中。実体験をもとにしたレシピを整理しています。</p>
                <a href="pages/about.html" class="read-more" style="justify-content: center;">詳しいプロフィール <span>→</span></a>
            </div>

            <!-- AdSense サイドバー広告スロット -->
            <div class="sidebar-widget ad-container ad-sidebar">
                <span class="ad-notice">スポンサーリンク</span>
                <div class="ad-box">
                    <!-- Google AdSense Responsive / 300x250 Ad Code Here -->
                    <span>広告スペース（AdSense レクタングル）</span>
                </div>
            </div>

            <!-- サイト情報 -->
            <div class="sidebar-widget">
                <h3 class="widget-title">📌 サイト情報</h3>
                <ul class="widget-links">
                    <li><a href="pages/about.html">このサイトについて <span>›</span></a></li>
                    <li><a href="pages/contact.html">お問い合わせ <span>›</span></a></li>
                    <li><a href="pages/privacy_policy.html">プライバシーポリシー <span>›</span></a></li>
                    <li><a href="pages/operator_info.html">運営者情報 <span>›</span></a></li>
                </ul>
            </div>

            <!-- 大澤チャンネルのオリジナル商品サイト -->
            <div id="shop-section" class="sidebar-widget shop-widget">
                <h3 class="widget-title">🛍️ オリジナル商品</h3>
                <div class="shop-card">
                    <p class="shop-label">●大澤チャンネルのオリジナル商品サイト</p>
                    <p class="shop-desc">大澤チャンネルおすすめ！こだわりのステンレス菜箸や鍋磨き用ブラシなど、便利なオリジナル調理グッズはこちらから。</p>
                    <a href="https://ozawachannnel.stores.jp" target="_blank" rel="noopener noreferrer" class="shop-btn">
                        公式ストアを見る <span>↗</span>
                    </a>
                </div>
            </div>
        </aside>
    </div>

    <!-- フッター -->
    <footer class="site-footer">
        <div class="footer-nav">
            <a href="index.html">ホーム</a>
            <a href="pages/about.html">このサイトについて</a>
            <a href="pages/contact.html">お問い合わせ</a>
            <a href="pages/privacy_policy.html">プライバシーポリシー</a>
            <a href="pages/operator_info.html">運営者情報</a>
        </div>
        <p>© {datetime.now().year} {site_name} All Rights Reserved.</p>
    </footer>

    <!-- カテゴリ絞り込み＋キーワード検索＋ページネーションJavaScript -->
    <script>
        const ITEMS_PER_PAGE = 5;
        let currentPage = 1;
        let currentFilter = 'all';
        let searchTokens = [];

        function parseSearchTokens(text) {{
            if (!text) return [];
            // 全角スペースを半角に置換し、小文字化して分割
            return text.replace(/　/g, ' ').trim().toLowerCase().split(/\\s+/).filter(Boolean);
        }}

        function getVisibleCards() {{
            const cards = Array.from(document.querySelectorAll('.post-card'));
            return cards.filter(card => {{
                // 1. カテゴリチェック
                const cat = card.getAttribute('data-category');
                const matchCategory = (currentFilter === 'all' || cat === currentFilter);
                if (!matchCategory) return false;

                // 2. キーワードチェック（複数単語AND検索）
                if (searchTokens.length === 0) return true;
                const searchText = (card.getAttribute('data-search-text') || '').toLowerCase();
                const cardTitle = (card.getAttribute('data-title') || '').toLowerCase();
                const targetCombined = cardTitle + ' ' + searchText;

                return searchTokens.every(token => targetCombined.includes(token));
            }});
        }}

        function applyPagination() {{
            const allCards = Array.from(document.querySelectorAll('.post-card'));
            const visibleCards = getVisibleCards();
            const totalPages = Math.max(1, Math.ceil(visibleCards.length / ITEMS_PER_PAGE));
            if (currentPage > totalPages) currentPage = totalPages;
            const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
            const endIdx = startIdx + ITEMS_PER_PAGE;

            allCards.forEach(card => {{ card.style.display = 'none'; }});
            visibleCards.forEach((card, i) => {{
                card.style.display = (i >= startIdx && i < endIdx) ? 'flex' : 'none';
            }});

            // インフィード広告: 表示ページの記事が2つ以上の場合のみ表示
            const pageCards = visibleCards.slice(startIdx, endIdx);
            document.querySelectorAll('.ad-infeed').forEach(ad => {{
                ad.style.display = (pageCards.length >= 2 && currentPage === 1) ? 'block' : 'none';
            }});

            // ページネーションUI更新
            const pagination = document.getElementById('pagination');
            const prevBtn = document.getElementById('prev-page-btn');
            const nextBtn = document.getElementById('next-page-btn');
            const pageInfo = document.getElementById('page-info');
            const noResults = document.getElementById('no-results-msg');
            const noResultsDesc = document.getElementById('no-results-desc');

            if (visibleCards.length === 0) {{
                pagination.style.display = 'none';
                if (noResults) {{
                    noResults.style.display = 'block';
                    if (searchTokens.length > 0) {{
                        noResultsDesc.textContent = '「' + searchTokens.join(' ') + '」に一致する記事は見つかりませんでした。別の言葉で検索してください。';
                    }} else {{
                        noResultsDesc.textContent = '選択されたカテゴリの記事は見つかりませんでした。';
                    }}
                }}
            }} else {{
                if (noResults) noResults.style.display = 'none';
                if (totalPages <= 1) {{
                    pagination.style.display = 'none';
                }} else {{
                    pagination.style.display = 'flex';
                    pageInfo.textContent = currentPage + ' / ' + totalPages + ' ページ';
                    prevBtn.disabled = (currentPage <= 1);
                    nextBtn.disabled = (currentPage >= totalPages);
                }}
            }}

            updateFilterBanner(visibleCards.length);
        }}

        function updateFilterBanner(count) {{
            const banner = document.getElementById('filter-status-banner');
            const bannerText = document.getElementById('filter-status-text');
            const hasCategory = currentFilter !== 'all';
            const hasSearch = searchTokens.length > 0;

            if (!hasCategory && !hasSearch) {{
                banner.style.display = 'none';
                return;
            }}

            banner.style.display = 'flex';
            let msg = '';
            if (hasCategory && hasSearch) {{
                msg = 'カテゴリ「<strong>' + currentFilter + '</strong>」 × 検索「<strong>' + searchTokens.join(' ') + '</strong>」の記事を表示中（<strong>' + count + '</strong>件）';
            }} else if (hasCategory) {{
                msg = 'カテゴリ「<strong>' + currentFilter + '</strong>」の記事を表示中（<strong>' + count + '</strong>件）';
            }} else {{
                msg = '検索「<strong>' + searchTokens.join(' ') + '</strong>」の記事を表示中（<strong>' + count + '</strong>件）';
            }}
            bannerText.innerHTML = msg;
        }}

        function applyCategoryFilter(catName) {{
            currentFilter = catName;
            currentPage = 1;

            // ボタンのactiveクラス切り替え
            document.querySelectorAll('.filter-btn, .cat-link').forEach(el => {{
                if (el.getAttribute('data-filter') === catName) {{
                    el.classList.add('active');
                }} else {{
                    el.classList.remove('active');
                }}
            }});

            applyPagination();
        }}

        function handleSearchInput() {{
            const input = document.getElementById('keyword-search-input');
            const clearBtn = document.getElementById('clear-search-btn');
            const val = input.value.trim();

            if (val) {{
                clearBtn.style.display = 'flex';
            }} else {{
                clearBtn.style.display = 'none';
            }}

            searchTokens = parseSearchTokens(val);
            currentPage = 1;
            applyPagination();
        }}

        function resetAllFilters() {{
            const input = document.getElementById('keyword-search-input');
            input.value = '';
            document.getElementById('clear-search-btn').style.display = 'none';
            searchTokens = [];
            currentFilter = 'all';
            currentPage = 1;

            document.querySelectorAll('.filter-btn, .cat-link').forEach(el => {{
                if (el.getAttribute('data-filter') === 'all') {{
                    el.classList.add('active');
                }} else {{
                    el.classList.remove('active');
                }}
            }});

            if (window.location.hash && window.location.hash.startsWith('#category=')) {{
                history.replaceState(null, '', window.location.pathname);
            }}

            applyPagination();
        }}

        // イベントリスナーの登録
        document.addEventListener('DOMContentLoaded', () => {{
            const searchInput = document.getElementById('keyword-search-input');
            const clearSearchBtn = document.getElementById('clear-search-btn');
            const submitSearchBtn = document.getElementById('submit-search-btn');

            // 検索入力時のインクリメンタル検索
            searchInput.addEventListener('input', handleSearchInput);
            searchInput.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    handleSearchInput();
                }}
            }});
            submitSearchBtn.addEventListener('click', handleSearchInput);

            // 検索クリアボタン
            clearSearchBtn.addEventListener('click', () => {{
                searchInput.value = '';
                clearSearchBtn.style.display = 'none';
                searchTokens = [];
                currentPage = 1;
                applyPagination();
                searchInput.focus();
            }});

            // カテゴリタブ・サイドバーボタンのクリック
            document.querySelectorAll('[data-filter]').forEach(el => {{
                el.addEventListener('click', (e) => {{
                    e.preventDefault();
                    e.stopPropagation();
                    const filterVal = el.getAttribute('data-filter');
                    applyCategoryFilter(filterVal);
                }});
            }});

            // 絞り込みリセットボタン
            const resetBtn = document.getElementById('reset-filter-btn');
            if (resetBtn) {{
                resetBtn.addEventListener('click', resetAllFilters);
            }}
            const noResultsResetBtn = document.getElementById('no-results-reset-btn');
            if (noResultsResetBtn) {{
                noResultsResetBtn.addEventListener('click', resetAllFilters);
            }}

            // ページネーションボタン
            document.getElementById('prev-page-btn').addEventListener('click', () => {{
                if (currentPage > 1) {{ currentPage--; applyPagination(); window.scrollTo(0, 0); }}
            }});
            document.getElementById('next-page-btn').addEventListener('click', () => {{
                currentPage++; applyPagination(); window.scrollTo(0, 0);
            }});

            // 初期ロード時のURLハッシュ判定
            const hash = window.location.hash;
            if (hash && hash.startsWith('#category=')) {{
                const targetCat = decodeURIComponent(hash.replace('#category=', ''));
                applyCategoryFilter(targetCat);
            }} else {{
                applyPagination();
            }}
        }});
    </script>
</body>
</html>
"""

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  [トップページ作成完了] {index_path}")
    print("=" * 50)
    print(" [Build Portal] 完了しました！")
    print("=" * 50)
    return index_path

if __name__ == "__main__":
    build_portal()
