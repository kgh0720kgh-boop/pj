"""Provider-neutral parsing and planner backend contracts for Week 2."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ParseResult:
    raw_output: str
    parse_success: bool
    graph: dict[str, Any] | None
    parse_error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_output": self.raw_output,
            "parse_success": self.parse_success,
            "graph": self.graph,
            "parse_error": self.parse_error,
        }


def _candidate_json(raw_output: str) -> str:
    text = raw_output.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    return fenced.group(1) if fenced else text


def parse_graph_output(raw_output: str) -> ParseResult:
    """Parse exactly one graph object without repair or substring guessing."""

    if not isinstance(raw_output, str):
        return ParseResult(str(raw_output), False, None, "raw output is not a string")
    try:
        value = json.loads(_candidate_json(raw_output))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return ParseResult(raw_output, False, None, f"{type(exc).__name__}: {exc}")
    if not isinstance(value, dict):
        return ParseResult(raw_output, False, None, "top-level JSON value is not an object")
    return ParseResult(raw_output, True, value, None)


@dataclass(frozen=True)
class GenerationResponse:
    text: str
    latency_ms: float
    model_calls: int = 1
    metadata: Mapping[str, Any] | None = None


class PlannerBackend(Protocol):
    """Same backend contract for unconstrained, post-hoc, and constrained runs."""

    backend_id: str

    def generate(self, messages: Sequence[Mapping[str, str]], **kwargs: Any) -> GenerationResponse:
        ...


__all__ = [
    "GenerationResponse",
    "ParseResult",
    "PlannerBackend",
    "parse_graph_output",
]
