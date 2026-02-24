"""
Romerike Værvarsling
Sjekker værdata fra Met.no og Norsk klimaservicesenter
og sender varsler til Slack ved kritiske forhold.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

# --- Konfigurasjon ---
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Romerike (Lillestrøm som referansepunkt)
LAT = 59.9557
LON = 11.0524
LOCATION_NAME = "Romerike (Lillestrøm)"

# Terskelverdier for varsler
THRESHOLDS = {
    "precipitation_1h_mm": 5.0,      # mm per time - kraftig nedbør
    "precipitation_6h_mm": 15.0,     # mm per 6 timer
    "precipitation_12h_mm": 25.0,    # mm per 12 timer
    "temp_drop_6h": 8.0,             # °C temperaturfall på 6 timer
    "temp_rise_6h": 8.0,             # °C temperaturøkning på 6 timer
    "wind_speed_ms": 15.0,           # m/s (sterk vind ~liten storm)
}

HEADERS = {
    "User-Agent": "RomerikeWeatherBot/1.0 github.com/din-org/romerike-weather"
}

EVENT_TYPE_NO = {
    "wind": "Vind",
    "rain": "Regn",
    "snow": "Snø",
    "ice": "Is",
    "fog": "Tåke",
    "thunder": "Tordenvær",
    "avalanche": "Snøskred",
    "flooding": "Flom",
    "forestFire": "Skogbrann",
    "storm": "Storm",
    "polarLow": "Polart lavtrykk",
}

AWARENESS_LEVEL_NO = {
    "green": "Grønt nivå",
    "yellow": "Gult nivå",
    "orange": "Oransje nivå",
    "red": "Rødt nivå",
}

def fetch_met_forecast():
    """Henter varseldata fra Met.no Locationforecast 2.0"""
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={LAT}&lon={LON}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_met_alerts():
    """Henter farevarsler fra Met.no MetAlerts"""
    url = f"https://api.met.no/weatherapi/metalerts/2.0/current.json?lat={LAT}&lon={LON}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    return None

def fetch_frost_climate():
    """
    Henter klimanormaler/observasjoner fra Norsk klimaservicesenter (Frost API).
    Krever API-nøkkel satt som FROST_CLIENT_ID i GitHub Secrets.
    Returnerer None dersom nøkkel mangler.
    """
    client_id = os.environ.get("FROST_CLIENT_ID")
    if not client_id:
        return None

    # Nærmeste stasjon: Gardermoen (SN4780)
    station_id = "SN4780"
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

    url = "https://frost.met.no/observations/v0.jsonld"
    params = {
        "sources": station_id,
        "elements": "air_temperature,sum(precipitation_amount PT1H)",
        "referencetime": f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "timeresolutions": "PT1H",
    }
    resp = requests.get(url, params=params, auth=(client_id, ""), timeout=30)
    if resp.status_code == 200:
        return resp.json()
    return None

# --- Analyse ---

def analyze_forecast(data):
    """Analyserer varseldata og returnerer liste med funn."""
    alerts = []
    timeseries = data.get("properties", {}).get("timeseries", [])

    now = datetime.now(timezone.utc)
    lookahead_hours = 48

    temps = []
    for entry in timeseries:
        t = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        if t < now or t > now + timedelta(hours=lookahead_hours):
            continue

        instant = entry.get("data", {}).get("instant", {}).get("details", {})
        next1h = entry.get("data", {}).get("next_1_hours", {}).get("details", {})
        next6h = entry.get("data", {}).get("next_6_hours", {}).get("details", {})
        next12h = entry.get("data", {}).get("next_12_hours", {}).get("details", {})

        temp = instant.get("air_temperature")
        wind = instant.get("wind_speed")
        precip_1h = next1h.get("precipitation_amount")
        precip_6h = next6h.get("precipitation_amount")
        precip_12h = next12h.get("precipitation_amount")

        time_str = t.strftime("%d.%m %H:%M")

        if temp is not None:
            temps.append((t, temp))

        if precip_1h is not None and precip_1h >= THRESHOLDS["precipitation_1h_mm"]:
            alerts.append({
                "type": "nedbør",
                "emoji": "🌧️",
                "severity": "høy" if precip_1h >= 10 else "moderat",
                "title": f"Kraftig nedbør {precip_1h:.1f} mm/time",
                "period": f"{time_str} – {(t + timedelta(hours=1)).strftime('%d.%m %H:%M')}",
                "description": f"{precip_1h:.1f} mm nedbør meldt for denne timen.",
            })

        if precip_6h is not None and precip_6h >= THRESHOLDS["precipitation_6h_mm"]:
            alerts.append({
                "type": "nedbør",
                "emoji": "🌧️",
                "severity": "høy" if precip_6h >= 30 else "moderat",
                "title": f"Mye nedbør {precip_6h:.1f} mm over 6 timer",
                "period": f"{time_str} – {(t + timedelta(hours=6)).strftime('%d.%m %H:%M')}",
                "description": f"{precip_6h:.1f} mm nedbør meldt over 6 timer.",
            })

        if precip_12h is not None and precip_12h >= THRESHOLDS["precipitation_12h_mm"]:
            alerts.append({
                "type": "nedbør",
                "emoji": "🌧️",
                "severity": "høy" if precip_12h >= 50 else "moderat",
                "title": f"Mye nedbør {precip_12h:.1f} mm over 12 timer",
                "period": f"{time_str} – {(t + timedelta(hours=12)).strftime('%d.%m %H:%M')}",
                "description": f"{precip_12h:.1f} mm nedbør meldt over 12 timer.",
            })

        if wind is not None and wind >= THRESHOLDS["wind_speed_ms"]:
            alerts.append({
                "type": "vind",
                "emoji": "💨",
                "severity": "høy" if wind >= 20 else "moderat",
                "title": f"Sterk vind {wind:.1f} m/s",
                "period": time_str,
                "description": f"Vindstyrke på {wind:.1f} m/s meldt.",
            })

    # Analyser temperatursvingninger over 6-timersperioder
    for i in range(len(temps)):
        for j in range(i + 1, len(temps)):
            t1, temp1 = temps[i]
            t2, temp2 = temps[j]
            diff_hours = (t2 - t1).total_seconds() / 3600
            if abs(diff_hours - 6) > 0.6:
                continue
            diff_temp = temp2 - temp1
            if diff_temp <= -THRESHOLDS["temp_drop_6h"]:
                alerts.append({
                    "type": "temperatur",
                    "emoji": "🌡️",
                    "severity": "moderat",
                    "title": f"Kraftig temperaturfall {abs(diff_temp):.1f}°C på 6 timer",
                    "period": f"{t1.strftime('%d.%m %H:%M')} – {t2.strftime('%d.%m %H:%M')}",
                    "description": f"Temperaturen faller fra {temp1:.1f}°C til {temp2:.1f}°C på 6 timer.",
                })
            elif diff_temp >= THRESHOLDS["temp_rise_6h"]:
                alerts.append({
                    "type": "temperatur",
                    "emoji": "🌡️",
                    "severity": "moderat",
                    "title": f"Kraftig temperaturøkning {diff_temp:.1f}°C på 6 timer",
                    "period": f"{t1.strftime('%d.%m %H:%M')} – {t2.strftime('%d.%m %H:%M')}",
                    "description": f"Temperaturen stiger fra {temp1:.1f}°C til {temp2:.1f}°C på 6 timer.",
                })

    # Dedupliser (fjern svært like varsler)
    seen = set()
    unique_alerts = []
    for a in alerts:
        key = (a["type"], a["period"][:8])  # type + dag som nøkkel
        if key not in seen:
            seen.add(key)
            unique_alerts.append(a)

    return unique_alerts

def analyze_metalerts(data):
    """Analyserer farevarsler fra MetAlerts. Dedupliserer på farevarselets ID."""
    if not data:
        return []
    alerts = []
    seen_ids = set()
    features = data.get("features", [])
    for feature in features:
        props = feature.get("properties", {})

        # Bruk unik ID for å unngå duplikater
        alert_id = props.get("id", "")
        if alert_id in seen_ids:
            continue
        seen_ids.add(alert_id)

        description = props.get("description", "")
        # awareness_level format: "2; yellow; Moderate"
        awareness_level_raw = props.get("awareness_level", "")
        awareness_color = ""
        for part in awareness_level_raw.split(";"):
            part = part.strip().lower()
            if part in ("yellow", "orange", "red", "green"):
                awareness_color = part
                break

        event_type = props.get("event", "")
        area = props.get("area", "")

        # Hent tidsperiode fra title: "Is, gult nivå, Deler av Østlandet, 2026-02-25T12:00:00+00:00, 2026-02-25T22:59:00+00:00"
        MÅNEDER = {
            1: "januar", 2: "februar", 3: "mars", 4: "april",
            5: "mai", 6: "juni", 7: "juli", 8: "august",
            9: "september", 10: "oktober", 11: "november", 12: "desember"
        }

        def norsk_dato(dt):
            return f"{dt.day}. {MÅNEDER[dt.month]} klokka {dt.strftime('%H.%M')}"

        period = ""
        try:
            title_raw = props.get("title", "")
            # Finn ISO-datoer i title
            import re
            dates = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+\-]\d{2}:\d{2}", title_raw)
            if len(dates) >= 2:
                norsk_tz = timezone(timedelta(hours=1))
                t_start = datetime.fromisoformat(dates[0]).astimezone(norsk_tz)
                t_end = datetime.fromisoformat(dates[1]).astimezone(norsk_tz)
                period = f"{norsk_dato(t_start)} til {norsk_dato(t_end)}"
            elif props.get("eventEndingTime"):
                t_end = datetime.fromisoformat(props["eventEndingTime"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=1)))
                period = f"Til {norsk_dato(t_end)}"
        except Exception:
            pass

        severity = "høy" if awareness_color == "red" else "moderat"
        emoji = "🚨" if severity == "høy" else "⚠️"

        event_type_no = EVENT_TYPE_NO.get(event_type, event_type)
        awareness_level_no = AWARENESS_LEVEL_NO.get(awareness_color, awareness_color)
        nivå_kort = awareness_level_no.replace(" nivå", "").capitalize()
        title = f"{nivå_kort} farevarsel for {event_type_no.lower()}"

        web_url = props.get("web", "").strip("_")

        alerts.append({
            "type": event_type_no,
            "emoji": emoji,
            "severity": severity,
            "title": title,
            "area": area,
            "period": period,
            "awareness_level": nivå_kort,
            "description": description,
            "url": web_url,
        })
    return alerts

# --- Slack ---

def build_slack_message(forecast_alerts, meta_alerts, frost_info=None):
    """Bygger Slack Block Kit-melding."""
    if not meta_alerts and not forecast_alerts:
        return None  # Ingen varsler = ingen melding

    blocks = []

    # --- Farevarsler fra MetAlerts ---
    for alert in meta_alerts:
        area_line = f"*Område:* {alert['area']}\n" if alert.get('area') else ""
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*[Vær] {alert['title']}*\n"
                    f"{area_line}"
                    f"*Tidsperiode:* {alert['period']}\n"
                    f"*Nivå:* {alert['awareness_level']}\n"
                    f"*Beskrivelse:* {alert['description']}"
                ),
            },
        })
        if alert.get("url"):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Sjekk kilden her", "emoji": True},
                        "url": alert["url"],
                        "style": "primary",
                    }
                ],
            })
        blocks.append({"type": "divider"})

    # --- Varsler fra varseldata (nedbør, temperatur, vind) ---
    for alert in forecast_alerts:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{alert['emoji']} *[Vær] {alert['title']}*\n"
                    f"*Tidsperiode:* {alert['period']}\n"
                    f"*Type:* {alert['type']}\n"
                    f"*Nivå:* {alert['severity']}\n"
                    f"*Beskrivelse:* {alert['description']}"
                ),
            },
        })
        blocks.append({"type": "divider"})

    if frost_info:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📊 *Klimadata siste 24t (Gardermoen)*\n{frost_info}",
            },
        })

    return {"blocks": blocks}

def send_slack_message(payload):
    """Sender melding til Slack via webhook."""
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL er ikke satt som miljøvariabel/secret!")
    resp = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    print(f"Slack-melding sendt: {resp.status_code}")

def summarize_frost(data):
    """Lager en kort oppsummering av Frost-observasjoner."""
    if not data or "data" not in data:
        return None
    obs = data["data"]
    temps = [o["observations"][0]["value"] for o in obs if o.get("observations") and o["observations"][0].get("elementId") == "air_temperature"]
    precips = [o["observations"][0]["value"] for o in obs if o.get("observations") and "precipitation" in o["observations"][0].get("elementId", "")]
    parts = []
    if temps:
        parts.append(f"Temp min/maks: *{min(temps):.1f}°C / {max(temps):.1f}°C*")
    if precips:
        parts.append(f"Total nedbør: *{sum(precips):.1f} mm*")
    return " | ".join(parts) if parts else None

# --- Hovedprogram ---

def main():
    print(f"Starter værkontroll for {LOCATION_NAME}...")

    # Hent data
    forecast_data = fetch_met_forecast()
    meta_data = fetch_met_alerts()
    frost_data = fetch_frost_climate()

    # Analyser
    forecast_alerts = analyze_forecast(forecast_data)
    meta_alerts = analyze_metalerts(meta_data)
    frost_info = summarize_frost(frost_data)

    print(f"Varsler funnet: {len(forecast_alerts)} fra varsel, {len(meta_alerts)} farevarsler")

    # Bygg og send Slack-melding
    payload = build_slack_message(forecast_alerts, meta_alerts, frost_info)
    if payload:
        send_slack_message(payload)
    else:
        print("Ingen varsler å sende – forholdene er normale.")

if __name__ == "__main__":
    main()
