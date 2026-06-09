"""
Gmail API 헬퍼 — 관리자 알림 이메일 및 뉴스레터 발송을 담당한다.
"""

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _get_service():
    """Gmail API 서비스 객체를 반환한다."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("gmail", "v1", credentials=creds)


def send_admin_notification(to: str, subject: str, body: str) -> None:
    """관리자에게 텍스트 알림 이메일을 발송한다."""
    sender = os.environ.get("GMAIL_SENDER_ADDRESS", "")
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service = _get_service()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_newsletter(recipients: list[str], subject: str, html_body: str) -> dict:
    """
    수신자 목록에 뉴스레터 HTML 이메일을 개별 발송한다.

    Returns:
        {"sent": [...], "failed": [...]}
    """
    sender = os.environ.get("GMAIL_SENDER_ADDRESS", "")
    service = _get_service()

    sent, failed = [], []
    for recipient in recipients:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = sender
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            sent.append(recipient)
        except Exception as exc:
            print(f"[WARN] 발송 실패 ({recipient}): {exc}")
            failed.append(recipient)

    return {"sent": sent, "failed": failed}
