# 🌧️ Romerike Værvarsling

GitHub Actions-tjeneste som sjekker vær for Romerike hver tredje time og sender varsel til Slack.

## Datakilder

| Kilde | API | Hva hentes |
|---|---|---|
| **Met.no** | Locationforecast 2.0 | 48-timers varsel (nedbør, temperatur, vind) |
| **Met.no** | MetAlerts 2.0 | Aktive farevarsler for området |
| **Norsk klimaservicesenter** | Frost API *(valgfritt)* | Observasjoner siste 24t fra Gardermoen |

## Varsler sendes ved

| Hendelse | Terskel |
|---|---|
| Kraftig nedbør | ≥ 5 mm/time |
| Mye nedbør | ≥ 15 mm over 6 timer |
| Mye nedbør | ≥ 25 mm over 12 timer |
| Temperaturfall | ≥ 8 °C på 6 timer |
| Temperaturøkning | ≥ 8 °C på 6 timer |
| Sterk vind | ≥ 15 m/s |
| Farevarsel fra Met.no | Alle nivåer (gult, oransje, rødt) |

## Slack-meldingsformat

```
*[Vær] Gult farevarsel for is*
Område: Deler av Østlandet
Tidsperiode: 25. februar klokka 12.00 til 25. februar klokka 22.59
Nivå: Gult
Beskrivelse: Fra onsdag ettermiddag er det fare for is...

[ Sjekk kilden her ]
```

## Oppsett

### 1. Klon repo

```bash
git clone https://github.com/martinholterhuset/romerike-weather.git
cd romerike-weather
```

### 2. Opprett Slack Incoming Webhook

1. Gå til [api.slack.com/apps](https://api.slack.com/apps) → *Create New App*
2. Velg *Incoming Webhooks* → aktiver → *Add New Webhook to Workspace*
3. Velg ønsket kanal og kopier webhook-URL

### 3. Legg til GitHub Secrets

Gå til **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Verdi | Påkrevd |
|---|---|---|
| `SLACK_WEBHOOK_URL` | Din Slack webhook-URL | ✅ |
| `FROST_CLIENT_ID` | API-nøkkel fra [frost.met.no](https://frost.met.no/auth/requestCredentials.html) | Valgfritt |

### 4. Kjøreplan

Workflowen kjører automatisk **hver tredje time** (`0 */3 * * *`).

For manuell kjøring: **Actions → Romerike Værvarsling → Run workflow**

## Struktur

```
.
├── .github/
│   └── workflows/
│       └── weather-check.yml   # GitHub Actions workflow
├── weather_check.py            # Hoved-script
└── README.md
```

## Tilpasning

Endre terskelverdier øverst i `weather_check.py`:

```python
THRESHOLDS = {
    "precipitation_1h_mm": 5.0,
    "precipitation_6h_mm": 15.0,
    "precipitation_12h_mm": 25.0,
    "temp_drop_6h": 8.0,
    "temp_rise_6h": 8.0,
    "wind_speed_ms": 15.0,
}
```

For annen lokasjon, endre `LAT`, `LON` og `LOCATION_NAME` øverst i scriptet.
