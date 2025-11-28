#!/usr/bin/env python3

import os
import re
import json
import datetime
import requests
from datetime import timedelta

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ORIGIN = "OTP"
MAX_PRICE = 100

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}


def next_weekend():
    today = datetime.date.today()
    saturday = today + timedelta((5 - today.weekday()) % 7)
    monday = saturday + timedelta(days=2)
    return saturday, monday


def scrape_google_flights(origin, depart, ret):
    """
    Safely scrape Google Flights JSON blobs for real prices.
    No f-strings spanning lines (avoid syntax issues).
    """

    base_url = "https://www.google.com/travel/flights/search?"
    query = (
        "hl=en&gl=us&curr=EUR&"
        "tfs=CBwQAholagwIAhIIL20vMDRocBID"
        + origin +
        "cgcIARID" +
        origin +
        "SgwIARISC21vdW50YWluIGRhdGUaIhIGc2RhdGUo"
        + depart +
        "),EgZzZGF0ZSg("
        + ret +
        "))"
    )

    url = base_url + query

    r = requests.get(url, headers=HEADERS)
    html = r.text

    matches = re.findall(r"AF_initDataCallback\((.*?)\);", html, re.DOTALL)
    prices = []

    for block in matches:
        try:
            j = json.loads(block)
        except:
            continue

        if "data" not in j:
            continue

        raw = json.dumps(j["data"])
        found = re.findall(r"(\d{1,4})\\u20ac", raw)

        for p in found:
            num = int(p)
            if num <= MAX_PRICE:
                prices.append(num)

    return sorted(set(prices))


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
    requests.post(url, json=payload)


def main():
    print("Scanning real flight prices...")

    sat, mon = next_weekend()
    depart = sat.strftime("%Y-%m-%d")
    ret = mon.strftime("%Y-%m-%d")

    prices = scrape_google_flights(ORIGIN, depart, ret)

    if not prices:
        text = (
            "😔 <b>Keine Flüge gefunden</b>\n"
            f"{depart} → {ret}\n"
            f"Unter {MAX_PRICE}€."
        )
        send_telegram(text)
        return

    text = (
        f"✈️ <b>TOP 10 BILLIGSTE REAL FLÜGE</b>\n"
        f"Ab: <b>{ORIGIN}</b>\n"
        f"Weekend: {depart} → {ret}\n"
        f"Max: {MAX_PRICE}€\n\n"
    )

    for p in prices[:10]:
        text += f"• <b>{p} €</b>\n"

    text += (
        "\n<a href='https://www.google.com/travel/flights?"
        "q=flights+from+OTP'>Google Flights öffnen</a>"
    )

    send_teleg_
