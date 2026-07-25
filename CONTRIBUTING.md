# Contributing to WELL

> **SOT:** 2026-07-25 | **DITEMPA BUKAN DIBERI**

WELL is the substrate readiness organ of the arifOS Federation. It reflects — never diagnoses, never adjudicates.

## Before You Start

1. Read the [README](README.md) — understand REFLECT_ONLY and the ABC Trinity
2. Understand the medical boundary: `test_medical_boundary.py` is non-negotiable
3. Run `curl :18083/health` — ensure WELL is running

## Setup

```bash
git clone git@github.com:ariffazil/WELL.git && cd WELL
pip install -e .
python server.py             # starts on :18083
curl http://localhost:18083/health
```

## Making Changes

1. **Fork → Branch → Edit → Test → PR**
2. Run `pytest tests/ -q --tb=short` before pushing
3. `asyncio_mode = "auto"` — no explicit `@pytest.mark.asyncio` needed

## Boundaries

- WELL reflects — never diagnoses medical conditions
- WELL observes — never overrides human self-reporting
- `state.json` is F13 territory — only Arif writes biometric state
- REFLECT_ONLY: no tool may issue strategic judgment or authorization

## Federation

WELL is one of 7 organs. See [ariffazil/ariffazil](https://github.com/ariffazil/ariffazil) for the federation map.

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
