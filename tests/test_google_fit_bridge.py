import importlib
import importlib.util

import pytest

# The Fit bridge was retired 2026-09-29 (scripts/google_fit_bridge.py and
# google_fit_auth_helper.py deleted), but this module imported it at top level,
# which aborted `make test` COLLECTION before a single test ran — the whole suite
# was unrunnable while reporting nothing. Skip with a reason instead: the file is
# kept as evidence of what the bridge was contractually required to do, so a future
# sensor lane can restore coverage rather than reinvent it.
# Reconcile this retirement with F13's zero-manual law: no flow may require the
# sovereign to run an injector by hand (trace HRFID-20260929).
_google_fit_bridge = importlib.util.find_spec("scripts.google_fit_bridge")
if _google_fit_bridge is None:
    raise pytest.skip(
        "google_fit_bridge retired 2026-09-29 — sensor path has no producer; "
        "restore the module or delete this file deliberately",
        allow_module_level=True,
    )

from scripts import google_fit_bridge  # noqa: E402  (import after the guard)


class Response:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.skip(reason="google_fit_bridge is a stub — awaiting sovereign OAuth configuration")
def test_missing_observations_are_not_fabricated(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: Response({"bucket": []}))
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: Response({"session": []}))

    assert google_fit_bridge.get_google_fit_data("token") == {
        "steps": None,
        "sleep_hours": None,
    }


@pytest.mark.skip(reason="google_fit_bridge is a stub — awaiting sovereign OAuth configuration")
def test_zero_steps_remains_a_real_observation(monkeypatch):
    steps = {"bucket": [{"dataset": [{"point": [{"value": [{"intVal": 0}]}]}]}]}
    sleep = {
        "session": [{
            "activityType": 72,
            "startTimeMillis": "0",
            "endTimeMillis": "28800000",
        }]
    }
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: Response(steps))
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: Response(sleep))

    assert google_fit_bridge.get_google_fit_data("token") == {
        "steps": 0,
        "sleep_hours": 8.0,
    }
