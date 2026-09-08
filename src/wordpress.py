"""
src/wordpress.py
WordPress REST API (Application Passwords 認証) を利用して、
記事・固定ページの投稿、メディアのアップロード、カテゴリ・タグの管理を行うクライアントモジュール。
"""
import os
import mimetypes
import requests
from typing import Optional, List, Dict, Any, Tuple
import config

class WordPressClient:
    """WordPress REST API クライアント"""

    def __init__(
        self,
        site_url: Optional[str] = None,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        default_status: Optional[str] = None
    ):
        self.site_url = (site_url or config.WP_SITE_URL or "").rstrip("/")
        self.username = username or config.WP_USERNAME or ""
        self.app_password = app_password or config.WP_APP_PASSWORD or ""
        self.default_status = default_status or config.WP_DEFAULT_STATUS or "draft"

        self.api_base = f"{self.site_url}/wp-json/wp/v2" if self.site_url else ""
        self.auth = (self.username, self.app_password) if (self.username and self.app_password) else None

    def is_configured(self) -> bool:
        """WordPress連携に必要な設定が揃っているか判定"""
        return bool(self.site_url and self.username and self.app_password)

    def test_connection(self) -> Tuple[bool, str]:
        """
        API接続テストを行う。
        成功時は (True, ユーザー表示名/メッセージ)、失敗時は (False, エラーメッセージ) を返す。
        """
        if not self.is_configured():
            return False, "WordPressの接続設定（WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD）が不足しています。"

        try:
            url = f"{self.api_base}/users/me"
            response = requests.get(url, auth=self.auth, timeout=10)
            if response.status_code == 200:
                data = response.json()
                name = data.get("name", self.username)
                return True, f"WordPress API接続成功: 認証ユーザー '{name}' (ID: {data.get('id')})"
            else:
                return False, f"WordPress API接続エラー: HTTP {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"WordPress接続例外: {str(e)}"

    def upload_media(self, file_path: str, title: Optional[str] = None) -> Optional[int]:
        """
        画像などのメディアファイルをアップロードし、media_id を返す。
        """
        if not self.is_configured():
            print("[WP Client] 接続情報が未設定のためメディアアップロードをスキップします。")
            return None

        if not os.path.exists(file_path):
            print(f"[WP Client] メディアファイルが存在しません: {file_path}")
            return None

        filename = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "image/jpeg"

        url = f"{self.api_base}/media"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type
        }

        try:
            with open(file_path, "rb") as f:
                media_bytes = f.read()

            response = requests.post(
                url,
                auth=self.auth,
                headers=headers,
                data=media_bytes,
                timeout=30
            )

            if response.status_code in (200, 201):
                data = response.json()
                media_id = data.get("id")
                print(f"[WP Client] メディアアップロード成功: ID {media_id} ({filename})")
                return media_id
            else:
                print(f"[WP Client] メディアアップロード失敗: HTTP {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[WP Client] メディアアップロード例外: {e}")
            return None

    def get_or_create_category(self, name: str) -> Optional[int]:
        """
        指定名のカテゴリを取得、存在しなければ新規作成して category_id を返す。
        """
        if not self.is_configured() or not name:
            return None

        try:
            # 既存検索
            url = f"{self.api_base}/categories"
            response = requests.get(url, auth=self.auth, params={"search": name, "per_page": 10}, timeout=10)
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat.get("name") == name:
                        return cat.get("id")

            # 新規作成
            post_response = requests.post(url, auth=self.auth, json={"name": name}, timeout=10)
            if post_response.status_code in (200, 201):
                return post_response.json().get("id")
            else:
                print(f"[WP Client] カテゴリ作成失敗 ({name}): {post_response.status_code} - {post_response.text}")
                return None
        except Exception as e:
            print(f"[WP Client] カテゴリ処理例外 ({name}): {e}")
            return None

    def get_or_create_tag(self, name: str) -> Optional[int]:
        """
        指定名のタグを取得、存在しなければ新規作成して tag_id を返す。
        """
        if not self.is_configured() or not name:
            return None

        try:
            # 既存検索
            url = f"{self.api_base}/tags"
            response = requests.get(url, auth=self.auth, params={"search": name, "per_page": 10}, timeout=10)
            if response.status_code == 200:
                tags = response.json()
                for tag in tags:
                    if tag.get("name") == name:
                        return tag.get("id")

            # 新規作成
            post_response = requests.post(url, auth=self.auth, json={"name": name}, timeout=10)
            if post_response.status_code in (200, 201):
                return post_response.json().get("id")
            else:
                print(f"[WP Client] タグ作成失敗 ({name}): {post_response.status_code} - {post_response.text}")
                return None
        except Exception as e:
            print(f"[WP Client] タグ処理例外 ({name}): {e}")
            return None

    def publish_post(
        self,
        title: str,
        html_content: str,
        status: Optional[str] = None,
        category_ids: Optional[List[int]] = None,
        tag_ids: Optional[List[int]] = None,
        featured_media_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        記事を投稿する。
        """
        if not self.is_configured():
            print("[WP Client] 接続情報が未設定のため投稿をスキップします。")
            return None

        post_status = status or self.default_status
        payload = {
            "title": title,
            "content": html_content,
            "status": post_status
        }
        if category_ids:
            payload["categories"] = category_ids
        if tag_ids:
            payload["tags"] = tag_ids
        if featured_media_id:
            payload["featured_media"] = featured_media_id

        try:
            url = f"{self.api_base}/posts"
            response = requests.post(url, auth=self.auth, json=payload, timeout=20)
            if response.status_code in (200, 201):
                data = response.json()
                post_id = data.get("id")
                link = data.get("link")
                print(f"[WP Client] 記事投稿成功: ID {post_id} ({post_status}) -> {link}")
                return data
            else:
                print(f"[WP Client] 記事投稿失敗: HTTP {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[WP Client] 記事投稿例外: {e}")
            return None

    def publish_page(
        self,
        title: str,
        html_content: str,
        status: str = "publish",
        slug: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        固定ページを投稿または更新する。
        slug が指定されており、すでに同一スラッグの固定ページが存在する場合は更新する。
        """
        if not self.is_configured():
            print("[WP Client] 接続情報が未設定のため固定ページ投稿をスキップします。")
            return None

        payload: Dict[str, Any] = {
            "title": title,
            "content": html_content,
            "status": status
        }
        if slug:
            payload["slug"] = slug

        try:
            # 同一slugのページが存在するか確認
            existing_id = None
            if slug:
                check_url = f"{self.api_base}/pages"
                check_res = requests.get(check_url, auth=self.auth, params={"slug": slug}, timeout=10)
                if check_res.status_code == 200:
                    pages = check_res.json()
                    if pages:
                        existing_id = pages[0].get("id")

            if existing_id:
                update_url = f"{self.api_base}/pages/{existing_id}"
                response = requests.post(update_url, auth=self.auth, json=payload, timeout=20)
                action = "更新"
            else:
                create_url = f"{self.api_base}/pages"
                response = requests.post(create_url, auth=self.auth, json=payload, timeout=20)
                action = "新規作成"

            if response.status_code in (200, 201):
                data = response.json()
                page_id = data.get("id")
                link = data.get("link")
                print(f"[WP Client] 固定ページ{action}成功: ID {page_id} (slug: {slug}) -> {link}")
                return data
            else:
                print(f"[WP Client] 固定ページ{action}失敗: HTTP {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[WP Client] 固定ページ投稿例外: {e}")
            return None
