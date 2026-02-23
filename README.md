# 🌧️ Romerike Værvarsel

GitHub Actions-tjeneste som sjekker vær for Romerike to ganger daglig og sender varsel til Slack.

## Datakilder

| Kilde | API | Hva hentes |
|---|---|---|
| **Met.no** | Locationforecast 2.0 | Timesvarsel for temperatur og nedbør (48t frem) |
| **Met.no MetAlerts** | MetAlerts 2.0 | Aktive farevarsler for Viken/Akershus/Romerike |
| **Norsk klimaservicesenter** | (lenke i Slack-footer) | Klimareferanse / bakgrunn |

## Varsler sendes ved

| Hendelse | Terskel |
|---|---|
| Kraftig nedbør (intensitet) | ≥ 3,0 mm/t |
| Høy akkumulert nedbør | ≥ 20 mm over 12 timer |
| Store temperatursvingninger | ≥ 10 °C innen 12 timer |
| Farevarsel fra Met.no | Alle nivåer (Minor → Extreme) |

## Oppsett

### 1. Fork / klon repo

```bash
git clone https://github.com/<din-bruker>/romerike-weather.git
cd romerike-weather
```

### 2. Legg til Slack Webhook som GitHub Secret

1. Gå til Slack → **Apps** → **Incoming Webhooks** → Opprett en ny webhook for ønsket kanal
2. Kopier webhook-URL (`https://hooks.slack.com/services/...`)
3. Gå til GitHub repo → **Settings** → **Secrets and variables** → **Actions**
4. Klikk **New repository secret**
   - Name: `SLACK_WEBHOOK_URL`
   - Value: din webhook-URL

### 3. Push og aktiver Actions

GitHub Actions kjører automatisk fra `.github/workflows/weather-check.yml`.

Tidspunkter (UTC):
- `0 6 * * *` → **kl. 08:00** norsk vintertid (07:00 UTC+1)
- `0 15 * * *` → **kl. 17:00** norsk vintertid

> Justér cron-tidene i workflow-filen for sommertid (+1 time).

### 4. Manuell kjøring

Gå til **Actions** → **Romerike Værvarsel** → **Run workflow**

Sett `SEND_ALLTID=true` i scriptet for alltid å sende melding (også uten varsler).

## Konfigurasjon

Rediger toppen av `scripts/check_weather.py`:

```python
LAT = 60.1939                        # Koordinater (Gardermoen)
LON = 11.1004
LOCATION_NAME = "Romerike (Gardermoen)"

NEDBOR_THRESHOLD_MM_PER_HOUR = 3.0  # mm/t
NEDBOR_THRESHOLD_MM_12H = 20.0      # mm over 12 timer
TEMP_SWING_THRESHOLD = 10.0         # °C svingning innen 12 timer
```

## Slack-varsel

Varselet viser:
- 🔴 **Aktive farevarsler** med alvorlighetsgrad, tidsperiode og beskrivelse
- ⚠️ **Terskelvarsler** med type, verdi og tidsperiode
- 🌡️ Temperaturspenn neste 48 timer
- Lenker til Met.no og klimaservicesenter.no

## Struktur

```
.
├── .github/
│   └── workflows/
│       └── weather-check.yml   # GitHub Actions workflow
├── scripts/
│   └── check_weather.py        # Hoved-script
└── README.md
```
