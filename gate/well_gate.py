# WELL Biological Readiness Mirror
# Role: Informational pre-JUDGE flag for human substrate governance.
# Axiom: W0 — Sovereignty Invariant. WELL holds no veto.
# Floor: F6 (MARUAH) + Rasa Witness Contract (RWC-1..7)

import json
import datetime
import os
from pathlib import Path
import sys
import urllib.request
import urllib.error

# Topology: Sovereign WELL Root. Canonical live path aligned with
# server.STATE_PATH; /root/WELL/state.json is a retired fixture decoy.
WELL_STATE_PATH = Path(os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json"))

# arifOS kernel endpoint — adopted from WEALTH wealth_arifos_bridge pattern.
# Per sovereign (888) C3 REDTEAM ratification 2026-07-18: every organ must
# delegate session validation to the arifOS kernel. WELL adopts the same
# pattern as GEOX + WEALTH — no new abstractions, just a new function on an
# existing gate module.
ARIFOS_KERNEL_URL = "http://127.0.0.1:8088"
ARIFOS_MCP_URL = f"{ARIFOS_KERNEL_URL}/mcp"


def validate_session_at_arifos(
    session_id: str | None = None,
    actor_id: str | None = None,
    session_token: str | None = None,
    timeout_seconds: float = 3.0,
) -> dict:
    """Delegate session validation to arifOS kernel (WELL adoption of GEOX/WEALTH pattern).

    Three-state verdict:
      valid=True                                       → ALLOW
      valid=False, reason='...'                        → HOLD (session rejected)
      valid=False, reason='ARIFOS_UNREACHABLE'         → HOLD, FAIL-CLOSED

    Fail-closed: if arifOS is unreachable, return HOLD. Never open.
    """
    if not session_id and not session_token:
        return {
            "valid": False,
            "reason": "L11 AUTH: session_id or session_token required",
            "fail_mode": "CLOSED",
            "actor_id": actor_id,
        }

    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "arif_init",
                "arguments": {
                    "mode": "validate",
                    "session_id": session_id,
                    "actor_id": actor_id,
                    "session_token": session_token,
                },
            },
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            ARIFOS_MCP_URL,
            data=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            if 200 <= resp.status < 300:
                raw = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    return {
                        "valid": False,
                        "reason": "L11 AUTH: arifOS response malformed",
                        "fail_mode": "CLOSED",
                    }
                result = data.get("result", {}) or {}
                content = result.get("content", [])
                parsed = result
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            try:
                                parsed = json.loads(item.get("text", "{}"))
                                break
                            except (json.JSONDecodeError, TypeError):
                                pass
                if not isinstance(parsed, dict):
                    return {
                        "valid": False,
                        "reason": "L11 AUTH: arifOS response malformed",
                        "fail_mode": "CLOSED",
                    }
                # Trust arifOS's authoritative verdict: result.valid is the
                # ground truth. effective_verdict can be HOLD/VOID/APPROVED;
                # we accept only when arifOS explicitly says valid=True AND
                # the session standing has a verified actor (or session_token).
                inner_result = (
                    parsed.get("result", {})
                    if isinstance(parsed.get("result"), dict)
                    else {}
                )
                arifos_says_valid = inner_result.get("valid")
                if arifos_says_valid is False:
                    return {
                        "valid": False,
                        "reason": inner_result.get("error")
                        or parsed.get("reason")
                        or "L11 AUTH: arifOS rejected session",
                        "fail_mode": "CLOSED",
                        "actor_id": actor_id,
                        "session_id": session_id,
                    }
                standing = (
                    parsed.get("standing", {})
                    if isinstance(parsed.get("standing"), dict)
                    else {}
                )
                standing_actor = (
                    standing.get("actor", {})
                    if isinstance(standing.get("actor"), dict)
                    else {}
                )
                actor_verified = standing_actor.get("verified") is True
                session_token_present = bool(parsed.get("session_token"))
                resp_sid = parsed.get("session_id") or standing.get("session_id")
                if actor_verified or session_token_present:
                    return {
                        "valid": True,
                        "session": parsed,
                        "actor": standing_actor.get("claimed_id")
                        or standing_actor.get("canonical_id")
                        or parsed.get("actor_id")
                        or actor_id,
                        "authority": standing.get("authority", {}).get("band")
                        if isinstance(standing.get("authority"), dict)
                        else parsed.get("authority") or "OBSERVE_ONLY",
                        "session_id": resp_sid or session_id,
                    }
                return {
                    "valid": False,
                    "reason": "L11 AUTH: session not verified by arifOS (no verified actor, no session_token)",
                    "fail_mode": "CLOSED",
                    "actor_id": actor_id,
                    "session_id": session_id,
                }
            return {
                "valid": False,
                "reason": f"L11 AUTH: arifOS HTTP {resp.status}",
                "fail_mode": "CLOSED",
                "actor_id": actor_id,
            }
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        return {
            "valid": False,
            "reason": f"ARIFOS_UNREACHABLE: {type(exc).__name__}: {str(exc)[:80]}",
            "fail_mode": "CLOSED",
            "actor_id": actor_id,
            "session_id": session_id,
        }


