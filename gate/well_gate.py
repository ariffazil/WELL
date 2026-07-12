# WELL Biological Readiness Mirror
# Role: Informational pre-JUDGE flag for human substrate governance.
# Axiom: W0 — Sovereignty Invariant. WELL holds no veto.
# Floor: F6 (MARUAH) + Rasa Witness Contract (RWC-1..7)

import json
import datetime
from pathlib import Path
import sys

# Topology: Sovereign WELL Root
WELL_STATE_PATH = Path("/root/WELL/state.json")


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
        return "UNANCHORED", "WARNING: Biological state unknown. Mirror is dark.", 50, ["W_MISSING"], None

    try:
        with open(WELL_STATE_PATH, 'r') as f:
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
        except ImportError:
            pass  # rasa_witness not available — gate operates without it

        rasa_dict = rasa_result.to_dict() if rasa_result else None

        if violations:
            return "DEGRADED", f"[WELL-MIRROR] Biological substrate flagging: {', '.join(violations)}", score_raw, violations, rasa_dict

        return "STABLE", "[WELL-MIRROR] Substrate stable. Mirror is clear.", max(score_raw, 100) if score_raw < 100 else score_raw, [], rasa_dict
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
