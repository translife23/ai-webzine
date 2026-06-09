"""워크플로 라우터 — 상태 조회, 기사 확정, 초안 검토, 승인"""

import os
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper
from routers.auth import _get_current_user

router = APIRouter()


def _week_id() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def _gh() -> GitHubHelper:
    return GitHubHelper()


@router.get("/status")
def get_status(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    week = _week_id()
    gh = _gh()
    status = gh.read_json(f"data/weekly/{week}/status.json")
    return status or {"week": week, "status": "IDLE"}


@router.get("/articles")
def get_articles(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    week = _week_id()
    gh = _gh()
    data = gh.read_json(f"data/weekly/{week}/news-candidates.json")
    if not data:
        raise HTTPException(status_code=404, detail="이번 주 뉴스 후보가 아직 없습니다.")
    return data


@router.put("/articles")
def update_articles(body: dict, session_id: str | None = Cookie(default=None)):
    """기사 목록 수정 (관리자가 교체·추가)"""
    _get_current_user(session_id)
    week = _week_id()
    gh = _gh()
    existing = gh.read_json(f"data/weekly/{week}/news-candidates.json") or {}
    existing.update(body)
    gh.write_json(f"data/weekly/{week}/news-candidates.json", existing, "admin: 기사 목록 수정")
    return {"message": "기사 목록 업데이트 완료"}


@router.post("/confirm-articles")
def confirm_articles(session_id: str | None = Cookie(default=None)):
    """기사 선정 확정 → selected-articles.json 저장, 상태 ARTICLES_CONFIRMED"""
    user = _get_current_user(session_id)
    week = _week_id()
    gh = _gh()

    candidates = gh.read_json(f"data/weekly/{week}/news-candidates.json")
    if not candidates:
        raise HTTPException(status_code=404, detail="뉴스 후보가 없습니다.")

    gh.write_json(
        f"data/weekly/{week}/selected-articles.json",
        {**candidates, "confirmed_by": user["username"], "confirmed_at": _now()},
        "admin: 기사 선정 확정",
    )

    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    gh.write_json(f"data/weekly/{week}/status.json", {
        **status,
        "status": "ARTICLES_CONFIRMED",
        "timeline": {**status.get("timeline", {}), "articles_confirmed": _now()},
    })
    return {"message": "기사 선정이 확정되었습니다."}


@router.get("/draft")
def get_draft(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    week = _week_id()
    gh = _gh()
    return {
        "week": week,
        "tech_report": gh.read_text(f"data/weekly/{week}/draft-tech-report.md"),
        "nontech_report": gh.read_text(f"data/weekly/{week}/draft-nontech-report.md"),
        "newsletter_html": gh.read_text(f"data/weekly/{week}/draft-newsletter.html"),
        "webzine_html": gh.read_text(f"data/weekly/{week}/draft-webzine.html"),
    }


@router.put("/draft")
def update_draft(body: dict, session_id: str | None = Cookie(default=None)):
    """초안 직접 수정"""
    user = _get_current_user(session_id)
    week = _week_id()
    gh = _gh()
    if "tech_report" in body:
        gh.write_text(f"data/weekly/{week}/draft-tech-report.md", body["tech_report"], "admin: 기술 보고서 수정")
    if "nontech_report" in body:
        gh.write_text(f"data/weekly/{week}/draft-nontech-report.md", body["nontech_report"], "admin: 비기술 보고서 수정")
    if "newsletter_html" in body:
        gh.write_text(f"data/weekly/{week}/draft-newsletter.html", body["newsletter_html"], "admin: 뉴스레터 수정")
    return {"message": "초안이 업데이트되었습니다."}


@router.post("/approve")
def approve(session_id: str | None = Cookie(default=None)):
    """초안 승인 → approval.json 저장 → Routine C API 트리거"""
    user = _get_current_user(session_id)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="관리자(admin) 권한이 필요합니다.")

    week = _week_id()
    gh = _gh()

    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    if status.get("status") != "DRAFT_READY":
        raise HTTPException(status_code=400, detail=f"승인 가능 상태가 아닙니다. 현재: {status.get('status')}")

    # approval.json 저장
    gh.write_json(f"data/weekly/{week}/approval.json", {
        "approved": True,
        "approved_by": user["username"],
        "approved_at": _now(),
        "week": week,
    }, "admin: 발행 승인")

    # 상태 업데이트
    gh.write_json(f"data/weekly/{week}/status.json", {
        **status,
        "status": "PUBLISHING",
        "timeline": {**status.get("timeline", {}), "approved": _now()},
    })

    # Routine C API 트리거 호출
    endpoint = os.environ.get("ROUTINE_C_ENDPOINT", "")
    token = os.environ.get("ROUTINE_C_BEARER_TOKEN", "")
    trigger_result = "skipped"

    if endpoint and token:
        try:
            resp = httpx.post(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
                json={"week": week, "triggered_by": user["username"]},
                timeout=10,
            )
            trigger_result = f"HTTP {resp.status_code}"
        except Exception as exc:
            trigger_result = f"오류: {exc}"

    return {
        "message": "승인 완료. 발행 파이프라인이 시작됩니다.",
        "routine_c_trigger": trigger_result,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
