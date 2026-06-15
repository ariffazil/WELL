"""
WELL Federation Memory Client - 2026-06-14
========================================================================
Adoption of FEDERATION_MEMORY_CONTRACT.md (R1: single write surface).
All WELL memory writes route through arifOS MCP `arif_memory_recall(mode="store")`.
No direct Qdrant / Supabase / Graphiti writes from WELL tools.

SOVEREIGN PATTERN (F2 honest, F11 gate compliant):
  - ACTOR_ID is the AI agent driving the organ (FORGE, OPENCLAW, HERMES, etc.)
  - Organ is the domain tag (well)
  - 888 sovereign decides which agents can write; organs inherit agent context
  - Direct `actor_id="well"` is F11-blocked by design

L5 Graphiti: advisory only (worker neutralized; 888 injects via raw Cypher).

DITEMPA BUKAN DIBERI - Forged, Not Given
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

ARIFOS_MCP_URL = os.getenv("ARIFOS_MCP_URL", "http://localhost:8088")
# Sovereign actor: which AI agent is driving WELL right now.
# F11 gate enforces actor_id is tracked by system.
ACTOR_ID = os.getenv("WELL_SOVEREIGN_ACTOR", "FORGE")
DEFAULT_TIMEOUT_S = 30.0
DOMAIN_TAG = "well"

_session_id: str | None = None
_session_ts: float = 0.0
_SESSION_TTL_S = 300.0


def _ensure_session() -> str | None:
    global _session_id, _session_ts
    now = time.time()
    if _session_id and (now - _session_ts) < _SESSION_TTL_S:
        return _session_id
    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "WELL", "version": "0.1"},
                    },
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        with urlrequest.urlopen(req, timeout=5) as resp:
            sid = resp.headers.get("mcp-session-id")
            if sid:
                _session_id = sid
                _session_ts = now
                return sid
    except (URLError, HTTPError, TimeoutError, OSError):
        return None
    return None


def _build_tags(extra: list[str] | None) -> list[str]:
    tags = [DOMAIN_TAG, "federation_adoption", "well"]
    if extra:
        tags.extend(extra)
    return tags


def remember(
    content: str,
    *,
    tags: list[str] | None = None,
    tier: str = "canon",
    session_id: str | None = None,
    summary: str | None = None,
    context: str = "normal",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Federation memory write via arifOS MCP. Never raises."""
    if not content:
        return {"stored": False, "error": "empty_content"}
    sid = _ensure_session()
    if not sid:
        return {
            "stored": False,
            "error": "session_unavailable",
            "_degraded": "arifOS MCP unreachable",
        }

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": "tools/call",
        "params": {
            "name": "arif_memory_recall",
            "arguments": {
                "mode": "store",
                "metadata": {
                    "content": content,
                    "tags": _build_tags(tags),
                    "summary": summary,
                    "context": context,
                    "writer_bot": "WELL",
                    "organ": "well",
                    "sovereign_actor": ACTOR_ID,
                    **(metadata or {}),
                },
                "actor_id": ACTOR_ID,
                "session_id": session_id or "well-default-session",
                "tier": tier,
            },
        },
    }
    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": sid,
            },
        )
        with urlrequest.urlopen(req, timeout=DEFAULT_TIMEOUT_S) as resp:
            body = resp.read().decode()
            return _parse_response(body, content)
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        return {
            "stored": False,
            "error": f"{type(e).__name__}: {e}",
            "_degraded": "arifOS MCP call failed",
        }


def recall(
    query: str,
    *,
    session_id: str | None = None,
    limit: int = 5,
    context: str = "normal",
) -> dict[str, Any]:
    """Federation memory read via arifOS MCP."""
    sid = _ensure_session()
    if not sid:
        return {"status": "session_unavailable", "results": []}
    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": int(time.time() * 1000) % 1_000_000,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_memory_recall",
                        "arguments": {
                            "mode": "search",
                            "query": query,
                            "session_id": session_id or "well-default-session",
                            "actor_id": ACTOR_ID,
                            "limit": limit,
                            "context": context,
                        },
                    },
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": sid,
            },
        )
        with urlrequest.urlopen(req, timeout=DEFAULT_TIMEOUT_S) as resp:
            body = resp.read().decode()
            return _parse_response(body, query, is_recall=True)
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        return {"status": "exception", "error": str(e), "results": []}


def _parse_response(body: str, content: str, *, is_recall: bool = False) -> dict[str, Any]:
    """Parse MCP response (JSON or SSE)."""
    for line in body.split("\n"):
        if line.startswith("data: "):
            try:
                rpc = json.loads(line[6:])
                sc = rpc.get("result", {}).get("structuredContent", {})
                if is_recall:
                    return {"status": "ok", "results": sc.get("results", [])}
                return _format_store_result(sc)
            except Exception:
                continue
    try:
        rpc = json.loads(body)
        sc = rpc.get("result", {}).get("structuredContent", {})
        if is_recall:
            return {"status": "ok", "results": sc.get("results", [])}
        return _format_store_result(sc)
    except Exception:
        return {"stored": False, "error": "no_data_in_response"}


def _format_store_result(sc: dict[str, Any]) -> dict[str, Any]:
    if sc.get("verdict") and sc["verdict"] != "SEAL":
        return {
            "stored": False,
            "verdict": sc.get("verdict"),
            "reasons": sc.get("reasons"),
            "failed_floors": sc.get("failed_floors"),
            "_degraded": f"arifOS returned {sc['verdict']}",
        }
    return {
        "stored": True,
        "memory_id": sc.get("memory_id"),
        "point_id": sc.get("point_id"),
        "pg_id": sc.get("pg_id"),
        "pg_ok": sc.get("pg_ok"),
        "l5_status": sc.get("l5_status"),
        "backends": sc.get("backends"),
    }


def get_contract_surface() -> dict[str, str]:
    return {
        "mcpUrl": ARIFOS_MCP_URL,
        "actor": ACTOR_ID,
        "organ": "well",
        "contract": "FEDERATION_MEMORY_CONTRACT.md (R1: single write surface)",
        "l5_status": "advisory_only (worker neutralized; 888 injects via raw Cypher)",
    }