def reflect_readiness(self_report_rasa=None, text_context=None):
    """
    Reflects current well_state for JUDGE context.
    Now includes Rasa Witness Contract evaluation (F6 binding).

    Args:
        self_report_rasa: Optional human self-report (e.g., "ok", "fine").
                          Has semantic sovereignty (RWC-1).
        text_context: Optional text to scan for prohibited conclusions (RWC-6).

    Returns: (status, message, readiness_score, violations, rasa_witness)
    """
    if not WELL_STATE_PATH.exists():
        return (
            "UNANCHORED",
            "WARNING: Biological state unknown. Mirror is dark.",
            50,
            ["W_MISSING"],
            None,
        )

    try:
        with open(WELL_STATE_PATH, "r") as f:
            state = json.load(f)

        metrics = state.get("metrics", {})
        sleep = metrics.get("sleep", {})
        cognitive = metrics.get("cognitive", {})
        violations = []

        # W1: Sleep Integrity Reflection
        if sleep.get("sleep_debt_days", 0) > 2:
            violations.append("W1_SLEEP_DEBT")

        # W5: Cognitive Entropy Reflection
        if cognitive.get("clarity", 10) < 4:
            violations.append("W5_COGNITIVE_ENTROPY")

        score_raw = state.get("well_score")
        if score_raw is None or not isinstance(score_raw, (int, float)):
            score_raw = 0

        # Rasa Witness Contract evaluation (F6)
        #
        # HUMAN_RASA P0 REMEDIATION G9 (2026-11-01): this block used to swallow
        # ImportError and continue WITHOUT the witness, so reflect_readiness()
        # could report STABLE on a run where the Rasa Witness Contract never
        # executed. That is a fail-open gate. The witness contract is fail-closed:
        # witness unavailable (import failure OR any exception inside it) => HOLD
        # with reason RASA_WITNESS_UNAVAILABLE. Readiness is withheld, not guessed.
        rasa_result = None
        try:
            from gate.rasa_witness import rasa_witness_gate

            rasa_result = rasa_witness_gate(
                str(WELL_STATE_PATH),
                self_report_rasa=self_report_rasa,
                text_context=text_context,
            )
            # Enforce RWC-6: strip prohibited conclusions from any output
            if rasa_result and rasa_result.prohibited_violations:
                violations.append("RWC6_PROHIBITED_CONCLUSIONS")
        except Exception as exc:  # ImportError, or any witness-side failure
            detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
            return (
                "HOLD",
                f"[WELL-HOLD] RASA_WITNESS_UNAVAILABLE: rasa witness contract could "
                f"not be evaluated — readiness withheld ({detail})",
                score_raw,
                violations + ["RASA_WITNESS_UNAVAILABLE"],
                None,
            )

        rasa_dict = rasa_result.to_dict() if rasa_result else None

        if violations:
            return (
                "DEGRADED",
                f"[WELL-MIRROR] Biological substrate flagging: {', '.join(violations)}",
                score_raw,
                violations,
                rasa_dict,
            )

        return (
            "STABLE",
            "[WELL-MIRROR] Substrate stable. Mirror is clear.",
            max(score_raw, 100) if score_raw < 100 else score_raw,
            [],
            rasa_dict,
        )
    except Exception as e:
        return "ERROR", f"[WELL-ERROR] Schema mismatch: {str(e)}", 0, ["W_ERROR"], None


if __name__ == "__main__":
    # Parse optional CLI args
    rasa_arg = None
    text_arg = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--rasa" and i + 1 < len(args):
            rasa_arg = args[i + 1]
            i += 2
        elif args[i] == "--text" and i + 1 < len(args):
            text_arg = args[i + 1]
            i += 2
        else:
            i += 1

    status, msg, score, violations, rasa_witness = reflect_readiness(
        self_report_rasa=rasa_arg,
        text_context=text_arg,
    )
    # Output is always successful (sys.exit(0)) because WELL never blocks alone.
    output = {
        "status": status,
        "message": msg,
        "score": score,
        "violations": violations,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    if rasa_witness:
        output["rasa_witness"] = rasa_witness
    print(json.dumps(output, indent=2))
    sys.exit(0)
