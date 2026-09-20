from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Mapping, Sequence
from typing import Any

from autogen_agentchat.agents import AssistantAgent, BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_core import CancellationToken

from .jsonutil import SchemaAgentJSONError, parse_json_object


JSONValidator = Callable[[dict[str, Any]], None]


class RetryingJSONAgent(BaseChatAgent):
    """Keep SchemaAgent's agent behavior while retrying malformed JSON once."""

    def __init__(
        self,
        delegate: AssistantAgent,
        *,
        validator: JSONValidator,
        on_format_retry: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(name=delegate.name, description=delegate.description)
        self._delegate = delegate
        self._validator = validator
        self._on_format_retry = on_format_retry
        self.format_retry_count = 0

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return self._delegate.produced_message_types

    async def on_messages(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> Response:
        first = await self._delegate.on_messages(messages, cancellation_token)
        try:
            self._validate_response(first)
            return first
        except SchemaAgentJSONError as first_error:
            self.format_retry_count += 1
            if self._on_format_retry is not None:
                self._on_format_retry(self.name)
            retry = await self._delegate.on_messages(
                [
                    TextMessage(
                        source="SchemaAgentFormatValidator",
                        content=(
                            f"Your previous response was invalid: {first_error}. "
                            "Return exactly one valid JSON object matching your required "
                            "output shape, with no Markdown or explanation."
                        ),
                    )
                ],
                cancellation_token,
            )
            try:
                self._validate_response(retry)
            except SchemaAgentJSONError as retry_error:
                raise SchemaAgentJSONError(
                    f"{self.name} returned invalid JSON after one format retry: {retry_error}"
                ) from retry_error
            inner_messages = list(first.inner_messages or [])
            inner_messages.append(first.chat_message)
            inner_messages.extend(retry.inner_messages or [])
            return Response(
                chat_message=retry.chat_message,
                inner_messages=inner_messages,
            )

    def _validate_response(self, response: Response) -> None:
        if not isinstance(response.chat_message, TextMessage):
            raise SchemaAgentJSONError("response is not textual")
        payload = parse_json_object(response.chat_message.content)
        try:
            self._validator(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise SchemaAgentJSONError(str(exc)) from exc

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        self.format_retry_count = 0
        await self._delegate.on_reset(cancellation_token)

    async def save_state(self) -> Mapping[str, Any]:
        return await self._delegate.save_state()

    async def load_state(self, state: Mapping[str, Any]) -> None:
        await self._delegate.load_state(state)

    async def close(self) -> None:
        await self._delegate.close()


class SourceFilteringAgent(BaseChatAgent):
    """Filter messages before a nested AutoGen agent or team sees them."""

    def __init__(self, delegate: BaseChatAgent, *, sources: set[str]) -> None:
        super().__init__(name=delegate.name, description=delegate.description)
        self._delegate = delegate
        self._sources = sources

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return self._delegate.produced_message_types

    async def on_messages(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> Response:
        response: Response | None = None
        async for item in self.on_messages_stream(messages, cancellation_token):
            if isinstance(item, Response):
                response = item
        if response is None:
            raise RuntimeError(f"{self.name} did not produce a response")
        return response

    async def on_messages_stream(
        self,
        messages: Sequence[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        filtered = [message for message in messages if message.source in self._sources]
        async for item in self._delegate.on_messages_stream(filtered, cancellation_token):
            yield item

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        await self._delegate.on_reset(cancellation_token)

    async def save_state(self) -> Mapping[str, Any]:
        return await self._delegate.save_state()

    async def load_state(self, state: Mapping[str, Any]) -> None:
        await self._delegate.load_state(state)

    async def close(self) -> None:
        await self._delegate.close()


def require_fields(*fields: str) -> JSONValidator:
    def validate(payload: dict[str, Any]) -> None:
        missing = [field for field in fields if field not in payload]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

    return validate


def validate_design(payload: dict[str, Any]) -> None:
    require_fields("question", "output")(payload)
    if not isinstance(payload["question"], str) or not isinstance(payload["output"], dict):
        raise ValueError("question must be a string and output must be an object")
