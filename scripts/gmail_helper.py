"""
이메일 헬퍼 — Gmail SMTP 앱 비밀번호 방식 관리자 알림 및 뉴스레터 발송
"""

import os
import socket
import smtplib
from contextlib import contextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@contextmanager
def _force_ipv4():
    """Anthropic Cloud 컨테이너 IPv6 미지원 대응 — SMTP 연결 시 IPv4 강제."""
    _orig = socket.getaddrinfo
    def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
        return _orig(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = _ipv4_only
    try:
        yield
    finally:
        socket.getaddrinfo = _orig


def _smtp_config() -> tuple[str, str]:
    sender = os.environ.get("GMAIL_SENDER_ADDRESS", "")
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not sender or not password:
        raise EnvironmentError("GMAIL_SENDER_ADDRESS, GMAIL_APP_PASSWORD 환경 변수가 필요합니다.")
    return sender, password


def send_admin_notification(to: str, subject: str, body: str) -> None:
    """관리자에게 텍스트 알림 이메일을 발송한다."""
    try:
        sender, password = _smtp_config()
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to
        with _force_ipv4():
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                smtp.sendmail(sender, [to], msg.as_string())
    except Exception as exc:
        print(f"[WARN] 관리자 알림 발송 실패 ({to}): {exc}")


def send_newsletter(recipients: list[str], subject: str, html_body: str) -> dict:
    """
    수신자 목록에 뉴스레터 HTML 이메일을 개별 발송한다.

    Returns:
        {"sent": [...], "failed": [...]}
    """
    sender, password = _smtp_config()
    sent, failed = [], []

    try:
        with _force_ipv4():
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                for recipient in recipients:
                    try:
                        msg = MIMEMultipart("alternative")
                        msg["Subject"] = subject
                        msg["From"] = sender
                        msg["To"] = recipient
                        msg.attach(MIMEText(html_body, "html", "utf-8"))
                        smtp.sendmail(sender, [recipient], msg.as_string())
                        sent.append(recipient)
                    except Exception as exc:
                        print(f"[WARN] 발송 실패 ({recipient}): {exc}")
                        failed.append(recipient)
    except Exception as exc:
        print(f"[ERROR] SMTP 연결 실패: {exc}")
        failed.extend(recipients)

    return {"sent": sent, "failed": failed}
