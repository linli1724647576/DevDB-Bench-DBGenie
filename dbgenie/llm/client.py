from __future__ import annotations

import http.client
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from dbgenie.core.config import LLMConfig


LLM_RETRY_BACKOFF_SECONDS = (30, 90, 180)
LLMAttemptErrorCallback = Callable[["LLMRequestError", dict[str, Any], int], None]


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        attempts: int = 0,
        status_code: int | None = None,
        detail: str = "",
        transient: bool = True,
        stage: str = "",
        kind: str = "",
        request_metadata: dict[str, Any] | None = None,
        response_headers: dict[str, str] | None = None,
        attempt_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.status_code = status_code
        self.detail = detail
        self.transient = transient
        self.stage = stage
        self.kind = kind
        self.request_metadata = request_metadata or {}
        self.response_headers = response_headers or {}
        self.attempt_errors = attempt_errors or []
        self.attempt_errors_reported = False


class LLMClient:
    """Minimal replaceable LLM client.

    The base URL and API key are intentionally allowed to be empty so the
    benchmark can be developed without external model access.
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def is_configured(self) -> bool:
        return bool(self.config.base_url and self.config.api_key and self.config.model)

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.config.name,
            "provider": self.config.provider,
            "base_url": self.config.base_url,
            "request_url": _chat_completions_url(self.config.base_url),
            "model": self.config.model,
            "timeout_seconds": self.config.timeout_seconds,
            "temperature": self.config.temperature,
            "stream": self.config.stream,
            "max_retries": self.config.max_retries,
            "configured": self.is_configured(),
        }

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        stage: str = "",
        on_attempt_error: LLMAttemptErrorCallback | None = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError(
                "LLM client is not configured. Fill llm.base_url, llm.api_key, "
                "and llm.model before calling external models."
            )
        if self.config.provider != "openai_compatible":
            raise RuntimeError(
                f"Unsupported LLM provider '{self.config.provider}'. "
                "V1 supports provider='openai_compatible'."
            )
        payload = {
            "model": self.config.model,
            "messages": [message.__dict__ for message in messages],
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        if self.config.stream:
            payload["stream"] = True
        return self._complete_with_retries(
            payload,
            stage=stage,
            on_attempt_error=on_attempt_error,
        )

    def _complete_with_retries(
        self,
        payload: dict[str, Any],
        *,
        stage: str = "",
        on_attempt_error: LLMAttemptErrorCallback | None = None,
    ) -> str:
        attempts = len(LLM_RETRY_BACKOFF_SECONDS) + 1
        last_error: LLMRequestError | None = None
        attempt_errors: list[dict[str, Any]] = []
        request_metadata = self._request_metadata(payload)
        for attempt in range(1, attempts + 1):
            try:
                if self.config.stream:
                    return self._post_stream_once(payload, attempt=attempt)
                body = self._post_once(payload, attempt=attempt)
                return _response_content(
                    body,
                    attempt=attempt,
                    request_metadata=request_metadata,
                )
            except LLMRequestError as exc:
                last_error = exc
                if stage and not exc.stage:
                    exc.stage = stage
                exc.request_metadata = exc.request_metadata or request_metadata
                record = _attempt_error_record(exc, attempt=attempt)
                if attempt < attempts and exc.transient:
                    record["next_backoff_seconds"] = LLM_RETRY_BACKOFF_SECONDS[attempt - 1]
                attempt_errors.append(record)
                exc.attempt_errors = list(attempt_errors)
                if on_attempt_error is not None:
                    try:
                        on_attempt_error(exc, record, attempts)
                    except Exception:
                        pass
                    else:
                        exc.attempt_errors_reported = True
                if attempt == attempts or not exc.transient:
                    raise
            time.sleep(LLM_RETRY_BACKOFF_SECONDS[attempt - 1])
        if last_error is not None:
            last_error.attempt_errors = list(attempt_errors)
            last_error.request_metadata = last_error.request_metadata or request_metadata
            raise last_error
        raise LLMRequestError(
            _request_error_message("unknown error", attempts, ""),
            attempts=attempts,
            kind="unknown_error",
            request_metadata=request_metadata,
            transient=True,
        )

    def _post_once(self, payload: dict[str, Any], *, attempt: int) -> str:
        request_metadata = self._request_metadata(payload)
        request = self._request(payload, stream=False)
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMRequestError(
                _request_error_message(
                    f"HTTP {exc.code}",
                    attempt,
                    detail,
                ),
                attempts=attempt,
                status_code=exc.code,
                detail=detail,
                kind=f"HTTP {exc.code}",
                request_metadata=request_metadata,
                response_headers={str(k): str(v) for k, v in (exc.headers or {}).items()},
                transient=True,
            ) from exc
        except (
            TimeoutError,
            urllib.error.URLError,
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            ConnectionError,
        ) as exc:
            kind = type(exc).__name__
            raise LLMRequestError(
                _request_error_message(kind, attempt, str(exc)),
                attempts=attempt,
                detail=str(exc),
                kind=kind,
                request_metadata=request_metadata,
                transient=True,
            ) from exc

    def _post_stream_once(self, payload: dict[str, Any], *, attempt: int) -> str:
        request_metadata = self._request_metadata(payload)
        request = self._request(payload, stream=True)
        content_parts: list[str] = []
        raw_events: list[str] = []
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    raw_events.append(data)
                    event = _parse_stream_event(
                        data,
                        attempt=attempt,
                        request_metadata=request_metadata,
                    )
                    if "error" in event:
                        raise LLMRequestError(
                            f"LLM stream returned an error after {attempt} attempt(s).",
                            attempts=attempt,
                            detail=json.dumps(event["error"], ensure_ascii=False),
                            kind="stream_error_event",
                            request_metadata=request_metadata,
                            transient=True,
                        )
                    choices = event.get("choices") or []
                    if not choices or not isinstance(choices[0], dict):
                        continue
                    choice = choices[0]
                    delta = choice.get("delta") or {}
                    if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                        content_parts.append(delta["content"])
                        continue
                    message = choice.get("message") or {}
                    if isinstance(message, dict) and isinstance(message.get("content"), str):
                        content_parts.append(message["content"])
                content = "".join(content_parts)
                if not content.strip():
                    raise LLMRequestError(
                        f"LLM stream did not contain message content after {attempt} attempt(s).",
                        attempts=attempt,
                        detail="\n".join(raw_events),
                        kind="missing_stream_content",
                        request_metadata=request_metadata,
                        transient=True,
                    )
                return content
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMRequestError(
                _request_error_message(
                    f"HTTP {exc.code}",
                    attempt,
                    detail,
                ),
                attempts=attempt,
                status_code=exc.code,
                detail=detail,
                kind=f"HTTP {exc.code}",
                request_metadata=request_metadata,
                response_headers={str(k): str(v) for k, v in (exc.headers or {}).items()},
                transient=True,
            ) from exc
        except (
            TimeoutError,
            urllib.error.URLError,
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            ConnectionError,
        ) as exc:
            kind = type(exc).__name__
            detail = str(exc)
            if content_parts or raw_events:
                detail = (
                    f"{detail}\n\npartial_content={''.join(content_parts)}"
                    f"\n\nraw_stream_events={chr(10).join(raw_events)}"
                )
            raise LLMRequestError(
                _request_error_message(kind, attempt, detail),
                attempts=attempt,
                detail=detail,
                kind=kind,
                request_metadata=request_metadata,
                transient=True,
            ) from exc

    def _request(self, payload: dict[str, Any], *, stream: bool) -> urllib.request.Request:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dbgenie/0.1",
        }
        if stream:
            headers["Accept"] = "text/event-stream"
        return urllib.request.Request(
            _chat_completions_url(self.config.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def _request_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        messages = payload.get("messages") or []
        message_summaries = []
        total_chars = 0
        if isinstance(messages, list):
            for index, message in enumerate(messages):
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                content_text = json.dumps(content, ensure_ascii=False) if not isinstance(content, str) else content
                content_chars = len(content_text)
                total_chars += content_chars
                message_summaries.append(
                    {
                        "index": index,
                        "role": str(message.get("role") or ""),
                        "content_chars": content_chars,
                    }
                )
        return {
            "name": self.config.name,
            "provider": self.config.provider,
            "request_url": _chat_completions_url(self.config.base_url),
            "model": self.config.model,
            "timeout_seconds": self.config.timeout_seconds,
            "temperature": self.config.temperature,
            "stream": bool(payload.get("stream")),
            "max_retries": self.config.max_retries,
            "message_count": len(messages) if isinstance(messages, list) else 0,
            "message_chars": total_chars,
            "messages": message_summaries,
        }


def _chat_completions_url(base_url: str) -> str:
    clean = base_url.rstrip("/")
    if clean.endswith("/chat/completions"):
        return clean
    return f"{clean}/chat/completions"


def _request_error_message(kind: str, attempts: int, detail: str) -> str:
    suffix = f": {detail}" if detail else ""
    return f"LLM request failed with {kind} after {attempts} attempt(s){suffix}"


def _parse_stream_event(
    data: str,
    *,
    attempt: int,
    request_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        event = json.loads(data)
    except json.JSONDecodeError as exc:
        raise LLMRequestError(
            f"LLM stream event was not valid JSON after {attempt} attempt(s).",
            attempts=attempt,
            detail=data,
            kind="invalid_stream_event",
            request_metadata=request_metadata,
            transient=True,
        ) from exc
    if not isinstance(event, dict):
        raise LLMRequestError(
            f"LLM stream event was not a JSON object after {attempt} attempt(s).",
            attempts=attempt,
            detail=data,
            kind="invalid_stream_event",
            request_metadata=request_metadata,
            transient=True,
        )
    return event


def _response_content(
    body: str,
    *,
    attempt: int,
    request_metadata: dict[str, Any] | None = None,
) -> str:
    try:
        data: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LLMRequestError(
            f"LLM response body was not valid JSON after {attempt} attempt(s).",
            attempts=attempt,
            detail=body,
            kind="invalid_json_response",
            request_metadata=request_metadata,
            transient=True,
        ) from exc
    choices = data.get("choices") or []
    if not choices:
        raise LLMRequestError(
            f"LLM response did not contain choices after {attempt} attempt(s).",
            attempts=attempt,
            detail=body,
            kind="missing_choices",
            request_metadata=request_metadata,
            transient=True,
        )
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            str(item.get("text") or "")
            for item in content
            if isinstance(item, dict)
        )
    if not isinstance(content, str) or not content.strip():
        raise LLMRequestError(
            f"LLM response did not contain message.content after {attempt} attempt(s).",
            attempts=attempt,
            detail=body,
            kind="missing_message_content",
            request_metadata=request_metadata,
            transient=True,
        )
    return content


def _attempt_error_record(error: LLMRequestError, *, attempt: int) -> dict[str, Any]:
    detail = str(error.detail or "")
    return {
        "attempt": attempt,
        "error_type": type(error).__name__,
        "kind": error.kind,
        "status_code": error.status_code,
        "transient": error.transient,
        "message": str(error),
        "detail": detail,
        "detail_chars": len(detail),
        "response_headers": dict(error.response_headers or {}),
    }
