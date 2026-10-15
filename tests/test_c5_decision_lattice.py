"""Adversarial tests for the canonical WELL C-class decision lattice.

Directive: WELL::SEVERITY_INVERSION_REPAIR::2026-10-14
           AUTHORITY: ARIF · MODE: REPAIR_FIRST · VERDICT: HOLD_PENDING_TESTS

P0 item 7: adversarial tests for all C5 branches.

KILL CRITERION under test (verbatim from the directive):

    Any path where weaker telemetry changes a stricter verdict into a more
    permissive verdict: VOID.

`test_kill_criterion_telemetry_never_relaxes` enumerates the full cross-product
of band x decision-class x chronic-fatigue and asserts that weakening the
telemetry can only tighten the outcome. If that test goes red, the repair has
regressed and the directive says VOID -- do not ship.

These tests also bind the prose matrix in ``prompts/__init__.py`` to the
executable table in ``decision_lattice.py``, so the two cannot silently
diverge again (the defect that produced C5+STABLE -> DEFER against a spec
of BLOCK).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import decision_lattice as dl
from decision_lattice import RouteSignal

WELL_ROOT = Path(__file__).resolve().parents[1]

BAND_ORDER = ("OPTIMAL", "STABLE", "DEGRADED", "CRITICAL")
ALL_BANDS = BAND_ORDER
ALL_CLASSES = ("C1", "C2", "C3", "C4", "C5")

# Prose label -> wire value. The spec table writes BLOCK; the wire vocabulary
# is ADVISORY_BLOCKED.
PROSE_TO_SIGNAL = {
    "PROCEED": RouteSignal.PROCEED,
    "DEFER": RouteSignal.DEFER,
    "BLOCK": RouteSignal.ADVISORY_BLOCKED,
}

TELEMETRY_STATUSES = ("verified", "behavioral", "operator_reported", "unknown")


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────


def _parse_prose_matrix() -> dict[str, dict[str, RouteSignal]]:
    """Parse THE C-CLASS THRESHOLD MATRIX out of prompts/__init__.py.

    Rows that do not consist entirely of known prose labels are ignored, so
    unrelated box-drawing tables in the same file cannot corrupt the parse.
    """
    text = (WELL_ROOT / "prompts" / "__init__.py").read_text(encoding="utf-8")
    rows: dict[str, dict[str, RouteSignal]] = {}
    for line in text.splitlines():
        if "│" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("│").split("│")]
        if len(cells) != 5:
            continue
        head = cells[0].replace("*", "").strip()
        if not head:
            continue
        try:
            signals = [PROSE_TO_SIGNAL[c.replace("*", "").strip().upper()] for c in cells[1:]]
        except KeyError:
            continue
        for klass in (c.strip().upper() for c in head.split("/")):
            if klass:
                rows[klass] = dict(zip(BAND_ORDER, signals))
    return rows


def _find_key(obj, key):
    """Locate `key` anywhere in a nested federation output envelope."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None


# ─────────────────────────────────────────────────────────────────────────────
# vocabulary (P0 items 4 + 5)
# ─────────────────────────────────────────────────────────────────────────────


def test_route_vocabulary_is_closed_and_ordered():
    assert dl.ROUTE_VOCABULARY == ("PROCEED", "CAUTION", "DEFER", "ADVISORY_BLOCKED")
    assert RouteSignal.PROCEED < RouteSignal.CAUTION < RouteSignal.DEFER < RouteSignal.ADVISORY_BLOCKED


def test_constitutional_verdicts_are_not_route_signals():
    """WELL is ADVISORY_ONLY: it must not emit arifOS verdicts as decisions."""
    for constitutional in ("SEAL", "HOLD", "VOID", "SABAR"):
        assert constitutional in dl.CONSTITUTIONAL_VERDICTS
        assert constitutional not in dl.ROUTE_VOCABULARY
        with pytest.raises(dl.OffVocabularyVerdict):
            dl.validate_route_signal(constitutional)


