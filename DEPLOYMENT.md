# Deployment — WELL (Biometric & Health)

## Prerequisites

- Docker 24+ and Docker Compose v2
- 2 CPU cores, 4GB RAM
- Ports: `18083` (WELL organ)

## Quick Start

```bash
git clone https://github.com/arif-fazil/WELL.git
cd WELL
docker compose up -d

# Verify
curl http://localhost:18083/health
```

## Docker Compose

```yaml
services:
  well:
    image: arifazil/well:latest
    ports:
      - "18083:18083"
    volumes:
      - well-state:/var/lib/well
    environment:
      - WELL_STATE_PATH=/var/lib/well/state.json
    restart: unless-stopped

volumes:
  well-state:
```

## Capabilities

- Biometric ingestion
- Triadic state assessment
- Vitality scoring
- Homeostasis monitoring
- Health drift detection
- Machine diagnostics
