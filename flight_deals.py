#!/usr/bin/env python3

import os
import traceback
import requests

BOT = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT = os.getenv("TELEGRAM_CHAT_ID", "")

def tg(msg):
    """Guaranteed Telegram message."""
    print(msg)
    if not BOT or not CHAT:
        print("NO TELEGRAM CONFIG FOUND")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("TG FAIL:", e)

# --- START ---
tg("🚀 Script STARTED")

try:
    tg("📌 Step 1: Imports OK")
except:
    pass

# --- MAIN WORK ---
try:
    tg("🔍 Step 2: Running scraper (placeholder)")

    # THIS WILL ALWAYS RUN
    prices = [10, 20, 30]

    tg("📤 Step 3: Sending results...")
    tg("✔️ Preise: " + ", ".join(map(str, prices)))

except Exception as e:
    err = traceback.format_exc()
    tg("💥 ERROR OCCURRED:\n<code>" + err + "</code>")

# --- FINISH ---
tg("🏁 Script FINISHED")
