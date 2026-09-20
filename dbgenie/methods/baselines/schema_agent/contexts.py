from __future__ import annotations

from collections.abc import Callable

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage


class FilteredChatCompletionContext(ChatCompletionContext):
    def __init__(self, predicate: Callable[[LLMMessage], bool]) -> None:
        super().__init__()
        self._predicate = predicate

    async def get_messages(self) -> list[LLMMessage]:
        return [message for message in self._messages if self._predicate(message)]


def source_or_recipient_context(*names: str) -> FilteredChatCompletionContext:
    allowed = set(names)

    def include(message: LLMMessage) -> bool:
        if type(message).__name__ == "FunctionExecutionResultMessage":
            return True
        source = str(getattr(message, "source", ""))
        content = str(getattr(message, "content", ""))
        if source == "SchemaAgentFormatValidator":
            return True
        return source in allowed or any(name in content for name in allowed)

    return FilteredChatCompletionContext(include)


def source_context(*names: str) -> FilteredChatCompletionContext:
    allowed = set(names)
    return FilteredChatCompletionContext(
        lambda message: str(getattr(message, "source", "")) in allowed
        or str(getattr(message, "source", "")) == "SchemaAgentFormatValidator"
        or type(message).__name__ == "FunctionExecutionResultMessage"
    )
