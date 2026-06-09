"""수신자 관리 라우터"""

from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper
from routers.auth import _get_current_user

router = APIRouter()


class RecipientCreate(BaseModel):
    name: str
    email: str
    department: str = ""
    active: bool = True


class RecipientUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    active: bool | None = None


@router.get("/")
def list_recipients(session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    gh = GitHubHelper()
    data = gh.read_json("data/recipients.json") or {}
    return {"recipients": data.get("recipients", []), "total": len(data.get("recipients", []))}


@router.post("/")
def add_recipient(body: RecipientCreate, session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    gh = GitHubHelper()
    data = gh.read_json("data/recipients.json") or {"version": 1, "recipients": []}

    if any(r["email"] == body.email for r in data["recipients"]):
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")

    new_id = f"r{len(data['recipients'])+1:03d}"
    data["recipients"].append({
        "id": new_id,
        "name": body.name,
        "email": body.email,
        "department": body.department,
        "active": body.active,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    })
    gh.write_json("data/recipients.json", data, f"admin: 수신자 추가 {body.email}")
    return {"message": "수신자 추가 완료", "id": new_id}


@router.put("/{recipient_id}")
def update_recipient(recipient_id: str, body: RecipientUpdate, session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    gh = GitHubHelper()
    data = gh.read_json("data/recipients.json") or {"version": 1, "recipients": []}

    for r in data["recipients"]:
        if r["id"] == recipient_id:
            if body.name is not None:
                r["name"] = body.name
            if body.department is not None:
                r["department"] = body.department
            if body.active is not None:
                r["active"] = body.active
            gh.write_json("data/recipients.json", data, f"admin: 수신자 수정 {recipient_id}")
            return {"message": "수신자 정보 업데이트 완료"}

    raise HTTPException(status_code=404, detail="수신자를 찾을 수 없습니다.")


@router.delete("/{recipient_id}")
def delete_recipient(recipient_id: str, session_id: str | None = Cookie(default=None)):
    _get_current_user(session_id)
    gh = GitHubHelper()
    data = gh.read_json("data/recipients.json") or {"version": 1, "recipients": []}
    before = len(data["recipients"])
    data["recipients"] = [r for r in data["recipients"] if r["id"] != recipient_id]
    if len(data["recipients"]) == before:
        raise HTTPException(status_code=404, detail="수신자를 찾을 수 없습니다.")
    gh.write_json("data/recipients.json", data, f"admin: 수신자 삭제 {recipient_id}")
    return {"message": "수신자 삭제 완료"}
