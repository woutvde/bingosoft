# bingosoft

Bingo server with an operator console and one or more TV projection screens.
The operator draws numbers (1-90) on `/operator`; screens open `/display`, get
a 4-letter code, and are linked to the game by the operator. Game state is
stored in a JSON file, so games survive a server restart.

The UI is available in **English, Dutch, German and French** via the language
picker (top right on the console, on the setup screen of the display). The
choice is stored in `localStorage`; without a choice the browser language is
used, falling back to Dutch. Server error messages follow the `lang` field
sent by the frontend (`en`/`nl`/`de`/`fr`, default `nl`).

## Quick start (development)

```bash
pip install -r requirements.txt
python app.py          # on http://localhost:8000
```

Set `FLASK_DEBUG=1` for the Werkzeug reloader during development.
`HOST` and `PORT` can be set via environment variables (default `0.0.0.0:8000`).

## Production (Docker)

```bash
docker build -t bingosoft .
docker run -p 8000:8000 -e BINGO_DATA_FILE=/data/bingo_data.json -v bingo-data:/data bingosoft
```

or directly with the published image:

```bash
docker run -p 8000:8000 ghcr.io/woutvde/bingosoft:latest
```

The container runs **gunicorn** (1 worker, 8 threads) instead of the Werkzeug
dev server. Always use exactly 1 worker: game state lives in the process
memory plus a single JSON file, so extra workers would each get a divergent
state.

### Configuration via environment variables

| Variable          | Default            | Description                                             |
|-------------------|--------------------|---------------------------------------------------------|
| `BINGO_DATA_FILE` | `bingo_data.json`  | Path of the JSON storage file (mount a volume here)     |
| `PORT` / `HOST`   | `8000` / `0.0.0.0` | Only used by `python app.py` (development)              |
| `LOG_LEVEL`       | `INFO`             | Log level                                               |

### Recommendations for production

- Put the server behind a reverse proxy with TLS (e.g. nginx/Caddy). The app
  itself does not terminate HTTPS; otherwise game codes and tokens travel
  readable over the network.
- Restrict network access to the local (VPN) network; the 4-letter game code
  is the only barrier to the operator console.
- `/health` is available as a health check (also configured as `HEALTHCHECK`
  in the image).
- Expired games (no heartbeat for 1 hour) are cleaned up automatically by a
  background task, and once at startup.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

The tests use the stdlib `unittest` (no extra dependencies) against a
temporary datastore.

## API overview

| Endpoint | Method | Description |
|---|---|---|
| `/` or `/operator` | GET | Operator console |
| `/display` | GET | TV screen with a new pairing code |
| `/display/auto_link/<game_code>` | GET | TV screen linked directly to a game (same machine) |
| `/health` | GET | Health check |
| `/api/create_game` | POST | New game → `game_code` + `token` |
| `/api/join_game/<game_code>` | POST | Resume a game by code → `token` |
| `/api/heartbeat/<game_code>` | POST | Keep the session alive (requires token) |
| `/api/link_display/<game_code>` | POST | Link a TV code to the game (requires token) |
| `/api/unlink_display/<game_code>` | POST | Unlink a TV (requires token) |
| `/api/disconnect/<game_code>` | POST | End the game (requires token) |
| `/api/action/<game_code>` | POST | `call` / `undo` / `reset` / `set_display_theme` (requires token) |
| `/api/operator_state/<game_code>` | GET | State for the console |
| `/api/state/<display_code>` | GET | State for a TV screen |

## CI

GitHub Actions runs the test suite on every PR and builds/pushes the Docker
image to GHCR (on pushes to `main` and tags `v*`).

## Files

- `app.py` — Flask application, JSON storage and API
- `templates/input.html` — operator console
- `templates/display.html` — projection screen
- `static/i18n.js` — UI translations (EN/NL/DE/FR) and language picker logic
- `bingov3.1.py` — old tkinter prototype (no longer used by the web app)
