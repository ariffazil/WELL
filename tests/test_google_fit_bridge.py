from scripts import google_fit_bridge


class Response:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_missing_observations_are_not_fabricated(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: Response({"bucket": []}))
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: Response({"session": []}))

    assert google_fit_bridge.get_google_fit_data("token") == {
        "steps": None,
        "sleep_hours": None,
    }


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
