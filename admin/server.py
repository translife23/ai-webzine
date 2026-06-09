"""
AI 웹진 관리자 서버 — FastAPI

관리자 ID: admin4web
기능: 워크플로 관리, 기사 검토, 기획 주제 입력, 초안 승인, 수신자/멤버 관리
데이터: 모두 GitHub 저장소 JSON 파일로 저장 (Render.com 무료 티어 영구 디스크 없음)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import auth, workflow, members, recipients, topics

app = FastAPI(title="AI 웹진 관리자", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router,       prefix="/api/auth",       tags=["인증"])
app.include_router(workflow.router,   prefix="/api/workflow",   tags=["워크플로"])
app.include_router(members.router,    prefix="/api/members",    tags=["멤버 관리"])
app.include_router(recipients.router, prefix="/api/recipients", tags=["수신자 관리"])
app.include_router(topics.router,     prefix="/api/topics",     tags=["기획 주제"])

# 정적 파일 서빙 (SPA)
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """SPA 라우팅: /api 외 모든 경로는 index.html을 반환한다."""
    return FileResponse(str(_static_dir / "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("ADMIN_PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
