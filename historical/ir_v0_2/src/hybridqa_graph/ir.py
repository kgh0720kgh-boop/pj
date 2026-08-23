"""Data model and JSON helpers for execution-graph IR v0.1.

The validator accepts ordinary mappings so that malformed documents can be
reported rather than rejected during object construction.  These immutable
classes are the convenient, valid-document representation used by executors
and annotation scripts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping


IR_VERSION = "0.1"
DEFAULT_OUTPUT_PORT = "result"


@dataclass(frozen=True)
class SourceRef:
    """Reference to one entry in the graph-level ``sources`` map."""

    source_id: str
    kind: str = field(default="source", init=False)

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "source_id": self.source_id}


@dataclass(frozen=True)
class NodeRef:
    """Reference to a named output port on a node."""

    node_id: str
    port: str = DEFAULT_OUTPUT_PORT
    kind: str = field(default="node", init=False)

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "node_id": self.node_id, "port": self.port}


InputRef = SourceRef | NodeRef


@dataclass(frozen=True)
class OutputSpec:
    port: str
    type: str

    def to_dict(self) -> dict[str, str]:
        return {"port": self.port, "type": self.type}


@dataclass(frozen=True)
class SourceSpec:
    type: str
    locator: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "locator": dict(self.locator)}


@dataclass(frozen=True)
class Node:
    id: str
    operator: str
    inputs: Mapping[str, InputRef]
    arguments: Mapping[str, Any]
    output: OutputSpec
    tool_binding: str
    provenance: Mapping[str, Any]
    status: str | None = None
    execution: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "operator": self.operator,
            "inputs": {name: ref.to_dict() for name, ref in self.inputs.items()},
            "arguments": dict(self.arguments),
            "output": self.output.to_dict(),
            "tool_binding": self.tool_binding,
            "provenance": dict(self.provenance),
        }
        if self.status is not None:
            result["status"] = self.status
        if self.execution is not None:
            result["execution"] = dict(self.execution)
        return result


@dataclass(frozen=True)
class ExecutionGraph:
    graph_id: str
    question_ref: Mapping[str, Any]
    schema_ref: Mapping[str, Any]
    sources: Mapping[str, SourceSpec]
    nodes: tuple[Node, ...]
    answer: NodeRef
    ir_version: str = IR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "ir_version": self.ir_version,
            "graph_id": self.graph_id,
            "question_ref": dict(self.question_ref),
            "schema_ref": dict(self.schema_ref),
            "sources": {source_id: source.to_dict() for source_id, source in self.sources.items()},
            "nodes": [node.to_dict() for node in self.nodes],
            "answer": self.answer.to_dict(),
        }


def graph_to_dict(graph: ExecutionGraph | Mapping[str, Any]) -> dict[str, Any]:
    """Return a detached JSON-compatible dictionary."""

    raw = graph.to_dict() if isinstance(graph, ExecutionGraph) else dict(graph)
    # JSON round-trip provides a small dependency-free deep copy and catches
    # accidental non-serializable annotation values at the serialization edge.
    return json.loads(json.dumps(raw, ensure_ascii=False))


def dump_graph(
    graph: ExecutionGraph | Mapping[str, Any],
    path: str | Path,
    *,
    indent: int = 2,
) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(graph_to_dict(graph), handle, ensure_ascii=False, indent=indent)
        handle.write("\n")


def load_graph(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("An execution graph JSON document must be an object")
    return value


def make_ref(value: Mapping[str, Any]) -> InputRef:
    """Construct a typed reference from its canonical JSON representation."""

    kind = value.get("kind")
    if kind == "source":
        return SourceRef(source_id=str(value["source_id"]))
    if kind == "node":
        return NodeRef(
            node_id=str(value["node_id"]),
            port=str(value.get("port", DEFAULT_OUTPUT_PORT)),
        )
    raise ValueError(f"Unknown reference kind: {kind!r}")


__all__ = [
    "DEFAULT_OUTPUT_PORT",
    "IR_VERSION",
    "ExecutionGraph",
    "InputRef",
    "Node",
    "NodeRef",
    "OutputSpec",
    "SourceRef",
    "SourceSpec",
    "dump_graph",
    "graph_to_dict",
    "load_graph",
    "make_ref",
]
