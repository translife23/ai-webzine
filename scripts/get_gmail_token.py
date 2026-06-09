"""
Gmail OAuth2 리프레시 토큰 발급 도우미 — 로컬에서 1회만 실행.

사용법:
  python scripts/get_gmail_token.py

실행 시 브라우저가 열리고 Google 로그인 후 승인하면
리프레시 토큰이 출력됩니다. 출력된 값을 .env의
GMAIL_REFRESH_TOKEN에 붙여넣으세요.
"""

import os
import sys
import json
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "https://www.googleapis.com/auth/gmail.send"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_auth_code: list[str] = []


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [""])[0]
        if code:
            _auth_code.append(code)
            self.send_response(200)
            self.end_headers()
            self.wfile.write("<h2>인증 완료. 터미널로 돌아가세요.</h2>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("<h2>코드 없음 — 다시 시도하세요.</h2>".encode("utf-8"))

    def log_message(self, *args):
        pass


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("[오류] .env에 GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET이 없습니다.")
        sys.exit(1)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(f"\n브라우저가 열립니다. Google 계정으로 로그인 후 승인하세요.\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8888), _CallbackHandler)
    server.handle_request()

    if not _auth_code:
        print("[오류] 인증 코드를 받지 못했습니다.")
        sys.exit(1)

    resp = httpx.post(TOKEN_URL, data={
        "code": _auth_code[0],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    tokens = resp.json()

    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        print("[오류] 리프레시 토큰이 없습니다. Google Cloud Console에서 테스트 사용자를 추가했는지 확인하세요.")
        sys.exit(1)

    print("\n" + "="*60)
    print("리프레시 토큰 발급 성공!")
    print("="*60)
    print(f"\nGMAIL_REFRESH_TOKEN={refresh_token}\n")
    print(".env 파일에 위 줄을 추가하세요.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
