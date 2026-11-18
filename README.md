# bingosoft

Bingo-server voor een operatorconsole en één of meer TV-projectieschermen.
De operator trekt nummers (1-90) op `/operator`; schermen openen `/display`,
krijgen een 4-lettercode en worden door de operator gekoppeld aan het spel.
Spelstatus wordt opgeslagen in een JSON-bestand, dus spellen overleven een
serverrestart.

## Snel starten (ontwikkeling)

```bash
pip install -r requirements.txt
python app.py          # op http://localhost:8000
```

Zet `FLASK_DEBUG=1` voor de Werkzeug-reloader tijdens ontwikkeling.
`HOST` en `PORT` zijn instelbaar via omgevingsvariabelen (standaard `0.0.0.0:8000`).

## Productie (Docker)

```bash
docker build -t bingosoft .
docker run -p 8000:8000 -e BINGO_DATA_FILE=/data/bingo_data.json -v bingo-data:/data bingosoft
```

of direct met het gepubliceerde image:

```bash
docker run -p 8000:8000 ghcr.io/woutvde/bingosoft:latest
```

De container draait **gunicorn** (1 worker, 8 threads) in plaats van de
Werkzeug dev-server. Gebruik altijd precies 1 worker: de spelstatus leeft in
het geheugen van het proces plus één JSON-bestand, dus extra workers zouden elk
een eigen, afwijkende staat krijgen.

### Configuratie via omgevingsvariabelen

| Variabele         | Standaard          | Beschrijving                                   |
|-------------------|--------------------|------------------------------------------------|
| `BINGO_DATA_FILE` | `bingo_data.json`  | Pad van het JSON-opslagbestand (mount hier een volume op) |

| `PORT` / `HOST`   | `8000` / `0.0.0.0` | Alleen voor `python app.py` (dev)              |
| `LOG_LEVEL`       | `INFO`             | Logniveau                                      |


### Aanbevelingen voor productie

- Zet de server achter een reverse proxy met TLS (bijv. nginx/Caddy). De app
  zelf terminate geen HTTPS; spelcodes en tokens gaan anders leesbaar over het netwerk.
- Beperk netwerktoegang tot het lokale (VPN-)netwerk; de 4-letter spelcode is
  de enige barrière voor de operatorconsole.
- `/health` is beschikbaar als healthcheck (zit ook als `HEALTHCHECK` in de image).
- Verlopen spellen (1 uur geen heartbeat) worden automatisch opgeruimd door een
  achtergrondtaak; bij het opstarten gebeurt dit meteen een keer.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

De tests draaien met de stdlib `unittest` (geen extra dependencies) tegen een
tijdelijke datastore.

## API-overzicht

| Endpoint | Methode | Beschrijving |
|---|---|---|
| `/` of `/operator` | GET | Operatorconsole |
| `/display` | GET | TV-scherm met nieuwe koppelcode |
| `/display/auto_link/<game_code>` | GET | TV direct gekoppeld aan spel (zelfde machine) |
| `/health` | GET | Healthcheck |
| `/api/create_game` | POST | Nieuw spel → `game_code` + `token` |
| `/api/join_game/<game_code>` | POST | Spel hervatten met code → `token` |
| `/api/heartbeat/<game_code>` | POST | Houdt sessie actief (vereist token) |
| `/api/link_display/<game_code>` | POST | Koppel TV-code aan spel (vereist token) |
| `/api/unlink_display/<game_code>` | POST | Ontkoppel TV (vereist token) |
| `/api/disconnect/<game_code>` | POST | Spel beëindigen (vereist token) |
| `/api/action/<game_code>` | POST | `call` / `undo` / `reset` / `set_display_theme` (vereist token) |
| `/api/operator_state/<game_code>` | GET | Status voor de console |
| `/api/state/<display_code>` | GET | Status voor een TV-scherm |

## CI

GitHub Actions draait bij elke PR de testsuite en bouwt/pusht de Docker-image
naar GHCR (bij push naar `main` en tags `v*`).

## Bestanden

- `app.py` — Flask-applicatie, JSON-opslag en API
- `templates/input.html` — operatorconsole
- `templates/display.html` — projectiescherm
- `bingov3.1.py` — oude tkinter-prototype (niet meer in de webapp gebruikt)
