FROM python:3.12-slim

WORKDIR /app

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /usr/local/bin/uv

# Copy project files. state.json and events.jsonl are mutable runtime state.
COPY pyproject.toml server.py schema.json ./
COPY .well-known ./.well-known

# FIX: Copy contracts directory properly (not contracts/ which copies contents)
COPY contracts ./contracts/

# Install dependencies
RUN uv pip install --system fastmcp>=2.0 uvicorn \
    && python -c 'import json, datetime; state = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "identity": "WELL", "role": "Body / Human Intelligence", "authority": "REFLECT_ONLY", "delta_s": 0.0, "peace2": 1.0, "kappa_r": 0.95, "rasa": True, "amanah": "LOCK", "operator_id": "arif", "truth_status": "UNVERIFIED", "metrics": {}, "well_score": 50, "floors_violated": []}; open("state.json", "w").write(json.dumps(state, indent=2)); open("events.jsonl", "a").close()'

# Create non-root user for runtime security
RUN useradd -m -u 1000 welluser && chown -R welluser:welluser /app
USER welluser

ENV WELL_VAULT_PATH=/tmp/well_ledger.jsonl
ENV WELL_STATE_PATH=/app/state.json
ENV WELL_EVENTS_PATH=/app/events.jsonl
ENV HOST=0.0.0.0
ENV PORT=8083
ENV LOG_LEVEL=info
ENV FEDERATION_SOMATIC_BOUNDARY=1

EXPOSE 8083

CMD ["python", "server.py"]
