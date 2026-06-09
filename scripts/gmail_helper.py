"""
이메일 헬퍼 — Gmail API (OAuth2) 방식 관리자 알림 및 뉴스레터 발송
SMTP 포트 차단 환경(Anthropic Cloud)에서도 HTTPS(443)로 정상 동작.
"""

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _get_access_token() -> str:
    resp = httpx.post(_TOKEN_URL, data={
        "client_id":     os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type":    "refresh_token",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def _send_raw(access_token: str, raw_bytes: bytes) -> None:
    encoded = base64.urlsafe_b64encode(raw_bytes).decode()
    resp = httpx.post(
        _SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": encoded},
        timeout=30,
    )
    resp.raise_for_status()


def send_admin_notification(to: str, subject: str, body: str) -> None:
    """관리자에게 텍스트 알림 이메일을 발송한다."""
    try:
        sender = os.environ["GMAIL_SENDER_ADDRESS"]
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to
        token = _get_access_token()
        _send_raw(token, msg.as_bytes())
    except Exception as exc:
        print(f"[WARN] 관리자 알림 발송 실패 ({to}): {exc}")


def send_newsletter(recipients: list[str], subject: str, html_body: str) -> dict:
    """
    수신자 목록에 뉴스레터 HTML 이메일을 개별 발송한다.

    Returns:
        {"sent": [...], "failed": [...]}
    """
    sender = os.environ["GMAIL_SENDER_ADDRESS"]
    sent, failed = [], []

    try:
        token = _get_access_token()
    except Exception as exc:
        print(f"[ERROR] 액세스 토큰 발급 실패: {exc}")
        return {"sent": [], "failed": recipients}

    for recipient in recipients:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            _send_raw(token, msg.as_bytes())
            sent.append(recipient)
        except Exception as exc:
            print(f"[WARN] 발송 실패 ({recipient}): {exc}")
            failed.append(recipient)

    return {"sent": sent, "failed": failed}
