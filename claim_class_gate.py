"""WELL claim-class gate - the explanatory-class gate for claims about a PERSON.

DITEMPA BUKAN DIBERI - Forged, Not Given.

PROVENANCE / EVIDENCE (on disk, re-checkable):
  receipt_id: WELL-CLAIMCLASS-GATE-20260919
  /root/WELL/tools_sot.yaml                   WELL tool SOT (declared surface)
  /root/WELL/contracts/WELL_MANIFEST.json     WELL organ manifest
  /root/WELL/well_mcp/manifest.json           well_mcp surface manifest
  /root/AAA/lib/claim_kernel/claim_kernel.py  claim_kernel/v1 (selftest ALL PASS)
  /root/WELL/gate/dignity_shadow.py           existing WELL dignity guard (F05/F06)
  /root/WELL/server.py:3317                   RECORD point - well_log
  /root/WELL/server.py:17387                  REPORT point - well_guard_dignity
  /root/WELL/well_triad/phase1_tools.py:114   RECORD point - well_log_intake
  /root/WELL/tests/test_claim_class_gate.py   tests for this module

WELL (:18083) is the human-substrate organ. Every other organ's claims are about
machines, capital, rock or institutions. WELL's claims are about a real person's
body and state - and a *narrative* about a person is the most dangerous claim
class of all, because it is unfalsifiable and reads as insight. "He is burned
out because he is avoidant" has no mechanism, no measure, and no way to be
proven wrong; it is nonetheless the sentence most likely to be returned as an
assessment and to drive a recommendation about a human being.

WHAT THIS GATE GOVERNS - READ THIS BEFORE TOUCHING IT
-----------------------------------------------------
This gate governs the EPISTEMIC CLASS OF A SENTENCE.
It does NOT label, score, rank, judge or model the PERSON.

* The subject of the gate is the claim's class: MEASURED / MECHANISM / PATTERN /
  NARRATIVE / UNCLASSIFIED (claim_kernel/v1).
* ``person_label_assigned`` is always False. No field of any result carries a
  class, tier or score for a human being.
* A NARRATIVE-class sentence may be TRUE, VALUABLE and WORTH READING. It is
  still refused as an assessment. The refusal is about the sentence's
  explanatory power, never about the person's dignity, worth or truthfulness.

The one rule (claim_kernel): a NARRATIVE claim may be PUBLISHED/LOGGED but it
may never be the SOLE JUSTIFICATION for a mutation, and here it may never be
RETURNED AS AN ASSESSMENT that drives a recommendation. UNCLASSIFIED fails
closed.

RECORD vs REPORT
----------------
* RECORD point - ``server.well_log`` (biological telemetry) and
  ``server.well_log_intake`` (triad intake) write an observation about the body.
* REPORT point - ``server.well_guard_dignity`` returns an interpretation of a
  person's state as an ``observation`` + ``signal``, i.e. as an assessment that
  drives a recommendation. This is where the refusal bites hardest.

DIGNITY GUARD INTEGRATION (not beside it)
-----------------------------------------
WELL already has a dignity guard: ``gate/dignity_shadow.assess_dignity_risk``
(F05 PEACE / F06 EMPATHY, tiers SAFE | GUARDED | HOLD). This gate *calls* that
guard and consumes its verdict - it does not duplicate or replace it.

Interaction is strictly one-way and additive:

    dignity HOLD  =>  returned_as_assessment = False   (always)

The dignity guard can only ever REMOVE assessment eligibility. This gate can
never grant eligibility the dignity guard withheld, never soften a tier, and
never rewrites the guard's notes or violations. The guard's dict is passed
through verbatim under ``dignity``. The dignity guard is not weakened - it is
given a second, independent veto (explanatory class) and this gate is given a
floor (dignity).

Fail-closed: gate error, unreachable claim_kernel, undeclared class, unknown
class and NARRATIVE all yield ``returned_as_assessment = False``.

Sovereign: Muhammad Arif bin Fazil (F13)
License: AGPL-3.0
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

__all__ = [
    "CLAIM_CLASS_GATE_SCHEMA",
    "REFUSAL_VERDICTS",
    "CLAIM_CLASSES",
    "ACTION_ELIGIBLE_CLASSES",
    "NON_ASSESSMENT_CLASSES",
    "ASSESSMENT_WITHHELD_REASON",
    "evaluate_claim_class",
    "gate_human_claim",
    "must_not_return_as_assessment",
    "dignity_verdict",
]

CLAIM_CLASS_GATE_SCHEMA = "claim_class_gate/human_assessment/v1"

# Verdict strings are stable API - callers branch on them.
REFUSAL_VERDICTS = (
    "CLAIM_CLASS_NOT_DECLARED",
    "CLAIM_CLASS_ACTION_ELIGIBLE",
    "CLAIM_CLASS_NOT_ACTION_ELIGIBLE",
    "CLAIM_CLASS_MISMATCH",
    "CLAIM_CLASS_GATE_ERROR",
    "CLAIM_CLASS_DIGNITY_HOLD",
)

CLAIM_CLASSES = ("MEASURED", "MECHANISM", "PATTERN", "NARRATIVE", "UNCLASSIFIED")
ACTION_ELIGIBLE_CLASSES = ("MEASURED", "MECHANISM", "PATTERN")

# Classes that may be logged but may never come back as an assessment.
NON_ASSESSMENT_CLASSES = ("NARRATIVE", "UNCLASSIFIED")

ASSESSMENT_WITHHELD_REASON = (
    "A statement about a person in class {cls} is not returned as an assessment "
    "and drives no recommendation. It is logged. This governs the class of the "
    "SENTENCE, not the person: no label, score or tier is attached to anyone."
)

# claim_kernel is the authority for claim class. Reached by import; if it is not
# already on sys.path its parent directory is appended once (the module's own
# documented install instruction). An unreachable kernel does NOT open the gate:
# the membership rule is still enforced locally and `degraded` says so.
CLAIM_KERNEL_PATH = os.environ.get("CLAIM_KERNEL_PATH", "/root/AAA/lib")
_CLAIM_KERNEL_CACHE: dict = {"loaded": False, "module": None}


def _claim_kernel():
    """Import claim_kernel if reachable; None if not. Never raises."""
    if _CLAIM_KERNEL_CACHE["loaded"]:
        return _CLAIM_KERNEL_CACHE["module"]
    module = None
    try:
        import claim_kernel as module  # type: ignore  # noqa: F401
    except Exception:  # noqa: BLE001
        module = None
        try:
            if CLAIM_KERNEL_PATH not in sys.path:
                sys.path.append(CLAIM_KERNEL_PATH)
            import claim_kernel as module  # type: ignore  # noqa: F401,F811
        except Exception:  # noqa: BLE001
            module = None
    _CLAIM_KERNEL_CACHE["loaded"] = True
    _CLAIM_KERNEL_CACHE["module"] = module
    return module


def dignity_verdict(statement: str, confidence: float = 0.5) -> dict:
    """Run WELL's existing dignity guard. Never raises; UNKNOWN degrades closed.

    Imported lazily from ``gate.dignity_shadow`` so this module stays importable
    when the gate package is not on the path (tests, tooling). A guard that
    cannot be reached is reported as tier GUARDED with ``degraded`` set - an
    unreachable dignity guard must not read as SAFE.
    """
    try:
        from gate.dignity_shadow import assess_dignity_risk  # type: ignore
    except Exception:  # noqa: BLE001
        return {
            "tier": "GUARDED",
            "violations": [],
            "notes": [
                "Dignity guard unreachable; treated as GUARDED (fail-closed). "
                "Not SAFE."
            ],
            "safe_rephrase_hint": None,
            "degraded": True,
        }
    try:
        verdict = assess_dignity_risk(statement, confidence)
    except Exception as exc:  # noqa: BLE001
        return {
            "tier": "GUARDED",
            "violations": [],
            "notes": ["Dignity guard errored (%s); GUARDED." % str(exc)[:80]],
            "safe_rephrase_hint": None,
            "degraded": True,
        }
    out = dict(verdict)
    out["degraded"] = False
    return out


def evaluate_claim_class(claim_text: str, claim_class: Optional[str] = None) -> dict:
    """Class axis only: is this claim's declared class action-eligible?

    Delegates to ``claim_kernel.action_eligible()``. Fail-closed in every branch
    that is not a declared, action-eligible, self-consistent class.
    """
    declared = str(claim_class or "").strip().upper()
    result: dict[str, Any] = {
        "declared": declared if declared else "UNCLASSIFIED",
        "kernel": "not_consulted",
        "kernel_schema": "",
        "inferred": "",
        "agree": False,
        "action_eligible": False,
        "verdict": "CLAIM_CLASS_NOT_DECLARED",
        "reasons": [],
        "note": "",
        "degraded": False,
    }

    if not declared or declared not in CLAIM_CLASSES:
        result["reasons"] = ["class=UNCLASSIFIED is not action-eligible"]
        result["note"] = (
            "No action-eligible claim_class declared"
            + (" (%r is not a known class)" % declared if declared else "")
            + ". Undeclared fails closed: not returnable as an assessment."
        )
        return result

    kernel = _claim_kernel()
    if kernel is None:
        eligible = declared in ACTION_ELIGIBLE_CLASSES
        result.update(
            {
                "kernel": "local-fallback",
                "action_eligible": eligible,
                "degraded": True,
                "verdict": (
                    "CLAIM_CLASS_ACTION_ELIGIBLE"
                    if eligible
                    else "CLAIM_CLASS_NOT_ACTION_ELIGIBLE"
                ),
                "reasons": [] if eligible else ["class=%s is not action-eligible" % declared],
                "note": (
                    "claim_kernel unreachable at %s; membership rule enforced "
                    "locally, mismatch lint skipped." % CLAIM_KERNEL_PATH
                ),
            }
        )
        return result

    try:
        verdict_dict = kernel.action_eligible(claim_text, declared)
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "kernel": "claim_kernel",
                "kernel_schema": str(getattr(kernel, "SCHEMA", "")),
                "verdict": "CLAIM_CLASS_GATE_ERROR",
                "reasons": ["claim_kernel raised: %s" % str(exc)[:120]],
                "note": "Claim-class check errored; fail-closed.",
            }
        )
        return result

    class_verdict = verdict_dict.get("class_verdict") or {}
    eligible = bool(verdict_dict.get("eligible"))
    if eligible:
        verdict = "CLAIM_CLASS_ACTION_ELIGIBLE"
    elif declared == "NARRATIVE":
        verdict = "CLAIM_CLASS_NOT_ACTION_ELIGIBLE"
    elif class_verdict.get("agree") is False:
        verdict = "CLAIM_CLASS_MISMATCH"
    else:
        verdict = "CLAIM_CLASS_NOT_ACTION_ELIGIBLE"

    result.update(
        {
            "kernel": "claim_kernel",
            "kernel_schema": str(verdict_dict.get("schema", "")),
            "inferred": str(class_verdict.get("inferred", "")),
            "agree": bool(class_verdict.get("agree", False)),
            "action_eligible": eligible,
            "verdict": verdict,
            "reasons": [str(r) for r in (verdict_dict.get("reasons") or [])],
            "note": str(class_verdict.get("note", "")),
        }
    )
    return result


def gate_human_claim(
    statement: str,
    claim_class: Optional[str] = None,
    *,
    tool: str = "",
    subject: Optional[str] = None,
    confidence: float = 0.5,
    dignity: Optional[dict] = None,
) -> dict:
    """Gate a sentence about a person: may it be returned AS AN ASSESSMENT?

    Args:
        statement: the sentence about a human body/state being recorded or
            reported. This is the object of the gate - never the person.
        claim_class: declared class, one of CLAIM_CLASSES. ``None`` (undeclared)
            fails closed.
        tool: calling tool name, for provenance.
        subject: name of the person the sentence is about, used for the audit
            trail ONLY. It is never classified, scored or labelled.
        confidence: passed to the dignity guard when it is run here.
        dignity: a dignity-guard verdict already computed by the caller. Pass it
            so WELL has ONE dignity guard, not two. If omitted, the guard is run
            here.

    Returns a dict including: gate, schema, tool, subject, statement_logged,
    returned_as_assessment, assessment_refused, verdict, declared, inferred,
    agree, action_eligible, reasons, note, kernel, kernel_schema, degraded,
    refusal, dignity, dignity_guard_authority, dignity_guard_unchanged,
    person_label_assigned, governs, governs_not, w0, final_authority.

    ``returned_as_assessment`` is True ONLY for a declared, action-eligible,
    self-consistent class AND a dignity tier that is not HOLD. Everything else -
    undeclared, unknown, NARRATIVE, mismatch, kernel error, dignity HOLD - is
    False. Fail-closed.
    """
    statement = statement if isinstance(statement, str) else str(statement or "")
    cls = evaluate_claim_class(statement, claim_class)

    # Dignity guard: consume it, never duplicate it, never soften it.
    dignity_result = (
        dignity if isinstance(dignity, dict) else dignity_verdict(statement, confidence)
    )
    dignity_tier = str(dignity_result.get("tier", "GUARDED")).upper()
    dignity_hold = dignity_tier == "HOLD"

    eligible = bool(cls["action_eligible"]) and not dignity_hold
    verdict = "CLAIM_CLASS_DIGNITY_HOLD" if dignity_hold else str(cls["verdict"])

    reasons = list(cls["reasons"])
    if dignity_hold:
        reasons.append(
            "dignity guard tier=HOLD (F05 PEACE / F06 EMPATHY): the sentence "
            "reduces a person to a label; it is refused as an assessment "
            "regardless of claim class."
        )

    declared = str(cls["declared"])
    refusal: Optional[dict] = None
    if not eligible:
        refusal = {
            "refused": True,
            "code": "CLAIM_CLASS_NOT_RETURNABLE_AS_ASSESSMENT",
            "may_be_logged": True,
            "returned_as_assessment": False,
            "drives_recommendation": False,
            "reason": ASSESSMENT_WITHHELD_REASON.format(cls=declared),
            "remedy": (
                "Declare claim_class in "
                "(%s) and attach the number, the stated mechanism, or the case "
                "set that supports it." % ", ".join(ACTION_ELIGIBLE_CLASSES)
            ),
            "dignity_hold": dignity_hold,
        }

    return {
        "gate": "well_human_claim_gate",
        "schema": CLAIM_CLASS_GATE_SCHEMA,
        "tool": tool,
        "subject": subject,
        "statement_logged": True,  # logging is always permitted
        "returned_as_assessment": eligible,
        "assessment_refused": not eligible,
        "verdict": verdict,
        "declared": declared,
        "inferred": str(cls["inferred"]),
        "agree": bool(cls["agree"]),
        "action_eligible": eligible,
        "reasons": reasons,
        "note": str(cls["note"]),
        "kernel": cls["kernel"],
        "kernel_schema": cls["kernel_schema"],
        "degraded": bool(cls["degraded"]) or bool(dignity_result.get("degraded")),
        "refusal": refusal,
        # The dignity guard is the sole authority on dignity. Its verdict is
        # passed through verbatim and can only ever REMOVE eligibility above.
        "dignity": dignity_result,
        "dignity_guard_authority": "gate/dignity_shadow.assess_dignity_risk",
        "dignity_guard_unchanged": True,
        # Hard invariant of this gate: it never attaches a class to a PERSON.
        # Only the sentence carries a class.
        "person_label_assigned": False,
        "governs": "EPISTEMIC_CLASS_OF_A_SENTENCE_ABOUT_A_PERSON",
        "governs_not": (
            "Never labels, scores, tiers or models the person. A NARRATIVE "
            "sentence may be true and worth reading; the refusal concerns its "
            "explanatory power, not anyone's dignity."
        ),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "final_authority": "Arif",
    }


def must_not_return_as_assessment(
    statement: str,
    claim_class: Optional[str] = None,
    *,
    confidence: float = 0.5,
    dignity: Optional[dict] = None,
) -> bool:
    """True when this sentence may be logged but must NOT come back as an
    assessment that drives a recommendation. Fail-closed: True on any doubt."""
    verdict = gate_human_claim(
        statement,
        claim_class,
        confidence=confidence,
        dignity=dignity,
    )
    return not bool(verdict["returned_as_assessment"])
