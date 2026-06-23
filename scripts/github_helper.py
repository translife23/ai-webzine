"""
GitHub 저장소 읽기/쓰기 헬퍼 — PyGitHub를 통해 JSON/Markdown 파일을 관리한다.

Render.com 무료 티어는 영구 디스크가 없으므로 모든 데이터 파일은 GitHub 저장소에 저장한다.
Claude Code Routine 환경에서는 PyGitHub API 대신 로컬 파일 + git push를 사용한다.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

try:
    from github import Github, GithubException
    _PYGITHUB_AVAILABLE = True
except ImportError:
    _PYGITHUB_AVAILABLE = False


_REPO_ROOT = Path(__file__).parent.parent


class LocalGitHubHelper:
    """로컬 클론 + git commit/push 방식. PyGitHub API 차단 환경에서 사용."""

    def __init__(self) -> None:
        self._root = _REPO_ROOT

    def _path(self, rel: str) -> Path:
        return self._root / rel

    def read_json(self, path: str) -> dict | None:
        p = self._path(path)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def write_json(self, path: str, data: dict, message: str | None = None) -> None:
        p = self._path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        p.write_text(content_str, encoding="utf-8")
        self._commit_and_push(path, message or f"auto: update {path}")

    def read_text(self, path: str) -> str | None:
        p = self._path(path)
        if not p.exists():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return None

    def write_text(self, path: str, text: str, message: str | None = None) -> None:
        p = self._path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        self._commit_and_push(path, message or f"auto: update {path}")

    def write_html(self, path: str, html: str, message: str | None = None) -> None:
        self.write_text(path, html, message)

    def list_dir(self, path: str) -> list[str]:
        p = self._path(path)
        if not p.exists() or not p.is_dir():
            return []
        return [item.name for item in p.iterdir()]

    def path_exists(self, path: str) -> bool:
        return self._path(path).exists()

    def _commit_and_push(self, rel_path: str, message: str) -> None:
        root = str(self._root)
        subprocess.run(["git", "add", rel_path], cwd=root, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=root
        )
        if result.returncode == 0:
            return  # 변경사항 없음
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=root,
            check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "Routine C", "GIT_AUTHOR_EMAIL": "routine@ai-webzine",
                 "GIT_COMMITTER_NAME": "Routine C", "GIT_COMMITTER_EMAIL": "routine@ai-webzine"},
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=root,
            check=True,
        )


class GitHubHelper:
    def __init__(self) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPO")
        if not token or not repo_name:
            raise EnvironmentError("GITHUB_TOKEN, GITHUB_REPO 환경 변수가 필요합니다.")

        if _PYGITHUB_AVAILABLE:
            try:
                self._gh = Github(token)
                self._repo = self._gh.get_repo(repo_name)
                self._local = None
                return
            except Exception:
                pass

        # PyGitHub 불가 → 로컬 파일 + git 방식으로 폴백
        print("[GitHubHelper] PyGitHub API 불가 → 로컬 파일 + git 모드")
        self._gh = None
        self._repo = None
        self._local = LocalGitHubHelper()

    def read_json(self, path: str) -> dict | None:
        if self._local:
            return self._local.read_json(path)
        try:
            content = self._repo.get_contents(path)
            return json.loads(content.decoded_content.decode("utf-8"))
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                return None
            raise

    def write_json(self, path: str, data: dict, message: str | None = None) -> None:
        if self._local:
            return self._local.write_json(path, data, message)
        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        commit_msg = message or f"auto: update {path}"
        try:
            from github import GithubException
            existing = self._repo.get_contents(path)
            self._repo.update_file(path, commit_msg, content_str, existing.sha)
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                self._repo.create_file(path, commit_msg, content_str)
            else:
                raise

    def read_text(self, path: str) -> str | None:
        if self._local:
            return self._local.read_text(path)
        try:
            content = self._repo.get_contents(path)
            return content.decoded_content.decode("utf-8")
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                return None
            raise

    def write_text(self, path: str, text: str, message: str | None = None) -> None:
        if self._local:
            return self._local.write_text(path, text, message)
        commit_msg = message or f"auto: update {path}"
        try:
            from github import GithubException
            existing = self._repo.get_contents(path)
            self._repo.update_file(path, commit_msg, text, existing.sha)
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                self._repo.create_file(path, commit_msg, text)
            else:
                raise

    def write_html(self, path: str, html: str, message: str | None = None) -> None:
        self.write_text(path, html, message)

    def list_dir(self, path: str) -> list[str]:
        if self._local:
            return self._local.list_dir(path)
        try:
            from github import GithubException
            contents = self._repo.get_contents(path)
            if isinstance(contents, list):
                return [c.name for c in contents]
            return []
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                return []
            raise

    def path_exists(self, path: str) -> bool:
        if self._local:
            return self._local.path_exists(path)
        try:
            self._repo.get_contents(path)
            return True
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                return False
            raise
