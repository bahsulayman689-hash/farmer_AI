"""FarmAI daily reminders. Run once a day (see .github/workflows/reminders.yml).

For every farmer with reminders switched on it builds the morning message (tasks due today or tomorrow,
overdue tasks, rain alert) and sends it by WhatsApp or SMS through Twilio. Farmers with nothing to do get nothing.

Environment variables
  SUPABASE_URL, SUPABASE_SERVICE_KEY    service_role key: server only, never put it in the Streamlit app
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
  TWILIO_SMS_FROM                       e.g. +1555...   (for channel = sms)
  TWILIO_WHATSAPP_FROM                  e.g. +14155238886 (sandbox) or your approved sender (for channel = whatsapp)
  GEMINI_API_KEY                        optional, translates the message for farmers who chose another language
  DRY_RUN=1                             print messages instead of sending (default when Twilio is not configured)
"""
import os, sys, json, datetime as dt
import requests
from farm_data import build_message

SB_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
DRY = os.getenv("DRY_RUN") == "1" or not (os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"))

def sb(method, table, params=None, body=None):
    h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}
    r = requests.request(method, f"{SB_URL}/rest/v1/{table}", headers=h, params=params, json=body, timeout=30)
    if r.status_code >= 400: raise RuntimeError(f"{table}: {r.status_code} {r.text[:200]}")
    return r.json() if r.text else []

_rain = {}
def rain_chance(city):
    """Highest rain probability (%) for today and tomorrow, cached per city. None when unknown."""
    if city in _rain: return _rain[city]
    try:
        g = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=15).json()
        loc = g["results"][0]
        w = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": loc["latitude"], "longitude": loc["longitude"],
                         "timezone": "auto", "forecast_days": 2, "daily": "precipitation_probability_max"}, timeout=15).json()
        _rain[city] = max(x or 0 for x in w["daily"]["precipitation_probability_max"][:2])
    except Exception as e:
        print(f"  weather unavailable for {city}: {e}"); _rain[city] = None
    return _rain[city]

def translate(text, lang):
    key = os.getenv("GEMINI_API_KEY")
    if lang == "English" or not key: return text
    prompt = f"Translate this farm reminder into {lang} as spoken in The Gambia, in simple words. Keep the emoji and line breaks. Reply with the translation only.\n\n{text}"
    try:
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": key}, timeout=60,
                          json={"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}})
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip() or text
    except Exception:
        return text

def send(phone, channel, body):
    if DRY:
        print(f"  [dry run] {channel} to {phone}:\n" + "\n".join("    " + l for l in body.splitlines())); return True
    sid, tok = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
    frm = os.getenv("TWILIO_WHATSAPP_FROM") if channel == "whatsapp" else os.getenv("TWILIO_SMS_FROM")
    if not frm: print(f"  no sender configured for {channel}"); return False
    pre = "whatsapp:" if channel == "whatsapp" else ""
    r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, tok), timeout=30,
                      data={"To": pre + phone, "From": pre + frm, "Body": body[:1500]})
    if r.status_code >= 400: print(f"  Twilio error {r.status_code}: {r.text[:200]}"); return False
    return True

def main():
    if not (SB_URL and SB_KEY): sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")
    today = dt.date.today(); only = os.getenv("ONLY_PHONE")
    profiles = sb("GET", "profiles", {"select": "user_id,phone,channel,location,lang,last_sent", "reminders": "eq.true"})
    print(f"{today}: {len(profiles)} farmer(s) with reminders on" + (" (dry run)" if DRY else ""))
    sent = skipped = failed = 0
    for pr in profiles:
        uid = pr["user_id"]
        try:
            if not pr.get("phone") or (only and pr["phone"] != only): continue
            if pr.get("last_sent") == today.isoformat() and not only: skipped += 1; continue
            plots = sb("GET", "plots", {"select": "id,crop,planted", "user_id": f"eq.{uid}"})
            done = {}
            for r in sb("GET", "task_done", {"select": "plot_id,idx", "user_id": f"eq.{uid}"}): done.setdefault(r["plot_id"], set()).add(r["idx"])
            msg = build_message([dict(crop=p["crop"], planted=dt.date.fromisoformat(p["planted"]), done=done.get(p["id"], set())) for p in plots],
                                rain_chance(pr.get("location") or "Banjul"), today)
            if not msg: skipped += 1; continue
            if send(pr["phone"], pr.get("channel", "whatsapp"), translate(msg, pr.get("lang", "English"))):
                sent += 1
                if not DRY: sb("PATCH", "profiles", {"user_id": f"eq.{uid}"}, {"last_sent": today.isoformat()})
            else: failed += 1
        except Exception as e:
            failed += 1; print(f"  farmer {str(uid)[:8]}: {e}")
    print(f"done: {sent} sent, {skipped} skipped, {failed} failed")
    if failed and not sent: sys.exit(1)

if __name__ == "__main__":
    main()
