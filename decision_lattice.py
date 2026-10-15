"""WELL decision lattice -- canonical, executable C-class matrix.

Directive: WELL::SEVERITY_INVERSION_REPAIR::2026-10-14
           AUTHORITY: ARIF · MODE: REPAIR_FIRST

This module is the SINGLE SOURCE OF TRUTH for:

  * the closed route-signal vocabulary and its strictness ordering
  * the homeostasis band derivation
  * the C-class x band routing matrix
  * the telemetry-evidence ceiling
  * monotonic composition of the two
  * routing-note rendering derived FROM the final structured verdict

KILL CRITERION (binding, from the directive):

    Any path where weaker telemetry changes a stricter verdict into a more
    permissive verdict: VOID.

Composition is therefore ``max()`` over strictness -- never assignment. The
defect this repairs is a telemetry cap written as ``route_signal = "CAUTION"``,
which overwrote DEFER / ADVISORY_BLOCKED with a weaker signal: an honesty cap
that increased permissiveness.

The prose matrix in ``prompts/__init__.py`` is documentation. It is bound to
this table by ``tests/test_c5_decision_lattice.py::test_matrix_matches_prose_spec``.
Do not edit one without the other.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final

__all__ = [
    "RouteSignal",
    "ROUTE_VOCABULARY",
    "BANDS",
    "DECISION_CLASSES",
    "C_CLASS_MATRIX",
    "CONSTITUTIONAL_VERDICTS",
    "LEGACY_VERDICT_BY_BAND",
    "OffVocabularyVerdict",
    "band_from_score",
    "matrix_signal",
    "telemetry_ceiling",
    "g_fold_ceiling",
    "compose",
    "validate_route_signal",
    "render_routing_note",
    "explain_signal",
]


class RouteSignal(IntEnum):
    """Closed vocabulary of WELL advisory route signals.

    Ordered least -> most restrictive. ``IntEnum`` so composition is ``max()``.

    SEAL / HOLD / VOID / SABAR are arifOS constitutional verdicts and are
    deliberately NOT members: WELL is ADVISORY_ONLY and must not emit them as
    decisions. See ``CONSTITUTIONAL_VERDICTS``.
    """

    PROCEED = 0
    CAUTION = 1
    DEFER = 2
    ADVISORY_BLOCKED = 3


ROUTE_VOCABULARY: Final[tuple[str, ...]] = tuple(s.name for s in RouteSignal)

#: Verdicts reserved to arifOS. WELL may never emit these as a decision.
CONSTITUTIONAL_VERDICTS: Final[frozenset[str]] = frozenset(
    {"SEAL", "HOLD", "VOID", "SABAR"}
)

#: Homeostasis bands, best -> worst.
BANDS: Final[tuple[str, ...]] = ("OPTIMAL", "STABLE", "DEGRADED", "CRITICAL")

#: Recognised decision classes. Anything else fails closed.
DECISION_CLASSES: Final[tuple[str, ...]] = ("C1", "C2", "C3", "C4", "C5")

_P = RouteSignal.PROCEED
_D = RouteSignal.DEFER
_B = RouteSignal.ADVISORY_BLOCKED

#: Canonical C-class x band matrix.
#:
#: Mirrors ``prompts/__init__.py`` "THE C-CLASS THRESHOLD MATRIX", where the
#: prose label ``BLOCK`` is the wire value ``ADVISORY_BLOCKED``.
C_CLASS_MATRIX: Final[dict[str, dict[str, RouteSignal]]] = {
    "C1": {"OPTIMAL": _P, "STABLE": _P, "DEGRADED": _P, "CRITICAL": _B},
    "C2": {"OPTIMAL": _P, "STABLE": _P, "DEGRADED": _P, "CRITICAL": _B},
    "C3": {"OPTIMAL": _P, "STABLE": _P, "DEGRADED": _D, "CRITICAL": _B},
    "C4": {"OPTIMAL": _P, "STABLE": _D, "DEGRADED": _B, "CRITICAL": _B},
    "C5": {"OPTIMAL": _P, "STABLE": _B, "DEGRADED": _B, "CRITICAL": _B},
}

#: Score -> band thresholds (descending). Canonical; previously inline.
_BAND_THRESHOLDS: Final[tuple[tuple[float, str], ...]] = (
    (7.0, "OPTIMAL"),
    (5.0, "STABLE"),
    (3.0, "DEGRADED"),
)

#: LEGACY WIRE COMPAT -- DO NOT EXTEND.
#:
#: ``verdict`` historically carried SEAL/HOLD/VOID from this organ. That is an
#: authority-class leak (WELL is ADVISORY_ONLY; arifOS adjudicates). It is
#: preserved verbatim here ONLY because A-FORGE branches on the literal value
#: (``chain-orchestrator.ts:286`` -> ``verdict === 'HOLD'``) and P0 item 9
#: forbids modifying other organs. Renaming it unilaterally would make that
#: gate fail OPEN.
#:
#: Tracked as residual risk R1 for a coordinated WELL + A-FORGE change.
#: New code must read ``decision_signal``, never ``verdict``.
LEGACY_VERDICT_BY_BAND: Final[dict[str, str]] = {
    "OPTIMAL": "SEAL",
    "STABLE": "SEAL",
    "DEGRADED": "HOLD",
    "CRITICAL": "VOID",
}


class OffVocabularyVerdict(ValueError):
    """A final route signal fell outside the closed vocabulary.

    Raised rather than coerced: silently substituting a default is how the
    original defect shipped.
    """


def band_from_score(homeostasis_score: float) -> str:
    """Derive the homeostasis band from the 0-10 score."""
    for floor, band in _BAND_THRESHOLDS:
        if homeostasis_score >= floor:
            return band
    return "CRITICAL"


def matrix_signal(
    band: str,
    decision_class: str,
    *,
    chronic_fatigue: bool = False,
) -> tuple[RouteSignal, str]:
    """Evaluate the canonical matrix. Returns ``(signal, reason_code)``.

    Fails closed: an unrecognised band or decision class yields
    ADVISORY_BLOCKED, never PROCEED.

    C5 is the strictest gate. Per spec -- "proceed only if OPTIMAL + no chronic
    fatigue; block otherwise" -- chronic fatigue blocks C5 in EVERY band,
    including OPTIMAL. The repaired defect: no branch previously mapped
    ``chronic_fatigue`` to a block; the OPTIMAL branch emitted DEFER while its
    own note claimed "C5 blocked".
    """
    dc = str(decision_class or "").strip().upper()
    b = str(band or "").strip().upper()

    if dc == "C5" and chronic_fatigue:
        return RouteSignal.ADVISORY_BLOCKED, "C5_CHRONIC_FATIGUE"

    row = C_CLASS_MATRIX.get(dc)
    if row is None:
        return RouteSignal.ADVISORY_BLOCKED, "UNKNOWN_DECISION_CLASS"

    signal = row.get(b)
    if signal is None:
        return RouteSignal.ADVISORY_BLOCKED, "UNKNOWN_BAND"

    return signal, "MATRIX"


def telemetry_ceiling(telemetry_status: str | None) -> RouteSignal:
    """Most permissive signal that the available evidence can support.

    Only the exact canonical token ``"verified"`` may support PROCEED. Every
    other value -- weaker evidence, missing, empty, or a differently-cased or
    padded lookalike -- yields a CAUTION ceiling.

    Deliberately NOT normalised, unlike :func:`matrix_signal` and
    :func:`validate_route_signal`. The asymmetry is directional:

      * Those fold case/whitespace onto a CLOSED set and fail closed to
        ADVISORY_BLOCKED on a miss, so folding can never widen permissiveness.
      * This token grants the MOST permissive ceiling. Folding it would widen
        the set of inputs able to authorise PROCEED -- an evidence gate that
        normalises its way into permissiveness, which is the same defect class
        as the telemetry cap this module repairs.

    A ceiling is an upper bound on permissiveness, so applying it via
    :func:`compose` can only tighten the outcome.
    """
    if telemetry_status == "verified":
        return RouteSignal.PROCEED
    return RouteSignal.CAUTION


def g_fold_ceiling(
    live_g: object,
    g_threshold: float,
    decision_class: str,
) -> RouteSignal | None:
    """Governance-capacity ceiling for C4/C5, or ``None`` when inactive.

    Replaces the former conditional override that fired only when the signal
    was already PROCEED. Expressed as a ceiling so it composes monotonically:
    it can tighten PROCEED -> DEFER but can never relax DEFER or
    ADVISORY_BLOCKED.
    """
    if not isinstance(live_g, (int, float)) or isinstance(live_g, bool):
        return None
    if float(live_g) >= float(g_threshold):
        return None
    if str(decision_class or "").strip().upper() not in ("C4", "C5"):
        return None
    return RouteSignal.DEFER


def compose(*signals: RouteSignal | None) -> RouteSignal:
    """Monotonic composition: the strictest contributor wins.

    This is the repair for the severity inversion. Every contributor -- matrix
    verdict, telemetry ceiling, governance ceiling -- may only TIGHTEN. ``None``
    contributors are inactive and ignored.
    """
    active = [s for s in signals if s is not None]
    if not active:
        return RouteSignal.ADVISORY_BLOCKED
    return RouteSignal(max(int(s) for s in active))


def validate_route_signal(value: object) -> RouteSignal:
    """Reject off-vocabulary final verdicts (P0 item 5).

    Raises :class:`OffVocabularyVerdict` for anything outside the closed set --
    including constitutional verdicts and empty/None values. Callers must not
    catch and default this; a verdict that cannot be named must not ship.
    """
    if isinstance(value, RouteSignal):
        return value
    try:
        return RouteSignal[str(value).strip().upper()]
    except (KeyError, ValueError, AttributeError) as exc:
        raise OffVocabularyVerdict(
            f"route signal {value!r} is not in the closed vocabulary "
            f"{ROUTE_VOCABULARY}; refusing to emit an unnamed verdict"
        ) from exc


_SIGNAL_TEXT: Final[dict[RouteSignal, str]] = {
    RouteSignal.PROCEED: "PROCEED",
    RouteSignal.CAUTION: "PROCEED WITH CAUTION",
    RouteSignal.DEFER: "DEFER",
    RouteSignal.ADVISORY_BLOCKED: "ADVISORY BLOCK",
}


def explain_signal(signal: RouteSignal) -> str:
    """Human-readable form of a route signal."""
    return _SIGNAL_TEXT[RouteSignal(signal)]


def render_routing_note(
    final: RouteSignal,
    *,
    band: str,
    decision_class: str,
    chronic_fatigue: bool,
    telemetry_status: str,
    matrix: RouteSignal,
    matrix_reason: str,
    ceiling: RouteSignal,
    g_ceiling: RouteSignal | None = None,
    g_value: float | None = None,
    g_threshold: float | None = None,
) -> str:
    """Render the routing note FROM the final structured verdict (P0 item 6).

    The note is derived from the same values that produced the signal, so it
    cannot contradict it. The repaired defect: a hand-written string claimed
    "C5 blocked during chronic fatigue" while the emitted signal was DEFER.

    The leading token is always ``<CLASS> + <BAND> -> <FINAL>``, which is what
    ``test_note_never_contradicts_signal`` asserts over the full cross-product.
    """
    final = RouteSignal(final)
    parts: list[str] = [
        f"{decision_class} + {band} -> {final.name} ({explain_signal(final)})."
    ]

    if matrix_reason == "C5_CHRONIC_FATIGUE":
        parts.append(
            "C5 requires OPTIMAL with no chronic fatigue; chronic fatigue is "
            "active, so C5 is blocked."
        )
    elif matrix_reason == "UNKNOWN_DECISION_CLASS":
        parts.append(
            f"Decision class {decision_class!r} is not in {DECISION_CLASSES}; "
            "failed closed to ADVISORY_BLOCKED."
        )
    elif matrix_reason == "UNKNOWN_BAND":
        parts.append(
            f"Band {band!r} is not in {BANDS}; failed closed to ADVISORY_BLOCKED."
        )
    else:
        parts.append(f"Matrix verdict {matrix.name} for {decision_class} at {band}.")

    if ceiling > matrix:
        parts.append(
            f"Telemetry '{telemetry_status}' tightened {matrix.name} -> {ceiling.name}."
        )
    elif ceiling < matrix:
        parts.append(
            f"Telemetry '{telemetry_status}' ceiling {ceiling.name} did not relax "
            f"the stricter matrix verdict {matrix.name}."
        )

    if g_ceiling is not None:
        g_txt = f"{g_value:.3f}" if isinstance(g_value, (int, float)) else "n/a"
        thr_txt = f"{g_threshold}" if g_threshold is not None else "n/a"
        parts.append(
            f"Governance capacity G={g_txt} < SABAR threshold {thr_txt} "
            f"imposes a {g_ceiling.name} ceiling for {decision_class}."
        )

    tightened = final > matrix
    parts.append(
        "Composition = max(matrix, telemetry ceiling"
        + (", governance ceiling" if g_ceiling is not None else "")
        + f") = {final.name}; "
        + ("uncertainty tightened the verdict." if tightened
           else "no contributor relaxed the matrix verdict.")
    )
    return " ".join(parts)
