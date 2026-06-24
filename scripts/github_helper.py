"""
GitHub 저장소 읽기/쓰기 헬퍼 — 로컬 git 저장소를 통해 파일을 관리한다.

Anthropic Cloud 환경에서는 GitHub API 직접 호출이 차단되므로
로컬 파일 I/O + git commit + git push 방식을 사용한다.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any


class GitHubHelper:
    def __init__(self) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPO")
        if not token or not repo_name:
            raise EnvironmentError("GITHUB_TOKEN, GITHUB_REPO 환경 변수가 필요합니다.")
        self._repo_root = Path(__file__).parent.parent
        self._repo_name = repo_name
        self._token = token

    def read_json(self, path: str) -> dict | None:
        """파일을 읽어 dict로 반환한다. 없으면 None."""
        full = self._repo_root / path
        if not full.exists():
            return None
        try:
            return json.loads(full.read_text(encoding="utf-8"))
        except Exception:
            return None

    def write_json(self, path: str, data: dict, message: str | None = None) -> None:
        """dict를 JSON으로 직렬화하여 저장하고 git commit한다."""
        full = self._repo_root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._git_commit(path, message or f"auto: update {path}")

    def read_text(self, path: str) -> str | None:
        """텍스트 파일을 읽어 문자열로 반환한다. 없으면 None."""
        full = self._repo_root / path
        if not full.exists():
            return None
        try:
            return full.read_text(encoding="utf-8")
        except Exception:
            return None

    def write_text(self, path: str, text: str, message: str | None = None) -> None:
        """텍스트를 파일로 저장하고 git commit한다."""
        full = self._repo_root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(text, encoding="utf-8")
        self._git_commit(path, message or f"auto: update {path}")

    def write_html(self, path: str, html: str, message: str | None = None) -> None:
        """HTML 파일을 저장한다."""
        self.write_text(path, html, message)

    def list_dir(self, path: str) -> list[str]:
        """디렉토리 내 항목 이름 목록을 반환한다. 없으면 빈 리스트."""
        full = self._repo_root / path
        if not full.exists() or not full.is_dir():
            return []
        return [p.name for p in full.iterdir()]

    def path_exists(self, path: str) -> bool:
        """파일/디렉토리가 존재하는지 확인한다."""
        return (self._repo_root / path).exists()

    def push(self) -> None:
        """모든 커밋을 원격 저장소에 푸시한다."""
        result = subprocess.run(
            ["git", "push", "-u", "origin", "HEAD"],
            cwd=self._repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git push 실패: {result.stderr}")
        print(f"[GitHubHelper] push 완료: {result.stdout.strip() or result.stderr.strip()}")

    def _git_commit(self, path: str, message: str) -> None:
        """단일 파일을 git add 후 commit한다."""
        subprocess.run(
            ["git", "add", path],
            cwd=self._repo_root,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self._repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # 변경 사항 없으면 커밋 건너뜀
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                pass
            else:
                raise RuntimeError(f"git commit 실패: {result.stderr}")
