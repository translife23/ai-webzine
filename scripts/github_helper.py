"""
GitHub 저장소 읽기/쓰기 헬퍼 — PyGitHub를 통해 JSON/Markdown 파일을 관리한다.

Render.com 무료 티어는 영구 디스크가 없으므로 모든 데이터 파일은 GitHub 저장소에 저장한다.
"""

import json
import os
import base64
from typing import Any

from github import Github, GithubException


class GitHubHelper:
    def __init__(self) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPO")
        if not token or not repo_name:
            raise EnvironmentError("GITHUB_TOKEN, GITHUB_REPO 환경 변수가 필요합니다.")
        self._gh = Github(token)
        self._repo = self._gh.get_repo(repo_name)

    def read_json(self, path: str) -> dict | None:
        """저장소의 JSON 파일을 읽어 dict로 반환한다. 없으면 None."""
        try:
            content = self._repo.get_contents(path)
            return json.loads(content.decoded_content.decode("utf-8"))
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def write_json(self, path: str, data: dict, message: str | None = None) -> None:
        """dict를 JSON으로 직렬화하여 저장소에 저장(생성 또는 업데이트)한다."""
        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        commit_msg = message or f"auto: update {path}"
        try:
            existing = self._repo.get_contents(path)
            self._repo.update_file(path, commit_msg, content_str, existing.sha)
        except GithubException as e:
            if e.status == 404:
                self._repo.create_file(path, commit_msg, content_str)
            else:
                raise

    def read_text(self, path: str) -> str | None:
        """저장소의 텍스트 파일을 읽어 문자열로 반환한다. 없으면 None."""
        try:
            content = self._repo.get_contents(path)
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def write_text(self, path: str, text: str, message: str | None = None) -> None:
        """텍스트를 저장소 파일로 저장(생성 또는 업데이트)한다."""
        commit_msg = message or f"auto: update {path}"
        try:
            existing = self._repo.get_contents(path)
            self._repo.update_file(path, commit_msg, text, existing.sha)
        except GithubException as e:
            if e.status == 404:
                self._repo.create_file(path, commit_msg, text)
            else:
                raise

    def write_html(self, path: str, html: str, message: str | None = None) -> None:
        """HTML 파일을 저장소에 저장한다."""
        self.write_text(path, html, message)

    def path_exists(self, path: str) -> bool:
        """저장소에 파일/디렉토리가 존재하는지 확인한다."""
        try:
            self._repo.get_contents(path)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise
