# ADS-B Flight Monitoring System

Et robust Python-system for sanntidsovervåking av flytrafikk via ADS-B Exchange API med automatiske Slack-varsler.

## 🎯 Funksjoner

- **Geofencing med H3**: Overvåker fly i spesifikke geografiske områder definert ved H3-celler
- **Nødvarsel**: Umiddelbar varsling ved emergency squawk-koder (7700, 7600, 7500)
- **Spesifikke fartøy**: Overvåker utvalgte helikoptre/fly basert på hex-koder
- **Duplikatfiltrering**: Unngår gjentatte varsler for samme fly
- **Slack-integrasjon**: Rikt formaterte varsler med kart-lenker og flydetaljer
- **Robust feilhåndtering**: Fortsetter ved API-feil eller nettverksproblemer
- **Konfigurerbar**: Støtter både konfigurasjonsfil og miljøvariabler

## 📋 Forutsetninger

- Python 3.7+
- ADS-B Exchange API-tilgang (via RapidAPI eller direkte)
- Slack workspace med webhook-tilgang

## 🚀 Hurtigstart

### 1. Installer avhengigheter

```bash
pip install -r requirements.txt
```

### 2. Konfigurer Slack

Opprett en Slack webhook:
1. Gå til https://api.slack.com/apps
2. Opprett ny app → "Incoming Webhooks" → Aktiver
3. Opprett webhook for ønsket kanal
4. Kopier URL-en

**Sett miljøvariabel:**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX"
```

### 3. Test oppsettet

```bash
python3 test_setup.py
```

Dette verifiserer:
- ✅ Python-pakker er installert
- ✅ H3 geospatial-funksjoner fungerer
- ✅ Slack webhook er konfigurert
- ✅ ADS-B API er tilgjengelig

### 4. Kjør overvåkingen

**Manuell kjøring:**
```bash
python3 adsb_monitor.py
```

**Med cron (hvert minutt):**
```bash
crontab -e
# Legg til:
* * * * * /usr/bin/python3 /full/sti/til/adsb_monitor.py
```

## 📁 Filer

| Fil | Beskrivelse |
|-----|-------------|
| `adsb_monitor.py` | Hovedscript (hardkodede verdier) |
| `adsb_monitor_enhanced.py` | Forbedret versjon med config-støtte |
| `test_setup.py` | Testscript for verifikasjon |
| `requirements.txt` | Python-avhengigheter |
| `config.json.template` | Konfigurasjonsfil-mal |
| `INSTALLASJON.md` | Detaljert installasjonsveiledning |
| `adsb-monitor.service` | Systemd service-fil |
| `adsb-monitor.timer` | Systemd timer-fil |

## ⚙️ Konfigurasjon

### Med konfigurasjonsfil (anbefalt)

1. Kopier template:
```bash
cp config.json.template config.json
```

2. Rediger `config.json`:
```json
{
  "slack": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/REAL/WEBHOOK"
  },
  "monitoring": {
    "h3_cells": ["599130781545136127", ...],
    "monitored_aircraft": {
      "479C1E": "LN-ORA"
    }
  }
}
```

3. Bruk enhanced version:
```bash
python3 adsb_monitor_enhanced.py
```

### Med miljøvariabler

```bash
export SLACK_WEBHOOK_URL="your_webhook_url"
export ADSB_API_KEY="your_api_key"
python3 adsb_monitor.py
```

## 🗺️ H3 Geofencing

### Finne H3-celler for ditt område

```python
import h3

# Dine koordinater
lat, lon = 59.9139, 10.7522

# Generer H3-celle (resolution 8)
h3_cell = h3.geo_to_h3(lat, lon, 8)
print(f"H3 cell: {h3_cell}")

# Få naboområder
neighbors = h3.k_ring(h3_cell, 1)
print(f"Neighboring cells: {neighbors}")
```

### Visualisere H3-celler

Bruk [H3 Viewer](https://wolf-j.github.io/h3-viewer/) for å se cellene på kart.

## 🔔 Alert-kriterier

### Emergency Squawk-koder

| Kode | Betydning | Prioritet |
|------|-----------|-----------|
| 7700 | Emergency | 🔴 Kritisk |
| 7600 | Radio Failure | 🟠 Høy |
| 7500 | Hijack | 🔴 Kritisk |

### Overvåkede fartøy

Definert i `MONITORED_HEX_CODES`:
```python
{
    "479C1E": "LN-ORA",  # Norsk luftambulanse
    "479B34": "LN-ORB",
    # ... flere
}
```

## 📊 Logging

### Loggfiler

- **Hovedlogg**: `/tmp/adsb_monitor.log`
- **State-fil**: `/tmp/adsb_monitor_state.json`

### Overvåke logger

```bash
# Sanntids-logging
tail -f /tmp/adsb_monitor.log

# Sjekk feil
grep ERROR /tmp/adsb_monitor.log

# Antall varsler sendt i dag
grep "Slack alert sent" /tmp/adsb_monitor.log | grep $(date +%Y-%m-%d) | wc -l
```

## 🔧 Avansert oppsett

### Systemd Timer (anbefalt for produksjon)

1. Kopier service-filer:
```bash
sudo cp adsb-monitor.service /etc/systemd/system/
sudo cp adsb-monitor.timer /etc/systemd/system/
```

2. Rediger service-filen:
```bash
sudo nano /etc/systemd/system/adsb-monitor.service
# Oppdater brukernavn, gruppe og stier
```

3. Aktiver og start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable adsb-monitor.timer
sudo systemctl start adsb-monitor.timer
```

4. Sjekk status:
```bash
sudo systemctl status adsb-monitor.timer
sudo journalctl -u adsb-monitor -f
```

### Logrotate

Opprett `/etc/logrotate.d/adsb-monitor`:
```
/tmp/adsb_monitor.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0640 youruser yourgroup
}
```

## 🛡️ Sikkerhet

### Best Practices

1. **Aldri commit API-nøkler til Git**
   ```bash
   echo "config.json" >> .gitignore
   echo "*.log" >> .gitignore
   ```

2. **Bruk miljøvariabler i produksjon**
   ```bash
   # ~/.bashrc eller ~/.profile
   export SLACK_WEBHOOK_URL="..."
   export ADSB_API_KEY="..."
   ```

3. **Begrens filtilganger**
   ```bash
   chmod 700 adsb_monitor.py
   chmod 600 config.json
   ```

4. **Rate limiting**
   - ADS-B Exchange har typisk 100 forespørsler/time
   - Juster cron-intervall ved behov:
     ```cron
     */2 * * * *  # Hvert 2. minutt
     */5 * * * *  # Hvert 5. minutt
     ```

## 🐛 Feilsøking

### Ingen data fra API

```bash
# Test API manuelt
curl -H "X-RapidAPI-Key: YOUR_KEY" \
     -H "X-RapidAPI-Host: adsbexchange-com1.p.rapidapi.com" \
     "https://adsbexchange-com1.p.rapidapi.com/v2/lat/59.9139/lon/10.7522/dist/50/"
```

### Slack-varsler sendes ikke

1. Test webhook:
```bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"Test"}' $SLACK_WEBHOOK_URL
```

2. Sjekk logger:
```bash
grep "Slack alert" /tmp/adsb_monitor.log
```

### Duplikate varsler

- Øk `ALERT_COOLDOWN_MINUTES` i config
- Verifiser at state-filen oppdateres:
```bash
cat /tmp/adsb_monitor_state.json
```

### Ingen fly registreres i området

1. Verifiser H3-celler:
```python
import h3
# Test om dine koordinater er i listen
lat, lon = 59.9139, 10.7522
cell = h3.geo_to_h3(lat, lon, 8)
print(f"Din celle: {cell}")
# Sjekk om den matcher MONITORED_H3_CELLS
```

2. Utvid søkeradius i config:
```json
"radius_nautical_miles": 150
```

## 📈 Ytelse

### Optimalisering

- **API-kall**: ~1 forespørsel/minutt = 1440/dag
- **Responstid**: Typisk 200-500ms
- **Minnebruk**: <50MB
- **CPU**: Minimal (<1% på moderne system)

### Skalering

For flere områder:
```python
# Kjør flere instanser med forskjellige config-filer
python3 adsb_monitor_enhanced.py --config oslo.json &
python3 adsb_monitor_enhanced.py --config bergen.json &
```

## 📚 Ressurser

- [ADS-B Exchange Documentation](https://www.adsbexchange.com/data/)
- [H3 Geospatial Indexing](https://h3geo.org/)
- [Slack Webhooks Guide](https://api.slack.com/messaging/webhooks)
- [Squawk Codes Reference](https://www.skybrary.aero/articles/transponder-squawk-codes)

## 🤝 Bidrag

Forslag til forbedringer:
1. Fork repository
2. Opprett feature branch
3. Test grundig
4. Submit pull request

## 📄 Lisens

Dette scriptet er laget for privat bruk. Respekter ADS-B Exchange sine bruksvilkår.

## ⚠️ Disclaimer

- Data fra ADS-B Exchange kan ha forsinkelser (typisk 30-60 sekunder)
- Emergency squawk-koder kan være feilaktige (pilotfeil, testing)
- Systemet er for informasjonsformål - ikke for kritisk sikkerhet
- Følg alltid lokale lover om privatliv og datainnsamling

## 📞 Support

For problemer med:
- **Scriptet**: Se INSTALLASJON.md eller kjør test_setup.py
- **ADS-B Exchange API**: https://www.adsbexchange.com/contact/
- **Slack Webhooks**: https://api.slack.com/support

---

**Versjon**: 1.0  
**Sist oppdatert**: Februar 2026  
**Kompatibilitet**: Python 3.7+, ADS-B Exchange API v2
