"""Tests — WELL::CRAVING::v1 one-word events."""

from __future__ import annotations

import pathlib
import sys
import datetime as _dt
import json
import pathlib
import sys

UTC = _dt.timezone.utc
MYT = _dt.timezone(_dt.timedelta(hours=8))

sys.path.insert(0, "/root/WELL")
from human_checkin import craving as C  # noqa: E402


def test_word_classification():
    assert C.classify_word("20") == "craving"
    assert C.classify_word(" 20 ") == "craving"
    assert C.classify_word("ok") == "survived"
    assert C.classify_word("OK") == "survived"
    assert C.classify_word("hello") is None
    assert C.classify_word("2") is None


def test_log_and_pattern_roundtrip(tmp_path):
    lp = str(tmp_path / "c.jsonl")
    C.log_event("craving", "20", log_path=lp,
                now=_dt.datetime(2026, 11, 19, 2, 30, tzinfo=MYT))
    C.log_event("survived", "ok", log_path=lp,
                now=_dt.datetime(2026, 11, 19, 3, 0, tzinfo=MYT))
    p = C.pattern(lp)
    assert p["cravings"] == 1
    assert p["survived"] == 1
    assert p["by_band"] == {"late_night": 1}


def test_event_never_claims_measured(tmp_path):
    lp = str(tmp_path / "c.jsonl")
    ev = C.log_event("craving", "20", log_path=lp)
    assert ev["provenance"] == "self_reported"
    dumped = json.dumps(ev)
    assert "verified" not in dumped
    assert "score" not in dumped


def test_corrupted_line_survives(tmp_path):
    lp = pathlib.Path(tmp_path) / "c.jsonl"
    lp.write_text("{broken\n", encoding="utf-8")
    p = C.pattern(str(lp))
    assert p["events"] == 0


def test_handle_word_actions(tmp_path):
    lp = str(tmp_path / "c.jsonl")
    a = C.handle_word("20", log_path=lp)
    assert a["action"] == "start_hold"
    assert a["minutes"] == 20
    b = C.handle_word("ok", log_path=lp)
    assert b["action"] == "mark_survived"
    assert C.handle_word("random", log_path=lp) is None


def test_empty_log_pattern(tmp_path):
    assert C.pattern(str(tmp_path / "none.jsonl"))["events"] == 0