@pytest.mark.parametrize(
    "bad",
    ["", "   ", None, "BLOCK", "OK", "READY", "caution!", 0, 3, "None",
     "PROCEEDED", "ADVISORY_BLOCK"],
)
def test_off_vocabulary_final_verdicts_are_rejected(bad):
    """P0 item 5: reject off-vocabulary final verdicts rather than coerce them."""
    with pytest.raises(dl.OffVocabularyVerdict):
        dl.validate_route_signal(bad)


def test_validate_accepts_every_member_of_the_closed_set():
    for name in dl.ROUTE_VOCABULARY:
        assert dl.validate_route_signal(name) is RouteSignal[name]
        assert dl.validate_route_signal(name.lower()) is RouteSignal[name]


def test_legacy_verdict_map_is_band_complete():
    assert set(dl.LEGACY_VERDICT_BY_BAND) == set(ALL_BANDS)


# ─────────────────────────────────────────────────────────────────────────────
# band derivation
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "score,expected",
    [
        (10.0, "OPTIMAL"), (7.45, "OPTIMAL"), (7.0, "OPTIMAL"),
        (6.99, "STABLE"), (5.0, "STABLE"),
        (4.99, "DEGRADED"), (3.0, "DEGRADED"),
        (2.99, "CRITICAL"), (0.0, "CRITICAL"),
    ],
)
def test_band_from_score_thresholds(score, expected):
    assert dl.band_from_score(score) == expected


# ─────────────────────────────────────────────────────────────────────────────
# P0 item 1: the executable matrix IS the canonical matrix
# ─────────────────────────────────────────────────────────────────────────────


def test_matrix_matches_prose_spec():
    """Bind the prose table to the executable one.

    This is the regression guard for the duplicate-mode-table defect: the prose
    spec said C5+STABLE = BLOCK while the inline code emitted DEFER.
    """
    prose = _parse_prose_matrix()
    assert set(prose) == set(ALL_CLASSES), (
        f"prose matrix parse incomplete: got {sorted(prose)}"
    )
    for klass in ALL_CLASSES:
        for band in ALL_BANDS:
            assert dl.C_CLASS_MATRIX[klass][band] == prose[klass][band], (
                f"executable matrix diverges from prose spec at {klass}+{band}: "
                f"code={dl.C_CLASS_MATRIX[klass][band].name} spec={prose[klass][band].name}"
            )


def test_matrix_is_total_over_classes_and_bands():
    for klass in ALL_CLASSES:
        assert set(dl.C_CLASS_MATRIX[klass]) == set(ALL_BANDS)


# ─────────────────────────────────────────────────────────────────────────────
# P0 item 7: adversarial coverage of ALL C5 branches
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("band", ALL_BANDS)
def test_c5_with_chronic_fatigue_blocks_in_every_band(band):
    """The repaired defect: no branch previously mapped chronic_fatigue to a
    block. The OPTIMAL branch emitted DEFER while its own routing note claimed
    'C5 blocked during chronic fatigue'.
    """
    signal, reason = dl.matrix_signal(band, "C5", chronic_fatigue=True)
    assert signal is RouteSignal.ADVISORY_BLOCKED, (
        f"C5 + chronic_fatigue at {band} must block, got {signal.name}"
    )
    assert reason == "C5_CHRONIC_FATIGUE"


@pytest.mark.parametrize(
    "band,expected",
    [
        ("OPTIMAL", RouteSignal.PROCEED),
        ("STABLE", RouteSignal.ADVISORY_BLOCKED),
        ("DEGRADED", RouteSignal.ADVISORY_BLOCKED),
        ("CRITICAL", RouteSignal.ADVISORY_BLOCKED),
    ],
)
def test_c5_without_chronic_fatigue(band, expected):
    """C5 is the strictest gate: proceed only if OPTIMAL with no chronic fatigue."""
    signal, reason = dl.matrix_signal(band, "C5", chronic_fatigue=False)
    assert signal is expected
    assert reason == "MATRIX"


