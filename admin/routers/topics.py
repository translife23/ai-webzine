"""기획 주제 라우터 — 관리자가 보고서 주제 1건을 입력한다. 보고서 제목·테마 영역은 Routine B가 자동 선택."""

from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper
from routers.auth import _get_current_user

router = APIRouter()


class ReportPlan(BaseModel):
    agenda: str
    perspective: str


class ThemePlan(BaseModel):
    report_1: ReportPlan


@router.get("/plan")
def get_plan(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    week = _week_id()
    gh = GitHubHelper()
    plan = gh.read_json(f"data/weekly/{week}/theme-plan.json")
    return plan or {"week": week, "submitted_at": None}


@router.post("/plan")
def submit_plan(body: ThemePlan, session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    week = _week_id()
    gh = GitHubHelper()

    plan_data = {
        "week": week,
        "report_1": body.report_1.model_dump(),
        "submitted_by": user["username"],
        "submitted_at": _now(),
    }
    gh.write_json(f"data/weekly/{week}/theme-plan.json", plan_data, "admin: 기획 주제 입력")

    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    gh.write_json(f"data/weekly/{week}/status.json", {
        **status,
        "status": "THEME_PLAN_READY",
        "timeline": {**status.get("timeline", {}), "theme_plan_submitted": _now()},
    })

    return {"message": "기획 주제가 등록되었습니다. Routine B가 월요일 03:00에 실행됩니다."}


@router.put("/plan")
def update_plan(body: ThemePlan, session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    week = _week_id()
    gh = GitHubHelper()

    status = gh.read_json(f"data/weekly/{week}/status.json") or {}
    if status.get("status") in ("GENERATING", "DRAFT_READY", "PUBLISHING", "PUBLISHED"):
        raise HTTPException(status_code=400, detail="Routine B 실행 후에는 기획 주제를 수정할 수 없습니다.")

    plan_data = {
        "week": week,
        "report_1": body.report_1.model_dump(),
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
