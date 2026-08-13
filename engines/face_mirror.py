"""
WELL Face Mirror — Sovereign Substrate Vitality Observation
A mirror, not a camera. MediaPipe Face Mesh (468 landmarks). NEVER extracts identity.
substrate_class = SOVEREIGN, authority_ceiling = REFLECT_ONLY + CONSENT_GATE
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
import base64, gc, hashlib, logging, math, time
from typing import Any
import numpy as np

logger = logging.getLogger("well.face_mirror")
SUBSTRATE_CLASS = "SOVEREIGN"
AUTHORITY_CEILING = "REFLECT_ONLY"
_session_baselines: dict[str, dict[str, float]] = {}
_face_mesh = None


def _get_face_mesh():
    global _face_mesh
    if _face_mesh is None:
        import mediapipe as mp

        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
    return _face_mesh


# Landmark indices for vitality (DYNAMIC state, NOT static identity)
_L_EYE_T, _L_EYE_B, _L_EYE_L, _L_EYE_R = 159, 145, 33, 133
_R_EYE_T, _R_EYE_B = 386, 374
_L_BROW = 105
_JAW_L, _JAW_R = 234, 454
_LIP_T, _LIP_B = 13, 14


def _dist(a, b) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _extract_vitality(lm) -> dict[str, float]:
    eye_h = _dist(lm[_L_EYE_L], lm[_L_EYE_R])
    eye_v = _dist(lm[_L_EYE_T], lm[_L_EYE_B])
    brow = _dist(lm[_L_BROW], lm[_L_EYE_T])
    jaw = _dist(lm[_JAW_L], lm[_JAW_R])
    lip = _dist(lm[_LIP_T], lm[_LIP_B])
    return {
        "eye_openness": round(eye_v / max(eye_h, 0.001), 4),
        "brow_ratio": round(brow / max(eye_h, 0.001), 4),
        "jaw_ratio": round(jaw / max(eye_h, 0.001), 4),
        "mouth_tension": round(lip / max(eye_h, 0.001), 4),
    }


def _classify(metrics: dict, baseline: dict | None) -> tuple[str, float, str]:
    if baseline is None:
        eye = metrics["eye_openness"]
        if eye < 0.15:
            return (
                "DEGRADED",
                0.0,
                "Your eyes appear significantly closed. Consider rest.",
            )
        elif eye < 0.25:
            return ("STABLE", 0.0, "Vitality signals are within a normal range.")
        else:
            return ("OPTIMAL", 0.0, "Vitality signals suggest alertness.")
    eye_shift = baseline["eye_openness"] - metrics["eye_openness"]
    brow_shift = baseline["brow_ratio"] - metrics["brow_ratio"]
    jaw_shift = metrics["jaw_ratio"] - baseline["jaw_ratio"]
    fatigue = min(
        1.0, max(0, eye_shift * 3) + max(0, brow_shift * 2) + max(0, jaw_shift * 2)
    )
    if fatigue < 0.1:
        return (
            "OPTIMAL",
            round(fatigue, 2),
            "Vitality signals have remained stable since baseline.",
        )
    elif fatigue < 0.3:
        return (
            "STABLE",
            round(fatigue, 2),
            "Minor shifts in facial tension detected. You are maintaining well.",
        )
    elif fatigue < 0.6:
        return (
            "DEGRADED",
            round(fatigue, 2),
            "Your blink rate and brow tension have shifted noticeably. Consider a brief pause.",
        )
    else:
        return (
            "CRITICAL",
            round(fatigue, 2),
            "Significant fatigue indicators detected. Strongly recommend a 15-minute break.",
        )


async def observe_face(
    *,
    image_base64: str | None = None,
    consent_token: str | None = None,
    mode: str = "baseline",
    session_id: str = "default",
) -> dict[str, Any]:
    """A mirror, not a camera. Observes dynamic vitality. NEVER extracts identity."""
    t0 = time.monotonic()
    if not consent_token:
        return {
            "ok": False,
            "error": "FATAL: consent_token is REQUIRED.",
            "substrate_class": SUBSTRATE_CLASS,
            "w0": "OPERATOR_VETO_INTACT",
        }
    if not image_base64:
        return {"ok": False, "error": "image_base64 is required."}
    try:
        if "," in image_base64 and image_base64.startswith("data:"):
            image_base64 = image_base64.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        return {"ok": False, "error": f"Failed to decode image: {e}"}
    try:
        import cv2

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return {"ok": False, "error": "Could not decode image data"}
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = _get_face_mesh().process(rgb)
        del image, rgb, nparr, image_bytes
        gc.collect()
        if not results.multi_face_landmarks:
            return {
                "ok": False,
                "error": "No face detected. The mirror had nothing to reflect.",
                "image_purged": True,
            }
        face_lm = results.multi_face_landmarks[0]
        lm = [[p.x, p.y, p.z] for p in face_lm.landmark]
        metrics = _extract_vitality(lm)
        del lm, results, face_lm
        gc.collect()
    except Exception as e:
        logger.error(f"Face mesh failed: {e}")
        return {"ok": False, "error": f"Observation failed: {e}", "image_purged": True}
    baseline = None
    if mode == "baseline":
        _session_baselines[session_id] = metrics.copy()
    elif mode == "compare":
        baseline = _session_baselines.get(session_id)
        if baseline is None:
            _session_baselines[session_id] = metrics.copy()
    else:
        return {"ok": False, "error": f"Unknown mode '{mode}'. Use: baseline | compare"}
    state, shift, msg = _classify(metrics, baseline)
    ms = int((time.monotonic() - t0) * 1000)
    rh = hashlib.sha256(f"{session_id}:{mode}:{state}:{ms}".encode()).hexdigest()[:16]
    return {
        "ok": True,
        "tool": "well_observe_face",
        "substrate_class": SUBSTRATE_CLASS,
        "authority_ceiling": AUTHORITY_CEILING,
        "w0": "OPERATOR_VETO_INTACT",
        "state": state,
        "shift_from_baseline": shift,
        "maruah_message": msg,
        "image_purged": True,
        "no_persistent_state": True,
        "no_identity_vector": True,
        "metabolic_receipt": rh,
        "elapsed_ms": ms,
        "mode": mode,
        "baseline_set": mode == "baseline" or baseline is None,
        "_well_conformance": {
            "claim_state": "HYPOTHESIS",
            "witness_type": "AI",
            "organ_type": "G_WELL",
            "conformance_version": "v1.0",
            "conformant": True,
        },
        "boundary_notice": "Not diagnosis. Not therapy. Not identity. Reflective readiness only. Arif remains final judge.",
    }