def test_c5_chronic_fatigue_survives_verified_telemetry():
    """Adversarial: the strongest possible evidence must not unblock C5 while
    chronic fatigue is active. Verified telemetry removes the ceiling; the
    matrix verdict alone must still block.
    """
    band = "OPTIMAL"
    matrix, reason = dl.matrix_signal(band, "C5", chronic_fatigue=True)
    final = dl.compose(matrix, dl.telemetry_ceiling("verified"), None)
    assert reason == "C5_CHRONIC_FATIGUE"
    assert final is RouteSignal.ADVISORY_BLOCKED


@pytest.mark.parametrize("klass", ALL_CLASSES)
@pytest.mark.parametrize("band", ALL_BANDS)
def test_no_class_band_pair_ever_proceeds_at_critical(klass, band):
    """CRITICAL blocks every decision class without exception."""
    if band != "CRITICAL":
        pytest.skip("CRITICAL-only invariant")
    for chronic in (False, True):
        signal, _ = dl.matrix_signal(band, klass, chronic_fatigue=chronic)
        assert signal is RouteSignal.ADVISORY_BLOCKED


def test_c4_and_c5_are_at_least_as_strict_as_c1_through_c3():
    """Monotonicity in the class axis: raising the decision class may only
    tighten, never relax, at the same band.
    """
    for band in ALL_BANDS:
        ordered = [
            dl.matrix_signal(band, klass, chronic_fatigue=False)[0]
            for klass in ALL_CLASSES
        ]
        for weaker, stronger in zip(ordered, ordered[1:]):
            assert stronger >= weaker, (
                f"{band}: {stronger.name} is more permissive than {weaker.name}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# fail-closed behaviour
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad_class", ["", None, "C0", "C6", "c9", "CRITICAL", "5"])
def test_unknown_decision_class_fails_closed(bad_class):
    signal, reason = dl.matrix_signal("OPTIMAL", bad_class)
    assert signal is RouteSignal.ADVISORY_BLOCKED
    assert reason == "UNKNOWN_DECISION_CLASS"


@pytest.mark.parametrize("bad_band", ["", None, "LIMITED", "UNKNOWN", "OPTIMAL*", "OPTIMALLY", "FINE"])
def test_unknown_band_fails_closed(bad_band):
    signal, reason = dl.matrix_signal(bad_band, "C1")
    assert signal is RouteSignal.ADVISORY_BLOCKED
    assert reason == "UNKNOWN_BAND"


def test_class_and_band_folding_is_bounded_to_the_closed_set():
    """Case/whitespace folding is safe HERE because the identifier selects from
    a closed set and an unrecognised value fails CLOSED to ADVISORY_BLOCKED --
    folding can never widen permissiveness.

    Contrast ``telemetry_ceiling``, which is deliberately exact-match: that
    token grants the MOST permissive ceiling, so folding it would widen what
    can authorise PROCEED.
    """
    assert dl.matrix_signal("optimal", "c5")[0] is RouteSignal.PROCEED
    assert dl.matrix_signal("  Optimal  ", " C5 ")[0] is RouteSignal.PROCEED
    assert dl.matrix_signal("OPTIMAL", "C5", chronic_fatigue=True)[0] is RouteSignal.ADVISORY_BLOCKED
    # Lookalikes that do not fold onto a member still fail closed.
    assert dl.matrix_signal("OPTIMAL*", "C5")[0] is RouteSignal.ADVISORY_BLOCKED
    assert dl.matrix_signal("OPTIMALLY", "C5")[0] is RouteSignal.ADVISORY_BLOCKED


def test_route_signal_folding_is_bounded_the_same_way():
    assert dl.validate_route_signal(" defer ") is RouteSignal.DEFER
    assert dl.validate_route_signal("DEFER") is RouteSignal.DEFER
    with pytest.raises(dl.OffVocabularyVerdict):
        dl.validate_route_signal("DEFERRED")


def test_compose_with_no_active_contributor_fails_closed():
    assert dl.compose(None, None) is RouteSignal.ADVISORY_BLOCKED
    assert dl.compose() is RouteSignal.ADVISORY_BLOCKED


# ─────────────────────────────────────────────────────────────────────────────
# P0 items 2 + 3: monotonic composition, telemetry tightens only
# ─────────────────────────────────────────────────────────────────────────────


def test_compose_takes_the_strictest_contributor():
    assert dl.compose(RouteSignal.PROCEED, RouteSignal.CAUTION) is RouteSignal.CAUTION
    assert dl.compose(RouteSignal.DEFER, RouteSignal.CAUTION) is RouteSignal.DEFER
    assert dl.compose(RouteSignal.ADVISORY_BLOCKED, RouteSignal.PROCEED) is RouteSignal.ADVISORY_BLOCKED
    assert dl.compose(RouteSignal.PROCEED, None, RouteSignal.DEFER) is RouteSignal.DEFER


def test_compose_is_commutative_and_idempotent():
    signals = [RouteSignal.PROCEED, RouteSignal.CAUTION, RouteSignal.DEFER, RouteSignal.ADVISORY_BLOCKED]
    for a in signals:
        assert dl.compose(a, a) is a
        for b in signals:
            assert dl.compose(a, b) is dl.compose(b, a)


@pytest.mark.parametrize("status", TELEMETRY_STATUSES)
def test_telemetry_ceiling_never_exceeds_caution_for_unverified(status):
    ceiling = dl.telemetry_ceiling(status)
    if status == "verified":
        assert ceiling is RouteSignal.PROCEED
    else:
        assert ceiling is RouteSignal.CAUTION


@pytest.mark.parametrize("bad", [None, "", "VERIFIED", "Verified ", "trusted", "MEASURED"])
def test_unrecognised_telemetry_status_fails_closed(bad):
    """Anything not exactly 'verified' may not support PROCEED."""
    assert dl.telemetry_ceiling(bad) is RouteSignal.CAUTION


def test_kill_criterion_telemetry_never_relaxes():
    """THE KILL CRITERION, as an exhaustive property test.

    For every band x class x chronic-fatigue combination, weakening telemetry
    from 'verified' to any weaker status must never produce a more permissive
    final signal. This is the exact defect the directive names as VOID: the
    former cap assigned route_signal = "CAUTION", relaxing DEFER and
    ADVISORY_BLOCKED.
    """
    violations = []
    for band in ALL_BANDS:
        for klass in ALL_CLASSES:
            for chronic in (False, True):
                matrix, _ = dl.matrix_signal(band, klass, chronic_fatigue=chronic)
                baseline = dl.compose(matrix, dl.telemetry_ceiling("verified"), None)
                for weaker in ("behavioral", "operator_reported", "unknown", None, "garbage"):
                    outcome = dl.compose(matrix, dl.telemetry_ceiling(weaker), None)
                    if outcome < baseline:
                        violations.append(
                            f"{klass}+{band} chronic={chronic}: telemetry "
                            f"{weaker!r} relaxed {baseline.name} -> {outcome.name}"
                        )
    assert not violations, "KILL CRITERION violated:\n" + "\n".join(violations)


def test_regression_at2_c5_chronic_fatigue_is_not_caution():
    """AT-2 from the audit: C5 + chronic fatigue must be a block, never CAUTION.

    Reproduces the reported defect end-to-end at the lattice level, including
    the unverified-telemetry condition that was live at the time of the audit.
    """
    for telemetry in TELEMETRY_STATUSES:
        matrix, reason = dl.matrix_signal("OPTIMAL", "C5", chronic_fatigue=True)
        final = dl.compose(matrix, dl.telemetry_ceiling(telemetry), None)
        assert final is RouteSignal.ADVISORY_BLOCKED, (
            f"AT-2 regression: telemetry={telemetry} produced {final.name}"
        )
        assert reason == "C5_CHRONIC_FATIGUE"


def test_g_fold_ceiling_only_tightens_c4_and_c5():
    """The former G-fold fired only when route_signal was already PROCEED, so
    it could not act after another contributor had tightened. As a ceiling it
    now composes monotonically.
    """
    threshold = 0.5
    # Below threshold, C4/C5 get a DEFER ceiling.
    assert dl.g_fold_ceiling(0.1, threshold, "C5") is RouteSignal.DEFER
    assert dl.g_fold_ceiling(0.1, threshold, "C4") is RouteSignal.DEFER
    # Inactive for lower classes and when G is healthy.
    assert dl.g_fold_ceiling(0.1, threshold, "C3") is None
    assert dl.g_fold_ceiling(0.9, threshold, "C5") is None
    # Inactive / fails safe on non-numeric G.
    assert dl.g_fold_ceiling(None, threshold, "C5") is None
    assert dl.g_fold_ceiling("0.1", threshold, "C5") is None
    assert dl.g_fold_ceiling(True, threshold, "C5") is None


def test_g_fold_never_relaxes_an_already_strict_verdict():
    matrix = RouteSignal.ADVISORY_BLOCKED
    final = dl.compose(matrix, dl.telemetry_ceiling("verified"), dl.g_fold_ceiling(0.1, 0.5, "C5"))
    assert final is RouteSignal.ADVISORY_BLOCKED


# ─────────────────────────────────────────────────────────────────────────────
# P0 item 6: notes are generated FROM the final structured verdict
# ─────────────────────────────────────────────────────────────────────────────


def test_note_never_contradicts_signal():
    """The repaired defect: a hand-written note claimed 'C5 blocked' while the
    emitted signal was DEFER. The note is now rendered from the final value, so
    its leading token must always name that value.
    """
    for band in ALL_BANDS:
        for klass in ALL_CLASSES:
            for chronic in (False, True):
                matrix, reason = dl.matrix_signal(band, klass, chronic_fatigue=chronic)
                for telemetry in TELEMETRY_STATUSES:
                    ceiling = dl.telemetry_ceiling(telemetry)
                    g_ceiling = dl.g_fold_ceiling(0.1, 0.5, klass)
                    final = dl.compose(matrix, ceiling, g_ceiling)
                    note = dl.render_routing_note(
                        final,
                        band=band,
                        decision_class=klass,
                        chronic_fatigue=chronic,
                        telemetry_status=telemetry,
                        matrix=matrix,
                        matrix_reason=reason,
                        ceiling=ceiling,
                        g_ceiling=g_ceiling,
                        g_value=0.1,
                        g_threshold=0.5,
                    )
                    head = f"{klass} + {band} -> {final.name}"
                    assert note.startswith(head), (
                        f"note does not name the final signal: {note!r}"
                    )
                    # A note may never claim a block while emitting a weaker signal.
                    if final is not RouteSignal.ADVISORY_BLOCKED:
                        assert "is blocked" not in note and "-> ADVISORY_BLOCKED" not in note


def test_note_names_chronic_fatigue_as_the_reason_when_it_blocks():
    note = dl.render_routing_note(
        RouteSignal.ADVISORY_BLOCKED,
        band="OPTIMAL",
        decision_class="C5",
        chronic_fatigue=True,
        telemetry_status="verified",
        matrix=RouteSignal.ADVISORY_BLOCKED,
        matrix_reason="C5_CHRONIC_FATIGUE",
        ceiling=RouteSignal.PROCEED,
    )
    assert "chronic fatigue" in note.lower()
    assert "C5 + OPTIMAL -> ADVISORY_BLOCKED" in note


def test_note_states_when_uncertainty_tightened_rather_than_relaxed():
    note = dl.render_routing_note(
        RouteSignal.ADVISORY_BLOCKED,
        band="STABLE",
        decision_class="C5",
        chronic_fatigue=False,
        telemetry_status="unknown",
        matrix=RouteSignal.ADVISORY_BLOCKED,
        matrix_reason="MATRIX",
        ceiling=RouteSignal.CAUTION,
    )
    assert "did not relax" in note


# ─────────────────────────────────────────────────────────────────────────────
# integration: the live tool must emit the repaired semantics
# ─────────────────────────────────────────────────────────────────────────────


def test_tool_c5_chronic_fatigue_emits_advisory_blocked():
    """End-to-end AT-2 through the real MCP tool entry point.

    Pre-repair this returned route_signal="CAUTION" with a note admitting the
    uncapped signal was DEFER -- two divergences from the spec's BLOCK.
    """
    import server

    result = server.well_assess_homeostasis(
        mode="fatigue",
        decision_class="C5",
        chronic_fatigue=True,
        sleep_debt_days=3,
        decision_fatigue=0.7,
        stress_load=0.8,
        subject="at2-regression-synthetic",
    )
    signal = _find_key(result, "route_signal")
    decision = _find_key(result, "decision_signal")
    note = _find_key(result, "routing_note")

    assert signal == "ADVISORY_BLOCKED", f"AT-2 not repaired: route_signal={signal!r}"
    assert decision == signal, "decision_signal must equal route_signal"
    assert "C5 + " in note and "-> ADVISORY_BLOCKED" in note, (
        f"note does not name the emitted signal: {note!r}"
    )
    # The legacy cap text must be gone: it described a relaxation.
    assert "capped to CAUTION" not in note


def test_tool_emits_only_closed_vocabulary_route_signals():
    """P0 item 5 across a sweep of the real tool, both modes."""
    import server

    for mode in ("fatigue", "sleep"):
        for klass in ALL_CLASSES:
            for chronic in (False, True):
                result = server.well_assess_homeostasis(
                    mode=mode,
                    decision_class=klass,
                    chronic_fatigue=chronic,
                    sleep_hours=6.0,
                    sleep_debt_days=2,
                    decision_fatigue=0.5,
                    stress_load=0.6,
                    cognitive_clarity=6.0,
                    subject="vocab-sweep-synthetic",
                )
                signal = _find_key(result, "route_signal")
                assert signal in dl.ROUTE_VOCABULARY, (
                    f"{mode}/{klass}/chronic={chronic} emitted off-vocabulary "
                    f"route_signal {signal!r}"
                )


def test_tool_separates_decision_from_advisory_and_band():
    """P0 item 4: three concerns, three fields."""
    import server

    result = server.well_assess_homeostasis(
        mode="fatigue",
        decision_class="C5",
        chronic_fatigue=True,
        sleep_debt_days=3,
        decision_fatigue=0.7,
        stress_load=0.8,
        subject="separation-synthetic",
    )
    decision = _find_key(result, "decision_signal")
    advisory = _find_key(result, "advisory_signal")
    band = _find_key(result, "homeostasis_band")

    assert decision in dl.ROUTE_VOCABULARY
    assert advisory is not None and advisory != decision, (
        "advisory_signal must be a distinct vocabulary from the decision"
    )
    assert band in ALL_BANDS, (
        f"homeostasis_band must carry the unqualified physiological read, got {band!r}"
    )


def test_tool_does_not_emit_constitutional_verdict_as_decision():
    """The decision field must never carry SEAL/HOLD/VOID/SABAR."""
    import server

    result = server.well_assess_homeostasis(
        mode="fatigue",
        decision_class="C5",
        chronic_fatigue=True,
        sleep_debt_days=3,
        subject="constitutional-leak-synthetic",
    )
    for field in ("route_signal", "decision_signal"):
        value = _find_key(result, field)
        assert value not in dl.CONSTITUTIONAL_VERDICTS, (
            f"{field} carries a constitutional verdict: {value!r}"
        )
