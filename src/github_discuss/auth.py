"""GitHub 認証管理モジュール。

認証方式の自動切り替え：
- GITHUB_APP_PRIVATE_KEY のファイルが存在 → GitHub App 認証
- それ以外 → Personal Access Token 認証
"""

import os
import time
import jwt
import requests
from typing import Optional


class GitHubAuth:
    """GitHub 認証管理クラス。
    
    認証方式の自動切り替え：
    - GITHUB_APP_PRIVATE_KEY のファイルが存在すれば GitHub App 認証
    - それ以外 → Personal Access Token 認証
    """
    
    def __init__(self):
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY")
        self.installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        self._app_token: Optional[str] = None
        self._app_token_expires_at: float = 0
    
    def is_app_auth(self) -> bool:
        """GitHub App 認証かどうかを判定。
        
        Returns:
            bool: GitHub App 認証の場合は True、それ以外は False
        """
        return bool(self.private_key_path and os.path.exists(self.private_key_path))
    
    def get_token(self) -> str:
        """認証トークンを取得。
        
        Returns:
            str: 認証トークン
        """
        if self.is_app_auth():
            return self._get_app_token()
        else:
            return self._get_personal_token()
    
    def _get_personal_token(self) -> str:
        """Personal Access Token を返す。
        
        Returns:
            str: Personal Access Token
        
        Raises:
            ValueError: GITHUB_TOKEN が設定されていない場合
        """
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN が設定されていません")
        return token
    
    def _get_app_token(self) -> str:
        """GitHub App の Installation Access Token を取得・返す。
        
        トークンはキャッシュされ、有効期限内は再利用される。
        
        Returns:
            str: Installation Access Token
        
        Raises:
            ValueError: 必要な環境変数が設定されていない場合
            requests.RequestException: API リクエストが失敗した場合
        """
        # トークンが有効期限内ならキャッシュを返す
        if self._app_token and time.time() < self._app_token_expires_at:
            return self._app_token
        
        # 新しいトークンを取得
        jwt_token = self._create_jwt()
        
        # Installation Access Token を取得
        response = requests.post(
            f"https://api.github.com/app/installations/{self.installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            },
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        self._app_token = data["token"]
        self._app_token_expires_at = time.time() + 3600  # 1 時間有効
        
        return self._app_token
    
    def _create_jwt(self) -> str:
        """JWT トークンを作成。
        
        Returns:
            str: JWT トークン
        
        Raises:
            ValueError: GITHUB_APP_ID または GITHUB_APP_PRIVATE_KEY が設定されていない場合
        """
        if not self.app_id or not self.private_key_path:
            raise ValueError("GITHUB_APP_ID または GITHUB_APP_PRIVATE_KEY が設定されていません")
        
        with open(self.private_key_path, "r") as f:
            private_key = f.read()
        
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,  # 10 分有効
            "iss": self.app_id
        }
        
        return jwt.encode(payload, private_key, algorithm="RS256")
