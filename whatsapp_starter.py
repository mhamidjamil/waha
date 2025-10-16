# filename: whatsapp_starter.py
import time
import threading
import requests
import json
import argparse
import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ----------------------------
# Environment Config
# ----------------------------
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

WAHA_BASE_URL = os.getenv("WAHA_API_URL")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
WAHA_WEBHOOK_URL = os.getenv("WAHA_WEBHOOK_URL")

# Construct the specific session start endpoint from the base URL
if WAHA_BASE_URL:
    WAHA_SESSION_START_URL = WAHA_BASE_URL.rstrip('/') + '/api/sessions/start'
else:
    WAHA_SESSION_START_URL = None

NTFY_URL = os.getenv("NTFY_URL")

# ----------------------------
# WhatsApp API Call Function
# ----------------------------
def start_whatsapp_session():
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": WAHA_API_KEY
    }

    payload = {
        "name": "default",
        "config": {
            "webhooks": [
                {
                    "url": WAHA_WEBHOOK_URL,
                    "events": ["message"]
                }
            ]
        }
    }

    try:
        if not WAHA_SESSION_START_URL:
            raise RuntimeError("WAHA base URL is not configured (WAHA_API_URL)")

        response = requests.post(WAHA_SESSION_START_URL, headers=headers, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return {"status": response.status_code, "response": response.text}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}


# ----------------------------
# API-based session status monitoring
# ----------------------------
DASHBOARD_CHECK_INTERVAL = int(os.getenv("DASHBOARD_CHECK_INTERVAL_SECONDS", "300"))  # seconds


def check_session_status_via_api() -> dict:
    """Call GET /api/sessions/default and return the parsed JSON (or error dict)."""
    if not WAHA_BASE_URL:
        return {'error': 'WAHA base URL not configured (WAHA_API_URL)'}

    url = WAHA_BASE_URL.rstrip('/') + '/api/sessions/default'
    headers = {
        'Accept': 'application/json',
        'X-Api-Key': WAHA_API_KEY
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {'status': data.get('status'), 'raw': data}
    except Exception as e:
        print(f"⚠️ Failed to call session status API {url}: {e}")
        return {'error': str(e)}


def monitor_session_loop():
    """Background loop that checks session status via API periodically and restarts sessions if STOPPED."""
    print(f"Session monitor starting, checking every {DASHBOARD_CHECK_INTERVAL} seconds...")
    while True:
        try:
            status = check_session_status_via_api()
            print(f"Session API check result: {status}")

            if status.get('status') == 'STOPPED':
                print("Detected STOPPED sessions via API — attempting to restart via WAHA API...")
                start_whatsapp_session()

        except Exception as e:
            print(f"⚠️ Session monitor error: {e}")

        time.sleep(DASHBOARD_CHECK_INTERVAL)

# ----------------------------
# Flask Routes
# ----------------------------
@app.route("/trigger", methods=["GET"])
def trigger():
    result = start_whatsapp_session()
    return jsonify(result)

@app.route("/waha", methods=["POST"])
def waha():
    payload = request.json

    msg_body = payload.get("payload", {}).get("body")
    raw_from = payload.get("payload", {}).get("from")
    sender_number = raw_from.split("@")[0] if raw_from else None

    result = {"body": msg_body, "from": sender_number}

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Incoming WAHA simplified event:")
    print(json.dumps(result, indent=2))

    BLOCKED_SENDERS = ["status", "ptcl"]

    if sender_number in BLOCKED_SENDERS:
        print(f"⛔ Skipping NTFY forward for blocked sender: {sender_number}")
    else:
        if NTFY_URL:
            try:
                message = f"From: {sender_number}\nMessage: {msg_body}"
                requests.post(NTFY_URL, data=message.encode("utf-8"))
            except Exception as e:
                print(f"⚠️ Failed to forward to ntfy: {e}")
        else:
            print("⚠️ NTFY_URL not set, skipping ntfy forward.")

    return {"ok": True}, 200

# ----------------------------
# Startup delayed call
# ----------------------------
def delayed_start(skip_delay: bool):
    if skip_delay:
        print("Skipping wait, starting WhatsApp session instantly...")
    else:
        print("Waiting 2 minutes before starting WhatsApp session...")
        time.sleep(120)

    print("Running initial WhatsApp session call...")
    start_whatsapp_session()
    # After initial start (or instant start), also start the session monitor
    print("Starting session monitor thread now...")
    threading.Thread(
        target=monitor_session_loop,
        daemon=True
    ).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--instant", action="store_true", help="Start WhatsApp instantly (skip 2 min wait)")
    args = parser.parse_args()

    threading.Thread(
        target=delayed_start,
        args=(args.instant,),
        daemon=True
    ).start()

    # Session monitor will be started by delayed_start once initial start completes

    app.run(host=FLASK_HOST, port=FLASK_PORT)
