"""A deterministic teaching double of the Model Context Protocol (MCP).

MCP standardizes the boundary between a host application and the servers
that expose tools, resources, and prompts to it. This module implements a
small, offline subset of the protocol — JSON-RPC 2.0 messages, the
initialize handshake, and the tools/resources/prompts primitives — so the
wire format stays fully inspectable without a network or an SDK.

Spec: https://modelcontextprotocol.io/specification/2025-06-18
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

PROTOCOL_VERSION = "2025-06-18"

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


@dataclass
class ToyTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[Mapping[str, Any]], Any]


@dataclass
class ToyResource:
    uri: str
    name: str
    text: str
    mime_type: str = "text/plain"


@dataclass
class ToyPrompt:
    name: str
    description: str
    template: str


class ToyMCPServer:
    """An in-memory MCP server speaking simplified JSON-RPC 2.0 dictionaries."""

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self._tools: dict[str, ToyTool] = {}
        self._resources: dict[str, ToyResource] = {}
        self._prompts: dict[str, ToyPrompt] = {}

    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable[[Mapping[str, Any]], Any],
    ) -> None:
        self._tools[name] = ToyTool(name, description, input_schema, handler)

    def add_resource(self, uri: str, name: str, text: str, mime_type: str = "text/plain") -> None:
        self._resources[uri] = ToyResource(uri, name, text, mime_type)

    def add_prompt(self, name: str, description: str, template: str) -> None:
        self._prompts[name] = ToyPrompt(name, description, template)

    def handle(self, message: Mapping[str, Any]) -> dict[str, Any] | None:
        """Dispatch one JSON-RPC message. Notifications return ``None``."""

        method = message.get("method", "")
        params = message.get("params", {}) or {}
        if "id" not in message:
            return None  # notifications (e.g. notifications/initialized) get no response
        handlers: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
            "initialize": self._initialize,
            "tools/list": self._tools_list,
            "tools/call": self._tools_call,
            "resources/list": self._resources_list,
            "resources/read": self._resources_read,
            "prompts/list": self._prompts_list,
            "prompts/get": self._prompts_get,
        }
        if method not in handlers:
            return _error(message["id"], METHOD_NOT_FOUND, f"method not found: {method}")
        try:
            return _result(message["id"], handlers[method](params))
        except _ParamError as exc:
            return _error(message["id"], INVALID_PARAMS, str(exc))

    def _initialize(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": self.name, "version": self.version},
        }

    def _tools_list(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "tools": [
                {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
                for t in self._tools.values()
            ]
        }

    def _tools_call(self, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if name not in self._tools:
            raise _ParamError(f"unknown tool: {name!r}")
        try:
            output = self._tools[name].handler(params.get("arguments", {}) or {})
        except Exception as exc:
            # Tool execution failures are results with isError, not protocol errors,
            # so the model can see the failure and decide what to do next.
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        return {"content": [{"type": "text", "text": str(output)}], "isError": False}

    def _resources_list(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "resources": [
                {"uri": r.uri, "name": r.name, "mimeType": r.mime_type}
                for r in self._resources.values()
            ]
        }

    def _resources_read(self, params: Mapping[str, Any]) -> dict[str, Any]:
        uri = params.get("uri")
        if uri not in self._resources:
            raise _ParamError(f"unknown resource: {uri!r}")
        resource = self._resources[uri]
        return {"contents": [{"uri": uri, "mimeType": resource.mime_type, "text": resource.text}]}

    def _prompts_list(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "prompts": [{"name": p.name, "description": p.description} for p in self._prompts.values()]
        }

    def _prompts_get(self, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if name not in self._prompts:
            raise _ParamError(f"unknown prompt: {name!r}")
        prompt = self._prompts[name]
        text = prompt.template.format(**(params.get("arguments", {}) or {}))
        return {
            "description": prompt.description,
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }


@dataclass
class ToyMCPClient:
    """A client bound to one server over an in-memory transport.

    Every request/response pair is appended to ``transcript`` so the raw
    JSON-RPC exchange can be printed and studied.
    """

    server: ToyMCPServer
    transcript: list[dict[str, Any]] = field(default_factory=list)
    _next_id: int = 1

    def connect(self) -> dict[str, Any]:
        """Run the initialize handshake and return the server's capabilities."""

        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "lab-toy-client", "version": "0.1.0"},
            },
        )
        self.notify("notifications/initialized")
        return result

    def request(self, method: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        message = {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": dict(params or {})}
        self._next_id += 1
        response = self.server.handle(message)
        self.transcript.append({"request": message, "response": response})
        if response is not None and "error" in response:
            raise RuntimeError(f"{response['error']['code']}: {response['error']['message']}")
        return response["result"] if response else {}

    def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        message = {"jsonrpc": "2.0", "method": method, "params": dict(params or {})}
        response = self.server.handle(message)
        self.transcript.append({"request": message, "response": response})

    def list_tools(self) -> list[dict[str, Any]]:
        return self.request("tools/list")["tools"]

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self.request("tools/call", {"name": name, "arguments": dict(arguments or {})})

    def read_resource(self, uri: str) -> dict[str, Any]:
        return self.request("resources/read", {"uri": uri})

    def get_prompt(self, name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self.request("prompts/get", {"name": name, "arguments": dict(arguments or {})})


class _ParamError(ValueError):
    pass


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
