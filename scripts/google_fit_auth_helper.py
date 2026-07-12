#!/usr/bin/env python3
"""
google_fit_auth_helper.py — Interactive helper to acquire Google Fit OAuth credentials.
Spawns a local server on port 8085 to capture the authorization code callback.
"""

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from pathlib import Path

CREDS_FILE = Path("/root/WELL/google_fit_creds.json")
PORT = 8085
REDIRECT_URI = f"http://localhost:{PORT}/"

# Global state to share with HTTP handler
auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Successful!</h1><p>You can close this tab and return to the terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code received.")

def exchange_code_for_tokens(client_id, client_secret, code):
    import requests
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        raise Exception(f"Token exchange failed: {r.text}")
    return r.json()

def main():
    print("==============================================================")
    print("GOOGLE FIT OAUTH AUTHORIZATION HELPER")
    print("==============================================================")
    
    # 1. Ask for Client ID and Client Secret
    client_id = input("Enter Google Client ID: ").strip()
    client_secret = input("Enter Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Both Client ID and Client Secret are required.")
        sys.exit(1)

    # 2. Build Auth URL
    scopes = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.sleep.read"
    ]
    scope_str = "+".join(scopes)
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope_str}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    # 3. Start Local Server
    server = HTTPServer(("0.0.0.0", PORT), OAuthCallbackHandler)
    
    print("\n[!] Please ensure your OAuth Client has 'http://localhost:8085/' added as an Authorized Redirect URI.")
    print(f"\n[+] Open the following link in your browser to authorize:")
    print(f"\n    {auth_url}\n")
    print("[*] Waiting for browser authorization callback on port 8085...")
    
    # Wait until callback handles request
    while auth_code is None:
        server.handle_request()

    print(f"\n[+] Authorization code captured successfully.")
    
    # 4. Exchange Code
    print("[*] Exchanging authorization code for tokens...")
    try:
        tokens = exchange_code_for_tokens(client_id, client_secret, auth_code)
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            print("Warning: No refresh_token returned. Ensure you removed previous access permissions or use prompt=consent.")
        
        # Save to credentials file
        creds_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        }
        
        CREDS_FILE.write_text(json.dumps(creds_data, indent=2))
        print(f"\n[+] SUCCESS: Credentials and Refresh Token saved to: {CREDS_FILE}")
        
    except Exception as e:
        print(f"\n[-] Error exchanging code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
