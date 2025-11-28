#!/usr/bin/env python3
"""
BULLETPROOF GOOGLE FLIGHTS SCRAPER
OTP → Anywhere (Roundtrip next weekend)
No API keys. Extremely robust JSON extraction.
Always sends Telegram message.
"""

import os
import re
import json
import datetime
import requests
from datetime import timedelta

# =========================
# CONFIG
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ORIGIN = "OTP"
MAX_PRICE = 100

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# =========================
# DATE HANDLER
# =========================

def next_weekend():
    today = datetime.date.today()
    sat = today + timedelta((5 - today.weekday()) % 7)
    mon = sat + timedelta(days=2)
    return sat, mon


# =========================
# BULLETPROOF GOOGLE FLIGHTS SCRAPER
# =========================

def extract_prices_from_text(text):
    """Find all real € prices in any encoding Google uses."""
    prices = set()

    # € as unicode
    for p in re.findall(r'(\d{1,4})\\u20ac', text):
        prices.add(int(p))

    # actual UTF-8 € symbol
    for p in re.findall(r'€\s?(\d{1,4})', text):
        prices.add(int(p))
    for p in re.findall(r'(\d{1,4})\s?€', text):
        prices.add(int(p))

    # JSON escaped €
    for p in re.findall(r'(\d{1,4})\\\\u20ac', text):
        prices.add(int(p))

    # Final
    return sorted(prices)


def scrape_google_flights(origin, depart, ret):
    """
    Extremely robust extraction:
    1) Load HTML
    2) Extract ALL AF_initDataCallback blobs
    3) Extract ALL JSON dicts inside
    4) Extract ALL price-like patterns
    """
    url = (
        "https://www.google.com/travel/flights/search?"
        f"hl=en&gl=us&curr=EUR&tfs=CBwQAholagwIAhIIL20vMDRocBID{origin}"
        f"cgcIARID{origin}SgwIARISC21vdW50YWluIGRhdGUaIhIGc2RhdGUo{depart}"
        f"),EgZzZGF0ZSg({ret}))"
    )

    r = requests.get(url, headers=HEADERS, timeout=10)
    html = r.text

    all_prices = []

    # ---- extract all callback blobs ----
    blobs = re.findall(r"AF_initDataCallback\((.*?)\);", html, re.DOTALL)

    for blob in blobs:
        # extract any JSON inside
        json_matches = re.findall(r"{.*}", blob, re.DOTALL)

        for jm in json_matches:
            try:
                jdata = json.loads(jm)
            except:
                continue

            raw = json.dumps(jdata)
            prices = extract_prices_from_text(raw)
            all_prices.extend(prices)

    # Deduplicate + filter by MAX_PRICE
    final = sorted(set([p for p in all_prices if p <= MAX_PRICE]))

    return final


# =========================
# TELEGRAM
# =========================

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured.")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# =========================
# MAIN
# =========================

def main():
    sat, mon = next_weekend()
    depart = sat.strftime("%Y-%m-%d")
    ret = mon.strftime("%Y-%m-%d")

    prices = []
    try:
        prices = scrape_google_flights(ORIGIN, depart, ret)
    except Exception as e:
        prices = []
        print("Scraper error:", e)

    # ALWAYS send Telegram, even on empty
    if not prices:
        msg = (
            "😔 <b>Keine realen Flüge gefunden</b>\n"
            f"{depart} → {ret}\n"
            f"(Unter {MAX_PRICE}€)"
        )
        send_telegram(msg)
        print(msg)
        return

    msg = (
        f"✈️ <b>Top 10 Billigste Flüge (Real Google Flights)</b>\n"
        f"Von: <b>{ORIGIN}</b>\n"
        f"Weekend: {depart} → {ret}\n"
        f"Max: {MAX_PRICE}€\n\n"
    )

    for p in prices[:10]:
        msg += f"• <b>{p} €</b>\n"

    msg += "\n<a href='https://www.google.com/travel/flights?q=flights+from+OTP'>Google Flights</a>"

    send_telegram(msg)
    print(msg)


if __name__ == "__main__":
    main()
