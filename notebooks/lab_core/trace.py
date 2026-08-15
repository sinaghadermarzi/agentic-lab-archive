"""A minimal span tracer for the lab's tool boundary.

Observability tools all stand on the same idea: a *span* records one timed
operation, spans nest into a tree, and exporters ship finished spans to a
UI. This module is that idea with nothing hidden — deterministic structure,
real timings — plus the seam the notebooks instrument: wrap a tools mapping
once and every ``run_tool_loop`` or ``DeepAgent`` call becomes a span tree.

``Sink`` is the exporter boundary. The bundled renderer prints the tree;
``notebooks/obs.py`` provides sinks that bridge the same spans into MLflow
and Arize Phoenix, so nothing here imports anything outside the stdlib.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Mapping, Protocol


@dataclass
class Span:
    name: str
    parent: Span | None = None
    children: list[Span] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    started: float = 0.0
    ended: float = 0.0
    error: str | None = None

    @property
    def duration_ms(self) -> float:
        return 1000 * (self.ended - self.started)


class Sink(Protocol):
    """Exporter boundary: called as each span opens and closes, LIFO-nested."""

    def on_start(self, span: Span) -> None: ...

    def on_end(self, span: Span) -> None: ...


class Tracer:
    """Collects span trees; completed root spans accumulate in ``roots``."""

    def __init__(self, sinks: list[Sink] | None = None) -> None:
        self.sinks = list(sinks or [])
        self.roots: list[Span] = []
        self._stack: list[Span] = []

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        span = Span(name, parent=self._stack[-1] if self._stack else None)
        span.attributes.update(attributes)
        if span.parent is not None:
            span.parent.children.append(span)
        self._stack.append(span)
        span.started = time.perf_counter()
        for sink in self.sinks:
            sink.on_start(span)
        try:
            yield span
        except Exception as exc:
            span.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            span.ended = time.perf_counter()
            self._stack.pop()
            for sink in self.sinks:
                sink.on_end(span)
            if span.parent is None:
                self.roots.append(span)

    def wrap_tools(
        self, tools: Mapping[str, Callable[[Any], Any]]
    ) -> dict[str, Callable[[Any], Any]]:
        """Instrument a tools mapping: every call becomes a span with input/output sizes."""

        def wrap(name: str, fn: Callable[[Any], Any]) -> Callable[[Any], Any]:
            def traced(args: Any) -> Any:
                with self.span(f"tool:{name}", input=str(args)[:120]) as span:
                    observation = fn(args)
                    span.attributes["observation_chars"] = len(str(observation))
                    return observation

            return traced

        return {name: wrap(name, fn) for name, fn in tools.items()}

    def render(self, span: Span | None = None) -> str:
        """Indented tree with latencies — the picture every trace UI draws."""

        if span is None:
            return "\n".join(self.render(root) for root in self.roots)

        def lines(node: Span, depth: int) -> list[str]:
            mark = f"  !! {node.error}" if node.error else ""
            out = [f"{'  ' * depth}{node.name}  [{node.duration_ms:.1f} ms]{mark}"]
            for child in node.children:
                out.extend(lines(child, depth + 1))
            return out

        return "\n".join(lines(span, 0))
