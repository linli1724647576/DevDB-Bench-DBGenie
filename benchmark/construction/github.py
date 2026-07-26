from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from dbgenie.core.config import GitHubConfig


@dataclass(frozen=True)
class RepositoryMetadata:
    full_name: str
    html_url: str = ""
    description: str = ""
    topics: list[str] = field(default_factory=list)
    license_spdx_id: str = ""
    fork: bool = False
    is_template: bool = False
    archived: bool = False
    disabled: bool = False
    stargazers_count: int = 0
    forks_count: int = 0
    contributors_count: int = 0
    pushed_at: str = ""
    default_branch: str = "main"


@dataclass(frozen=True)
class RepositoryFile:
    path: str
    content: str
    sha: str = ""
    size: int = 0


@dataclass(frozen=True)
class CodeSearchItem:
    full_name: str
    path: str
    html_url: str = ""


class GitHubClient:
    """Small GitHub REST client used by the repository screening pipeline.

    The token is allowed to be empty for unauthenticated development, but a
    token is recommended for screening because repository search and tree
    inspection quickly hit unauthenticated rate limits.
    """

    API_ROOT = "https://api.github.com"

    def __init__(self, config: GitHubConfig) -> None:
        self.config = config

    def search_repositories(
        self,
        query: str,
        page: int = 1,
        per_page: int | None = None,
    ) -> list[RepositoryMetadata]:
        payload = self._request_json(
            "GET",
            "/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "page": page,
                "per_page": per_page or self.config.per_page,
            },
        )
        return [self._repo_from_json(item) for item in payload.get("items", [])]

    def search_code_repositories(
        self,
        query: str,
        page: int = 1,
        per_page: int | None = None,
    ) -> list[str]:
        payload = self._request_json(
            "GET",
            "/search/code",
            params={
                "q": query,
                "page": page,
                "per_page": per_page or self.config.per_page,
            },
        )
        full_names = []
        for item in payload.get("items", []):
            repository = item.get("repository") or {}
            full_name = str(repository.get("full_name") or "")
            if full_name:
                full_names.append(full_name)
        return full_names

    def search_code_items(
        self,
        query: str,
        page: int = 1,
        per_page: int | None = None,
    ) -> list[CodeSearchItem]:
        payload = self._request_json(
            "GET",
            "/search/code",
            params={
                "q": query,
                "page": page,
                "per_page": per_page or self.config.per_page,
            },
        )
        items = []
        for item in payload.get("items", []):
            repository = item.get("repository") or {}
            full_name = str(repository.get("full_name") or "")
            path = str(item.get("path") or "")
            if full_name and path:
                items.append(
                    CodeSearchItem(
                        full_name=full_name,
                        path=path,
                        html_url=str(item.get("html_url") or ""),
                    )
                )
        return items

    def get_repository(self, full_name: str, include_contributors: bool = False) -> RepositoryMetadata:
        payload = self._request_json("GET", f"/repos/{full_name}")
        repo = self._repo_from_json(payload)
        contributors_count = self.count_contributors(full_name) if include_contributors else 0
        return RepositoryMetadata(
            **{
                **repo.__dict__,
                "contributors_count": contributors_count,
            }
        )

    def list_tree_paths(self, full_name: str, ref: str | None = None) -> list[str]:
        if ref is None:
            repo = self.get_repository(full_name)
            tree_ref = repo.default_branch
        else:
            tree_ref = ref
        payload = self._request_json(
            "GET",
            f"/repos/{full_name}/git/trees/{urllib.parse.quote(tree_ref, safe='')}",
            params={"recursive": "1"},
        )
        return [
            item["path"]
            for item in payload.get("tree", [])
            if item.get("type") == "blob" and item.get("path")
        ]

    def download_file(self, full_name: str, path: str, ref: str | None = None) -> RepositoryFile:
        encoded_path = urllib.parse.quote(path, safe="/")
        params = {"ref": ref} if ref else None
        payload = self._request_json(
            "GET",
            f"/repos/{full_name}/contents/{encoded_path}",
            params=params,
        )
        if isinstance(payload, list):
            raise GitHubAPIError(f"Path is a directory, not a file: {path}")
        content = payload.get("content", "")
        encoding = payload.get("encoding", "")
        if encoding == "base64":
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        else:
            decoded = str(content)
        return RepositoryFile(
            path=path,
            content=decoded,
            sha=str(payload.get("sha", "")),
            size=int(payload.get("size", 0)),
        )

    def count_contributors(self, full_name: str) -> int:
        try:
            response = self._request(
                "GET",
                f"/repos/{full_name}/contributors",
                params={"per_page": 1, "anon": "true"},
            )
        except GitHubAPIError:
            return 0
        link = response.headers.get("Link", "")
        if 'rel="last"' not in link:
            payload = json.loads(response.read().decode("utf-8"))
            return len(payload)
        for part in link.split(","):
            if 'rel="last"' not in part:
                continue
            if "<" in part and ">" in part:
                url = part.split("<", 1)[1].split(">", 1)[0]
                parsed = urllib.parse.urlparse(url)
                query = urllib.parse.parse_qs(parsed.query)
                page_values = query.get("page", [])
                page_value = page_values[0] if page_values else ""
                try:
                    return int(page_value)
                except ValueError:
                    return 0
        return 0

    def _request_json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = self._request(method, path, params=params)
        return json.loads(response.read().decode("utf-8"))

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> urllib.response.addinfourl:
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        request = urllib.request.Request(
            f"{self.API_ROOT}{path}{query}",
            method=method,
            headers=self._headers(),
        )
        try:
            return urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="ignore")
            raise GitHubAPIError(f"GitHub API error {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"GitHub API request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "dbgenie",
        }
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    @staticmethod
    def _repo_from_json(data: dict[str, Any]) -> RepositoryMetadata:
        license_data = data.get("license") or {}
        return RepositoryMetadata(
            full_name=str(data.get("full_name", "")),
            html_url=str(data.get("html_url", "")),
            description=str(data.get("description") or ""),
            topics=list(data.get("topics") or []),
            license_spdx_id=str(license_data.get("spdx_id") or ""),
            fork=bool(data.get("fork", False)),
            is_template=bool(data.get("is_template", False)),
            archived=bool(data.get("archived", False)),
            disabled=bool(data.get("disabled", False)),
            stargazers_count=int(data.get("stargazers_count", 0)),
            forks_count=int(data.get("forks_count", 0)),
            pushed_at=str(data.get("pushed_at") or ""),
            default_branch=str(data.get("default_branch") or "main"),
        )


class GitHubAPIError(RuntimeError):
    pass
