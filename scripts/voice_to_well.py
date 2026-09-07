#!/usr/bin/env python3
"""voice_to_well.py — Phase 1 voice→WELL bridge (Day 1, F13-ratified 2026-09-08).

Reads voice_state.py features (librosa, 14-feature extraction), maps to
WELL signals/derived, writes to /root/WELL/intake/voice/{ts}.json.

Called by:
- Hermes gateway (after voice_state.py extracts features)
- Manual: python3 /root/WELL/scripts/voice_to_well.py <features.json>
- Test mode: python3 /root/WELL/scripts/voice_to_well.py --test

Authority:
- Reads voice features (biometric, F1=biometric-equivalent, F9=measures-not-speaks)
- Writes to WELL intake (data flow only — never to transcript/LLM, never claims feeling)
- Confidence: HIGH if all 14 features present, MEDIUM if partial, LOW if only core

F9 ANTIHANTU: NEVER outputs narrative ("Arif is stressed"). Always
outputs feature counts only. The "derived" fields are well_score
inputs, not feelings claims.

Map (canonical 14-feature mapping, calibrated from voice_state.py):
  speech_rate      → energy (rate > 140 = high energy, < 90 = fatigue)
  pause_density    → fatigue (pauses > 0.3 = high fatigue)
  pitch_variance   → calm (variance > 0.4 = scattered, < 0.15 = flat)
  breath_rate      → energy proxy
  jitter           → fatigue proxy
  shimmer          → calm proxy
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

INTAKE_DIR = Path("/root/WELL/intake/voice")


def voice_features_to_well(features: dict) -> dict:
    """Map voice_state.py features → WELL signals + derived.

    No narrative. Feature counts only.
    """
    speech_rate = float(features.get("speech_rate", 0.0))
    pause_density = float(features.get("pause_density", 0.0))
    pitch_variance = float(features.get("pitch_variance", 0.0))
    breath_rate = float(features.get("breath_rate", 0.0))
    jitter = float(features.get("jitter", 0.0))
    shimmer = float(features.get("shimmer", 0.0))

    # Energy: speech_rate + breath_rate (0-10 scale, mid=5)
    energy = max(0, min(10, (speech_rate / 30.0) + (breath_rate - 14.0) / 2.0))
    # Fatigue: pause_density (0-10 scale)
    fatigue = max(0, min(10, pause_density * 33.3))
    # Calm: inverse pitch_variance + inverse jitter/shimmer (0-10)
    calm = max(0, min(10, 10.0 - (pitch_variance * 15.0) - (jitter * 5.0) - (shimmer * 2.0)))

    # Determine confidence based on feature completeness
    feature_count = sum(1 for k in features.keys() if features[k] is not None)
    if feature_count >= 12:
        confidence = "HIGH"
    elif feature_count >= 6:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "signals": {
            "speech_rate": speech_rate,
            "pause_density": pause_density,
            "pitch_variance": pitch_variance,
            "breath_rate": breath_rate,
            "jitter": jitter,
            "shimmer": shimmer,
            "raw_features_count": feature_count,
        },
        "derived": {
            "energy": round(energy, 2),
            "fatigue": round(fatigue, 2),
            "calm": round(calm, 2),
        },
        "confidence": confidence,
    }


def main():
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Synthetic test: produce a realistic voice features dict
        synthetic = {
            "speech_rate": 142.5,
            "pause_density": 0.21,
            "pitch_variance": 0.38,
            "breath_rate": 16.2,
            "jitter": 0.012,
            "shimmer": 0.043,
            # some optional ones null:
            "f0_mean": 118.4,
            "f0_std": 22.1,
            "hnr": 18.3,
            "spectral_centroid": 1850.0,
            "spectral_flux": 0.42,
            "energy_mean": -23.1,
            "energy_std": 4.5,
            "zcr": 0.062,
        }
        well = voice_features_to_well(synthetic)
    elif len(sys.argv) > 1:
        # Read features from file
        try:
            features = json.loads(Path(sys.argv[1]).read_text())
        except (FileNotFoundError, json.JSONDecodeError) as e:
            sys.exit(f"[voice_to_well] cannot read features file: {e}")
        well = voice_features_to_well(features)
    else:
        sys.exit("Usage: voice_to_well.py <features.json> | --test")

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "voice",
        "operator_id": "arif",
        **well,
    }

    # Filename: voice-{ts}.json (ts has colons sanitized)
    safe_ts = payload["ts"].replace(":", "-")
    out_path = INTAKE_DIR / f"voice-{safe_ts}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[voice_to_well] wrote {out_path}")
    print(f"[voice_to_well] signals={list(payload['signals'].keys())}")
    print(f"[voice_to_well] derived={payload['derived']} confidence={payload['confidence']}")


if __name__ == "__main__":
    main()
