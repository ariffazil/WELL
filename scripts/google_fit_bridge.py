#!/usr/bin/env python3
"""
google_fit_bridge.py — Bridge script to pull Xiaomi data synced to Google Fit
and update WELL state autonomously.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

CREDS_FILE = Path("/root/WELL/google_fit_creds.json")
STATE_FILE = Path("/root/WELL/state.json")
INJECT_SCRIPT = Path("/root/WELL/scripts/biometric_inject.sh")

SETUP_GUIDE = """
================================================================================
GOOGLE FIT BRIDGE SETUP GUIDE
================================================================================
1. Go to Google Cloud Console (https://console.cloud.google.com).
2. Create a new project (e.g. "Arif Wellness Bridge").
3. Go to "API & Services" > "Library", search for "Fitness API", and enable it.
4. Go to "OAuth consent screen":
   - Select "External".
   - Add your email and app details.
   - Under Scopes, add:
     - https://www.googleapis.com/auth/fitness.activity.read
     - https://www.googleapis.com/auth/fitness.sleep.read
   - Under "Test users", add your own Google email account.
5. Go to "Credentials" > "Create Credentials" > "OAuth client ID":
   - Application type: "Web application" or "Desktop app".
   - Name: "Wellness Bridge client".
   - Download the JSON credentials.
6. Run the OAuth authorization helper to get your Refresh Token:
   - python3 /root/WELL/scripts/google_fit_auth_helper.py
7. Save the client_id, client_secret, and refresh_token in:
   /root/WELL/google_fit_creds.json
================================================================================
"""

def print_setup_instructions():
    print(SETUP_GUIDE)

def get_access_token(client_id, client_secret, refresh_token):
    import requests
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        raise Exception(f"Failed to refresh token: {r.text}")
    return r.json()["access_token"]

def get_google_fit_data(access_token):
    import requests
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    
    start_ms = int(yesterday.timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    
    # 1. Fetch Steps
    steps_url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "aggregateBy": [{
            "dataTypeName": "com.google.step_count.delta",
            "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        }],
        "bucketByTime": { "durationMillis": 86400000 },
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms
    }
    
    steps = None
    try:
        r = requests.post(steps_url, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Google Fit steps request failed: HTTP {r.status_code}")
        data = r.json()
        values = [
            val.get("intVal", 0)
            for bucket in data.get("bucket", [])
            for dataset in bucket.get("dataset", [])
            for point in dataset.get("point", [])
            for val in point.get("value", [])
        ]
        if values:
            steps = sum(values)
    except Exception as e:
        print(f"Warning: Failed to fetch steps: {e}")

    # 2. Fetch Sleep Sessions
    start_iso = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    sleep_url = f"https://www.googleapis.com/fitness/v1/users/me/sessions?startTime={start_iso}&endTime={end_iso}"
    
    sleep_hours = None
    try:
        r = requests.get(sleep_url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"Google Fit sleep request failed: HTTP {r.status_code}")
        data = r.json()
        durations = []
        for session in data.get("session", []):
            # Activity type 72 corresponds to Sleep in Google Fit
            if session.get("activityType") == 72:
                start_t = int(session.get("startTimeMillis"))
                end_t = int(session.get("endTimeMillis"))
                durations.append((end_t - start_t) / 3600000.0)
        if durations:
            sleep_hours = sum(durations)
    except Exception as e:
        print(f"Warning: Failed to fetch sleep: {e}")

    return {
        "steps": steps,
        "sleep_hours": round(sleep_hours, 1) if sleep_hours is not None else None,
    }

def main():
    if not CREDS_FILE.exists():
        print("[-] google_fit_creds.json not found.")
        print_setup_instructions()
        sys.exit(0)

    try:
        creds = json.loads(CREDS_FILE.read_text())
        client_id = creds["client_id"]
        client_secret = creds["client_secret"]
        refresh_token = creds["refresh_token"]
    except Exception as e:
        print(f"[-] Invalid format in google_fit_creds.json: {e}")
        print_setup_instructions()
        sys.exit(1)

    print("[*] Contacting Google Fit API...")
    try:
        access_token = get_access_token(client_id, client_secret, refresh_token)
        fit_data = get_google_fit_data(access_token)
    except Exception as e:
        print(f"[-] Error querying Google Fit API: {e}")
        sys.exit(1)

    steps = fit_data["steps"]
    sleep = fit_data["sleep_hours"]
    if steps is None or sleep is None:
        print("[-] Google Fit returned incomplete observations; WELL state was not updated.")
        sys.exit(1)
    
    print(f"[+] Retrieved data: Sleep = {sleep} hours, Steps = {steps}")

    # Map retrieved data to WELL parameters
    # sleep >= 8 hours -> peace2 increases
    peace2 = min(1.0, max(0.5, sleep / 10.0))
    # steps >= 10000 -> delta_s decreases
    delta_s = min(0.8, max(0.1, 1.0 - (steps / 12000.0)))
    
    cmd = [
        "bash", str(INJECT_SCRIPT),
        "--non-interactive",
        "--delta-s", f"{delta_s:.2f}",
        "--peace2", f"{peace2:.2f}",
        "--kappa-r", "0.80",
        "--rasa", "sync_xiaomi",
        "--amanah", "0.90",
        "--signals",
        "--signal-s05-sleep-architecture", json.dumps({"hours": sleep, "quality": 8}),
        "--signal-s08-movement-strength", json.dumps({"steps": steps, "strength_sessions": 0})
    ]
    
    print(f"[*] Executing biometric injection script: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("[+] WELL state successfully updated with Xiaomi data via Google Fit!")
    except subprocess.CalledProcessError as e:
        print(f"[-] Injection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
