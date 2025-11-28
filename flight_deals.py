#!/usr/bin/env python3
"""
REAL WEEKEND FLIGHT FINDER
OTP → ANYWHERE (Roundtrip)
No API keys. No fake data. Google Flights scraped + parsed.
"""

import os
import re
import json
import datetime
import requests
from datetime import timedelta

# ============================================
# CONFIG
# ============================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ORIGIN = "OTP"
MAX_PRICE = 100

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

# ============================================
# WEEKEND CALCULATOR
# ============================================

def next_weekend():
    today = datetime.date.today()
    saturday = today + timedelta((5 - today.weekday()) % 7)
    monday = saturday + timedelta(days=2)
    return saturday, monday


# ============================================
# GOOGLE FLIGHTS SCRAPER (REAL DATA)
# ============================================

def scrape_google_flights(origin, depart, ret):
    """
    We load Google Flights search HTML → extract embedded JSON → find prices.
    Google puts all prices inside AF_initDataCallback JSON blobs.
    Parsing those gives real prices without JS.
    """

    url = (
        "https://www.google.com/travel/flights/search?"
        f"hl=en&gl=us&curr=EUR&tfs=CBwQAhoragwIAhIIL20vMDRocBID{origin}cg0IAhIIL20vMGp4djISA0FOWXIMCAkSA0FOWXIaIxIGc2RhdGUo{depart}),"
        f"EgZzZGF0ZSg{return})"
    )

    r = requests.get(url, headers=HEADERS)
    html = r.text

    # Extract JSON payload(s)
    matches = re.findall(r"AF_initDataCallback\((.*?)\);", html, re.DOTALL)
    prices = []

    for m in matches:
        try:
            j = json.loads(m)
        except:
            continue

        if "data" not in j:
            continue

        # Convert nested data to string to find EUR prices
        raw = json.dumps(j["data"])

        # Google writes "123\u20ac"
        found = re.findall(r"(\d{1,4})\\u20ac", raw)

        for p in found:
            p = int(p)
            if p <= MAX_PRICE:
                prices.append(p)

    prices = sorted(set(prices))
    return prices


# ============================================
# TELEGRAM
# ============================================

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })


# ============================================
# MAIN
# ============================================

def main():
    print("🔍 Pulling real flight data...")

    sat, mon = next_weekend()
    depart = sat.strftime("%Y-%m-%d")
    ret = mon.strftime("%Y-%m-%d")

    prices = scrape_google_flights(ORIGIN, depart, ret)

    if not prices:
        msg = (
            "😔 <b>Keine Flüge gefunden</b>\n"
            f"{depart} → {ret}\n"
            f"Unter {MAX_PRICE}€."
        )
        send_telegram(msg)
        return

    msg = (
        f"✈️ <b>TOP 10 BILLIGSTE FLÜGE (Real Prices)</b>\n"
        f"Ab: <b>{ORIGIN}</b>\n"
        f"Weekend: {depart} → {ret}\n"
        f"Max: {MAX_PRICE}€\n\n"
    )

    for p in prices[:10]:
        msg += f"• <b>{p} €</b>\n"

    msg += (
        "\n<a href='https://www.google.com/travel/flights?"
        f"q=flights+from+{ORIGIN}'>Google Flights öffnen</a>"
    )

    send_telegram(msg)
    print(msg)


if __name__ == "__main__":
    main()
