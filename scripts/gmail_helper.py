"""
이메일 헬퍼 — Resend API 기반 관리자 알림 및 뉴스레터 발송
"""

import os
import resend


def _client() -> resend.Emails:
    resend.api_key = os.environ["RESEND_API_KEY"]
    return resend.Emails


def send_admin_notification(to: str, subject: str, body: str) -> None:
    """관리자에게 텍스트 알림 이메일을 발송한다."""
    sender = os.environ.get("RESEND_SENDER_ADDRESS", "onboarding@resend.dev")
    try:
        _client().send({
            "from": sender,
            "to": [to],
            "subject": subject,
            "text": body,
        })
    except Exception as exc:
        print(f"[WARN] 관리자 알림 발송 실패 ({to}): {exc}")


def send_newsletter(recipients: list[str], subject: str, html_body: str) -> dict:
    """
    수신자 목록에 뉴스레터 HTML 이메일을 개별 발송한다.

    Returns:
        {"sent": [...], "failed": [...]}
    """
    sender = os.environ.get("RESEND_SENDER_ADDRESS", "onboarding@resend.dev")
    emails_api = _client()

    sent, failed = [], []
    for recipient in recipients:
        try:
            emails_api.send({
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "html": html_body,
            })
            sent.append(recipient)
        except Exception as exc:
            print(f"[WARN] 발송 실패 ({recipient}): {exc}")
            failed.append(recipient)

    return {"sent": sent, "failed": failed}
