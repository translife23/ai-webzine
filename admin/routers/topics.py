"""기획 주제 라우터 — 관리자가 기술/비기술 보고서 주제를 입력한다."""

from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper
from auth import _get_current_user

router = APIRouter()

THEME_AREAS = [
    "공공 AI 서비스 & 규제",
    "AI 기술 & 인프라",
    "AI 산업 & 시장",
    "AI 경제 & 금융",
    "AI 정책 & 거버넌스",
    "AI 사회 & 문화",
    "AI 안보 & 지정학",
]


class ReportPlan(BaseModel):
    theme_area: str
    title: str
    agenda: str
    perspective: str


class ThemePlan(BaseModel):
    tech_report: ReportPlan
    nontech_report: ReportPlan


@router.get("/areas")
def get_theme_areas():
    return {"theme_areas": THEME_AREAS}


@router.get("/plan")
def get_plan(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    week = _week_id()
    gh = GitHubHelper()
    plan = gh.read_json(f"data/weekly/{week}/theme-plan.json")
    return plan or {"week": week, "submitted": False}


@router.post("/plan")
def submit_plan(body: ThemePlan, session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)

    for field_name, report in [("tech_report", body.tech_report), ("nontech_report", body.nontech_report)]:
        if report.theme_area not in THEME_AREAS:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 테마 영역: {report.theme_area}")

    week = _week_id()
    gh = GitHubHelper()

    plan_data = {
        "week": week,
        "tech_report": body.tech_report.model_dump(),
        "nontech_report": body.nontech_report.model_dump(),
        "submitted_by": user["username"],
        "submitted_at": _now(),
    }
    gh.write_json(f"data/weekly/{week}/theme-plan.json", plan_data, "admin: 기획 주제 입력")

    # 상태 업데이트: THEME_PLAN_READY
    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    gh.write_json(f"data/weekly/{week}/status.json", {
        **status,
        "status": "THEME_PLAN_READY",
        "timeline": {**status.get("timeline", {}), "theme_plan_submitted": _now()},
    })

    return {"message": "기획 주제가 등록되었습니다. Routine B가 월요일 03:00에 실행됩니다."}


@router.put("/plan")
def update_plan(body: ThemePlan, session_id: str | None = Cookie(default=None)):
    """기획 주제 수정 (Routine B 실행 전까지만 가능)"""
    user = _get_current_user(session_id)
    week = _week_id()
    gh = GitHubHelper()

    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    if status.get("status") in ("GENERATING", "DRAFT_READY", "PUBLISHING", "PUBLISHED"):
        raise HTTPException(status_code=400, detail="Routine B 실행 후에는 기획 주제를 수정할 수 없습니다.")

    plan_data = {
        "week": week,
        "tech_report": body.tech_report.model_dump(),
        "nontech_report": body.nontech_report.model_dump(),
        "submitted_by": user["username"],
        "submitted_at": _now(),
    }
    gh.write_json(f"data/weekly/{week}/theme-plan.json", plan_data, "admin: 기획 주제 수정")
    return {"message": "기획 주제가 수정되었습니다."}


def _week_id() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
