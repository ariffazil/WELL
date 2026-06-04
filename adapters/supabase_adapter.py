import os
import httpx
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://utbmmjmbolmuahwixjqc.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))

async def _post_to_supabase(table: str, payload: dict, schema: str = "public"):
    if not SUPABASE_KEY:
        logger.debug(f"Missing SUPABASE_KEY. Skipping write to {table}.")
        return
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    if schema != "public":
        headers["Content-Profile"] = schema

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=5.0)
            if resp.status_code not in (200, 201, 204):
                logger.error(f"Supabase {table} write failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Supabase {table} write error: {e}")

def record_well_state(state: dict):
    payload = {
        "well_score": state.get("score", 0),
        "metrics": state.get("metrics", {}),
        "violations": state.get("floors_violated", []),
        "hypotheses": state.get("hypotheses", []),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_post_to_supabase("arifosmcp_well_states", payload, schema="public"))
    except Exception:
        # If no loop is running, just swallow it or run in a new loop
        try:
            asyncio.run(_post_to_supabase("arifosmcp_well_states", payload, schema="public"))
        except Exception as e:
            logger.error(f"Failed to write well state: {e}")
