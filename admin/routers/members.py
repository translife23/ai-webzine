"""멤버 관리 라우터"""

import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper
from routers.auth import _get_current_user

import bcrypt

router = APIRouter()


class MemberCreate(BaseModel):
    name: str = ""
    username: str
    email: str = ""
    initial_password: str = "admin1234!"


class MemberUpdate(BaseModel):
    email: str | None = None
    role: str | None = None


@router.get("/")
def list_members(session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한 필요")
    gh = GitHubHelper()
    data = gh.read_json("data/members.json") or {}
    members = [
        {k: v for k, v in m.items() if k != "password_hash"}
        for m in data.get("members", [])
    ]
    return {"members": members}


@router.post("/")
def create_member(body: MemberCreate, session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한 필요")
    gh = GitHubHelper()
    data = gh.read_json("data/members.json") or {"version": 1, "members": []}

    if any(m["username"] == body.username for m in data["members"]):
        raise HTTPException(status_code=409, detail="이미 존재하는 아이디입니다.")

    new_id = f"m{len(data['members'])+1:03d}"
    pw_hash = bcrypt.hashpw(body.initial_password.encode(), bcrypt.gensalt(12)).decode()
    data["members"].append({
        "id": new_id,
        "name": body.name,
        "username": body.username,
        "password_hash": pw_hash,
        "role": "member",
        "email": body.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    gh.write_json("data/members.json", data, f"admin: 멤버 추가 {body.username}")
    return {"message": f"멤버 {body.username} 추가 완료", "id": new_id}


@router.delete("/{member_id}")
def delete_member(member_id: str, session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한 필요")

    gh = GitHubHelper()
    data = gh.read_json("data/members.json") or {"version": 1, "members": []}
    before = len(data["members"])
    data["members"] = [m for m in data["members"] if m["id"] != member_id]
    if len(data["members"]) == before:
        raise HTTPException(status_code=404, detail="멤버를 찾을 수 없습니다.")
    gh.write_json("data/members.json", data, f"admin: 멤버 삭제 {member_id}")
    return {"message": "멤버 삭제 완료"}
