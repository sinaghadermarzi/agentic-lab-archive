"""A deterministic teaching double of the Agent2Agent (A2A) protocol.

A2A standardizes the boundary *between* agents: discovery via Agent Cards,
task lifecycle, and message/artifact exchange between peers that stay opaque
to each other. This module implements a small self-contained subset of the v1.0
JSON-RPC binding — ``SendMessage``, ``GetTask``, ``CancelTask``, the
``TASK_STATE_*`` lifecycle, and well-known-URI discovery — so every wire
message stays inspectable without a network or an SDK.

Spec: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

PROTOCOL_VERSION = "1.0"
WELL_KNOWN_PATH = "/.well-known/agent-card.json"

SUBMITTED = "TASK_STATE_SUBMITTED"
WORKING = "TASK_STATE_WORKING"
INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
COMPLETED = "TASK_STATE_COMPLETED"
FAILED = "TASK_STATE_FAILED"
CANCELED = "TASK_STATE_CANCELED"

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
TASK_NOT_FOUND = -32001
TASK_NOT_CANCELABLE = -32002

TERMINAL_STATES = {COMPLETED, FAILED, CANCELED}


@dataclass
class ToyAgentCard:
    """Simplified Agent Card: what a peer publishes at the well-known URI."""

    name: str
    description: str
    url: str
    skills: list[dict[str, str]] = field(default_factory=list)
    version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "supportedInterfaces": [{"url": self.url, "protocolBinding": "JSONRPC"}],
            "capabilities": {"streaming": False},
            "skills": self.skills,
        }


class ToyA2AServer:
    """One remote agent: an Agent Card plus a handler behind the task lifecycle.

    ``handler`` receives the user's text and returns either
    ``{"artifact": text}`` to complete the task or
    ``{"input_required": question}`` to pause it for another turn.
    """

    def __init__(self, card: ToyAgentCard, handler: Callable[[str], Mapping[str, Any]]) -> None:
        self.card = card
        self.handler = handler
        self._tasks: dict[str, dict[str, Any]] = {}
        self._counter = 0

    def handle(self, message: Mapping[str, Any]) -> dict[str, Any]:
        method = message.get("method", "")
        params = message.get("params", {}) or {}
        handlers = {
            "SendMessage": self._send_message,
            "GetTask": self._get_task,
            "CancelTask": self._cancel_task,
        }
        if method not in handlers:
            return _error(message.get("id"), METHOD_NOT_FOUND, f"method not found: {method}")
        try:
            return _result(message.get("id"), handlers[method](params))
        except _RpcError as exc:
            return _error(message.get("id"), exc.code, str(exc))

    def _send_message(self, params: Mapping[str, Any]) -> dict[str, Any]:
        msg = params.get("message") or {}
        text = " ".join(p.get("text", "") for p in msg.get("parts", []))
        task_id = msg.get("taskId")
        if task_id is None:
            task = self._new_task(msg)
        else:  # follow-up turn on a paused task
            task = self._require_task(task_id)
            if task["status"]["state"] != INPUT_REQUIRED:
                raise _RpcError(INVALID_PARAMS, f"task {task_id} is not awaiting input")
        task["history"].append(msg)
        task["status"] = {"state": WORKING}
        outcome = self.handler(text)
        if "input_required" in outcome:
            task["status"] = {
                "state": INPUT_REQUIRED,
                "update": _agent_message(outcome["input_required"], task["id"]),
            }
        else:
            task["artifacts"].append(
                {
                    "artifactId": f"artifact-{len(task['artifacts']) + 1}",
                    "name": "result",
                    "parts": [{"text": str(outcome["artifact"])}],
                }
            )
            task["status"] = {"state": COMPLETED}
        return {"task": task}

    def _get_task(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {"task": self._require_task(params.get("id"))}

    def _cancel_task(self, params: Mapping[str, Any]) -> dict[str, Any]:
        task = self._require_task(params.get("id"))
        if task["status"]["state"] in TERMINAL_STATES:
            raise _RpcError(TASK_NOT_CANCELABLE, f"task {task['id']} is already terminal")
        task["status"] = {"state": CANCELED}
        return {"task": task}

    def _new_task(self, msg: Mapping[str, Any]) -> dict[str, Any]:
        self._counter += 1
        task = {
            "id": f"task-{self._counter}",
            "contextId": f"ctx-{self._counter}",
            "status": {"state": SUBMITTED},
            "artifacts": [],
            "history": [],
        }
        self._tasks[task["id"]] = task
        return task

    def _require_task(self, task_id: Any) -> dict[str, Any]:
        if task_id not in self._tasks:
            raise _RpcError(TASK_NOT_FOUND, f"unknown task: {task_id!r}")
        return self._tasks[task_id]


class ToyA2ANetwork:
    """An in-memory stand-in for HTTP: URLs resolve to registered servers."""

    def __init__(self) -> None:
        self._servers: dict[str, ToyA2AServer] = {}

    def register(self, server: ToyA2AServer) -> None:
        self._servers[server.card.url] = server

    def fetch_well_known(self, url: str) -> dict[str, Any]:
        return self._server(url).card.to_dict()

    def post(self, url: str, message: Mapping[str, Any]) -> dict[str, Any]:
        return self._server(url).handle(message)

    def _server(self, url: str) -> ToyA2AServer:
        if url not in self._servers:
            raise KeyError(f"no agent at {url!r}")
        return self._servers[url]


@dataclass
class ToyA2AClient:
    """A client-side agent: discovers peers, delegates work, tracks the wire."""

    network: ToyA2ANetwork
    transcript: list[dict[str, Any]] = field(default_factory=list)
    _next_id: int = 1

    def discover(self, url: str) -> dict[str, Any]:
        card = self.network.fetch_well_known(url)
        self.transcript.append({"get": url + WELL_KNOWN_PATH, "response": card})
        return card

    def send_message(self, url: str, text: str, *, task_id: str | None = None) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "ROLE_USER", "parts": [{"text": text}]}
        if task_id is not None:
            message["taskId"] = task_id
        return self.request(url, "SendMessage", {"message": message})["task"]

    def get_task(self, url: str, task_id: str) -> dict[str, Any]:
        return self.request(url, "GetTask", {"id": task_id})["task"]

    def cancel_task(self, url: str, task_id: str) -> dict[str, Any]:
        return self.request(url, "CancelTask", {"id": task_id})["task"]

    def request(self, url: str, method: str, params: Mapping[str, Any]) -> dict[str, Any]:
        message = {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": dict(params)}
        self._next_id += 1
        response = self.network.post(url, message)
        self.transcript.append({"post": url, "request": message, "response": response})
        if "error" in response:
            raise RuntimeError(f"{response['error']['code']}: {response['error']['message']}")
        return response["result"]


class _RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _agent_message(text: str, task_id: str) -> dict[str, Any]:
    return {"role": "ROLE_AGENT", "parts": [{"text": text}], "taskId": task_id}


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
