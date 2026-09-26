"""Provider-neutral definitions and registration for Thymis agent tools."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from pydantic import BaseModel, ConfigDict

JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class ToolArguments(BaseModel):
    """Base model for arguments accepted by an agent tool."""

    model_config = ConfigDict(extra="forbid")


class ToolDefinition(BaseModel):
    """A provider-neutral function-tool definition.

    ``input_schema`` can be passed directly to an LLM SDK's function adapter.
    """

    name: str
    description: str
    input_schema: dict[str, Any]


class UnknownToolError(ValueError):
    """Raised when a caller asks for a tool that is not registered."""


@dataclass(frozen=True)
class ToolMetadata:
    """Static metadata attached to a decorated tool handler."""

    name: str
    description: str
    arguments_type: type[ToolArguments]


ToolHandler = Callable[[ToolArguments], Awaitable[JSONValue]]


@dataclass(frozen=True)
class RegisteredTool:
    """A validated tool definition bound to one toolbox instance."""

    metadata: ToolMetadata
    handler: ToolHandler

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.metadata.name,
            description=self.metadata.description,
            input_schema=self.metadata.arguments_type.model_json_schema(),
        )

    async def invoke(self, arguments: Mapping[str, Any] | None) -> JSONValue:
        parsed_arguments = self.metadata.arguments_type.model_validate(arguments or {})
        return await self.handler(parsed_arguments)


def tool(
    arguments_type: type[ToolArguments],
    description: str,
    *,
    name: str | None = None,
):
    """Mark an async toolbox method as an agent-callable tool.

    The decorator keeps tool metadata next to the implementation, so adding a
    tool does not require updating a separate registry by hand.
    """

    def decorate(handler: ToolHandler) -> ToolHandler:
        metadata = ToolMetadata(
            name=name or handler.__name__,
            description=description,
            arguments_type=arguments_type,
        )
        setattr(handler, "__thymis_tool__", metadata)
        return handler

    return decorate


def collect_tools(instance: object) -> dict[str, RegisteredTool]:
    """Collect decorated methods in source order, including inherited tools."""

    registered: dict[str, RegisteredTool] = {}
    for cls in reversed(type(instance).__mro__):
        for attribute_name, candidate in cls.__dict__.items():
            metadata = getattr(candidate, "__thymis_tool__", None)
            if metadata is None:
                continue
            handler = cast(ToolHandler, getattr(instance, attribute_name))
            registered[metadata.name] = RegisteredTool(metadata, handler)
    return registered


__all__ = [
    "JSONValue",
    "RegisteredTool",
    "ToolArguments",
    "ToolDefinition",
    "UnknownToolError",
    "collect_tools",
    "tool",
]
