"""인증 라우터 — 로그인, 로그아웃, 비밀번호 변경"""

import os
import secrets
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

# scripts 경로에서 github_helper 임포트
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from github_helper import GitHubHelper

router = APIRouter()

# 세션 저장소 (서버 메모리, 재시작 시 초기화 — 재로그인 필요)
_sessions: dict[str, dict] = {}
_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", secrets.token_hex(32))


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


def _get_member(username: str) -> dict | None:
    gh = GitHubHelper()
    data = gh.read_json("data/members.json") or {}
    for m in data.get("members", []):
        if m["username"] == username:
            return m
    return None


def _get_current_user(session_id: str | None) -> dict:
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return _sessions[session_id]


@router.post("/login")
def login(req: LoginRequest, response: Response):
    member = _get_member(req.username)
    if not member:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    pw_hash = member.get("password_hash", "")
    # 초기 placeholder 비밀번호 처리
    if pw_hash == "$2b$12$PLACEHOLDER_CHANGE_ON_FIRST_LOGIN":
        # 초기 로그인: 비밀번호 "admin1234!" 허용
        if req.password != "admin1234!":
            raise HTTPException(status_code=401, detail="초기 비밀번호: admin1234! (첫 로그인 후 반드시 변경)")
    else:
        if not bcrypt.checkpw(req.password.encode(), pw_hash.encode()):
            raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    session_id = secrets.token_hex(32)
    _sessions[session_id] = {
        "username": member["username"],
        "role": member.get("role", "editor"),
        "email": member.get("email", ""),
        "logged_in_at": datetime.now(timezone.utc).isoformat(),
    }
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,  # 7일
    )
    return {"message": "로그인 성공", "role": member.get("role", "editor")}


@router.post("/logout")
def logout(response: Response, session_id: str | None = Cookie(default=None)):
    if session_id and session_id in _sessions:
        del _sessions[session_id]
    response.delete_cookie("session_id")
    return {"message": "로그아웃 완료"}


@router.get("/me")
def me(session_id: str | None = Cookie(default=None)):
    user = _get_current_user(session_id)
    return {"username": user["username"], "role": user["role"]}


@router.put("/password")
def change_password(
    req: PasswordChangeRequest,
    session_id: str | None = Cookie(default=None),
):
    user = _get_current_user(session_id)
    member = _get_member(user["username"])
    if not member:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")

    pw_hash = member.get("password_hash", "")
    if pw_hash == "$2b$12$PLACEHOLDER_CHANGE_ON_FIRST_LOGIN":
        if req.current_password != "admin1234!":
            raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    elif not bcrypt.checkpw(req.current_password.encode(), pw_hash.encode()):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="새 비밀번호는 8자 이상이어야 합니다.")

    new_hash = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt(12)).decode()

    gh = GitHubHelper()
    members_data = gh.read_json("data/members.json") or {}
    for m in members_data.get("members", []):
        if m["username"] == user["username"]:
            m["password_hash"] = new_hash
            m.pop("note", None)
            break
    gh.write_json("data/members.json", members_data, "auth: 비밀번호 변경")
    return {"message": "비밀번호가 변경되었습니다."}
