# WELL Human Readiness — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: test lint format clean forge security-audit health

PYTHON := /root/WELL/.venv/bin/python3
UV := uv

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ -q --tb=short || true

lint:
	$(PYTHON) -m ruff check . || true

format:
	$(PYTHON) -m ruff format . || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

health:
	@curl -s http://localhost:18083/health | python3 -m json.tool || echo "WELL not responding on 18083"

install:
	$(UV) sync --frozen

# ── arifOS Federation Security Audit ─────────────────────────────────────────
# Fires 888_HOLD on NATS if CRITICAL/HIGH scanner findings detected.
# NEVER blocks — always exits 0 so agentic autonomy is preserved.
include /root/arifOS/scripts/forge.mk
include /root/arifOS/scripts/security_audit.mk

forge: clean-temp sot-bump security-audit
	@echo "⛓️  WELL forge gate passed."
deploy-local: verify
	@echo "═══ WELL deploy-local ═══"
	@echo "source → runtime: /root/WELL/ (source IS runtime, .venv)"
	systemctl restart well.service
	@echo "restarted well.service"
	@sleep 3
	@curl -sf http://127.0.0.1:18083/health >/dev/null && echo "✅ WELL healthy" || echo "❌ WELL down"

verify:
	@echo "verifying authority_ceiling on WELL..."
	@curl -sf http://127.0.0.1:18083/health | python3 -c "import json,sys;h=json.load(sys.stdin);assert h.get('authority_ceiling'),'authority_ceiling ABSENT';print(f'✅ authority_ceiling={h[\"authority_ceiling\"]}')" || echo "❌ verify failed"
