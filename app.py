import json
import os
import random
import string
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATA_FILE = 'bingo_data.json'
STALE_TIMEOUT = 3600  # seconden zonder heartbeat voordat een spel wordt opgeruimd


def generate_code(length=4):
    """Genereert een willekeurige unieke 4-letterige code (bijv. 'XQRT')."""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


class BingoGame:
    def __init__(self, game_code, token):
        self.game_code = game_code
        self.token = token
        self.called_numbers = []
        self.linked_displays = []
        self.display_theme = 'dark'  # Kan 'dark' of 'light' zijn
        self.last_active = time.time()

    def touch(self):
        """Update de activiteitstijd voor de heartbeat."""
        self.last_active = time.time()

    def to_dict(self):
        return {
            "game_code": self.game_code,
            "token": self.token,
            "called_numbers": self.called_numbers,
            "linked_displays": self.linked_displays,
            "display_theme": self.display_theme,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data):
        game = cls(data.get("game_code", ""), data.get("token", ""))
        game.called_numbers = data.get("called_numbers", [])
        game.linked_displays = data.get("linked_displays", [])
        game.display_theme = data.get("display_theme", "dark")
        game.last_active = data.get("last_active", time.time())
        return game


class Storage:
    """JSON-gebaseerde opslag voor alle actieve spellen en schermen.

    Alle mutaties gebeuren onder een lock en worden daarna atomair
    weggeschreven naar een JSON-bestand, zodat de staat een serverrestart
    overleeft.
    """

    def __init__(self, path=DATA_FILE):
        self.path = path
        self.lock = threading.Lock()
        self.games = {}                # game_code -> BingoGame
        self.pending_displays = set()  # actieve TV-codes die nog wachten op koppeling
        self.display_to_game = {}      # display_code -> game_code
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.games = {
                code: BingoGame.from_dict(g)
                for code, g in data.get('games', {}).items()
            }
            self.pending_displays = set(data.get('pending_displays', []))
            self.display_to_game = data.get('display_to_game', {})
        except (json.JSONDecodeError, OSError) as e:
            print(f"Waarschuwing: kon data niet laden uit {self.path}: {e}")

    def save(self):
        data = {
            "games": {code: g.to_dict() for code, g in self.games.items()},
            "pending_displays": list(self.pending_displays),
            "display_to_game": self.display_to_game,
        }
        # Atomair schrijven: eerst naar een tijdelijk bestand, dan hernoemen.
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)


storage = Storage()


def cleanup_stale_games():
    """Verwijdert spellen die te lang geen heartbeat hebben gehad.

    Voorkomt dat het JSON-bestand onbeperkt groeit met verlopen sessies.
    """
    now = time.time()
    with storage.lock:
        stale = [
            code for code, g in storage.games.items()
            if now - g.last_active > STALE_TIMEOUT
        ]
        for code in stale:
            game = storage.games.pop(code)
            for d_code in game.linked_displays:
                storage.display_to_game.pop(d_code, None)
                storage.pending_displays.add(d_code)
        if stale:
            storage.save()
    return stale


def cleanup_loop():
    while True:
        time.sleep(STALE_TIMEOUT)
        cleanup_stale_games()


# =====================================================================
# HTML ROUTES
# =====================================================================

@app.route('/')
@app.route('/operator')
def operator_index():
    """Laadt het operator dashboard."""
    return render_template('input.html')


@app.route('/display')
def display_index():
    """Genereert een unieke TV-code en toont het wacht/koppelscherm."""
    with storage.lock:
        code = generate_code()
        while code in storage.pending_displays or code in storage.display_to_game:
            code = generate_code()
        storage.pending_displays.add(code)
        storage.save()
    return render_template('display.html', display_code=code)


@app.route('/display/auto_link/<game_code>')
def display_auto_link(game_code):
    """
    Voor 1-op-1 (zelfde computer): opent de TV in een nieuw venster
    en koppelt deze direct op de achtergrond aan het spel.
    """
    game_code = game_code.upper()
    with storage.lock:
        if game_code not in storage.games:
            return "Spel niet gevonden", 404
        code = generate_code()
        while code in storage.pending_displays or code in storage.display_to_game:
            code = generate_code()
        game = storage.games[game_code]
        game.linked_displays.append(code)
        storage.display_to_game[code] = game_code
        storage.save()
    return render_template('display.html', display_code=code)


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.route('/api/create_game', methods=['POST'])
def create_game():
    """Start een nieuw bingospel en geeft de game_code en een veiligheidstoken terug."""
    with storage.lock:
        game_code = generate_code()
        while game_code in storage.games:
            game_code = generate_code()
        token = str(uuid.uuid4())
        storage.games[game_code] = BingoGame(game_code, token)
        storage.save()
    return jsonify({"game_code": game_code, "token": token})


@app.route('/api/join_game/<game_code>', methods=['POST'])
def join_game(game_code):
    """Laat een operator een bestaand spel hervatten via de spelcode."""
    game_code = game_code.upper()
    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spelcode niet gevonden"}), 404
        game.touch()
        storage.save()
        return jsonify({"token": game.token})


@app.route('/api/heartbeat/<game_code>', methods=['POST'])
def heartbeat(game_code):
    """Controleert of de operator nog online is en houdt de sessie actief."""
    game_code = game_code.upper()
    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spel niet gevonden"}), 404
        data = request.json or {}
        token = data.get('token')
        if game.token != token:
            return jsonify({"error": "Niet geautoriseerd"}), 401
        game.touch()
        storage.save()
        return jsonify({"status": "alive"})


@app.route('/api/link_display/<game_code>', methods=['POST'])
def link_display(game_code):
    """Koppelt een fysiek TV-scherm (via de 4-lettercode) aan een spel."""
    game_code = game_code.upper()
    data = request.json or {}
    token = data.get('token')
    display_code = data.get('display_code', '').upper()

    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spel niet gevonden"}), 404
        if game.token != token:
            return jsonify({"error": "Niet geautoriseerd"}), 401
        if display_code not in storage.pending_displays and display_code not in storage.display_to_game:
            return jsonify({"error": "Ongeldige of verlopen TV-code. Herstart het TV-scherm."}), 400

        # Ontkoppel eerst van eventueel vorig spel
        if display_code in storage.display_to_game:
            old_game_code = storage.display_to_game[display_code]
            old_game = storage.games.get(old_game_code)
            if old_game is not None:
                try:
                    old_game.linked_displays.remove(display_code)
                except ValueError:
                    pass

        storage.pending_displays.discard(display_code)
        storage.display_to_game[display_code] = game_code
        if display_code not in game.linked_displays:
            game.linked_displays.append(display_code)

        game.touch()
        storage.save()
        return jsonify({"status": "linked"})


@app.route('/api/unlink_display/<game_code>', methods=['POST'])
def unlink_display(game_code):
    """Ontkoppelt een TV-scherm zodat het weer terug naar het koppelscherm gaat."""
    game_code = game_code.upper()
    data = request.json or {}
    token = data.get('token')
    display_code = data.get('display_code', '').upper()

    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spel niet gevonden"}), 404
        if game.token != token:
            return jsonify({"error": "Niet geautoriseerd"}), 401

        if display_code in game.linked_displays:
            game.linked_displays.remove(display_code)
        storage.display_to_game.pop(display_code, None)
        storage.pending_displays.add(display_code)

        game.touch()
        storage.save()
        return jsonify({"status": "unlinked"})


@app.route('/api/disconnect/<game_code>', methods=['POST'])
def disconnect(game_code):
    """Beëindigt de sessie en stuurt alle gekoppelde TV's terug naar het startscherm."""
    game_code = game_code.upper()
    data = request.json or {}
    token = data.get('token')

    with storage.lock:
        game = storage.games.get(game_code)
        if game is not None and game.token == token:
            for d_code in list(game.linked_displays):
                storage.display_to_game.pop(d_code, None)
                storage.pending_displays.add(d_code)
            storage.games.pop(game_code, None)
            storage.save()
    return jsonify({"status": "disconnected"})


@app.route('/api/action/<game_code>', methods=['POST'])
def game_action(game_code):
    """Verwerkt acties van de operator (getal trekken, herstellen, reset, thema wijzigen)."""
    game_code = game_code.upper()
    data = request.json or {}
    token = data.get('token')
    action = data.get('action')
    number = data.get('number')

    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spel niet gevonden"}), 404
        if game.token != token:
            return jsonify({"error": "Niet geautoriseerd"}), 401

        game.touch()

        if action == 'call':
            if number is not None:
                try:
                    num = int(number)
                except (ValueError, TypeError):
                    num = None
                if num is not None and 1 <= num <= 90 and num not in game.called_numbers:
                    game.called_numbers.append(num)
        elif action == 'undo':
            if game.called_numbers:
                game.called_numbers.pop()
        elif action == 'reset':
            game.called_numbers = []
        elif action == 'set_display_theme':
            theme = data.get('theme', 'dark')
            if theme in ['dark', 'light']:
                game.display_theme = theme
                storage.save()
                return jsonify({"status": "success", "display_theme": game.display_theme})

        storage.save()
        return jsonify({"status": "success"})


@app.route('/api/operator_state/<game_code>')
def operator_state(game_code):
    """Geeft de actuele status van het spel door aan het operatorscherm."""
    game_code = game_code.upper()
    with storage.lock:
        game = storage.games.get(game_code)
        if game is None:
            return jsonify({"error": "Spel niet gevonden"}), 404
        return jsonify({
            "called_numbers": game.called_numbers,
            "linked_displays": game.linked_displays,
            "display_theme": game.display_theme
        })


@app.route('/api/state/<display_code>')
def display_state(display_code):
    """Laat de TV periodiek peilen naar het getrokken getal en het thema."""
    display_code = display_code.upper()
    with storage.lock:
        game_code = storage.display_to_game.get(display_code)
        if not game_code or game_code not in storage.games:
            return jsonify({
                "operator_connected": False
            })
        game = storage.games[game_code]
        last_num = game.called_numbers[-1] if game.called_numbers else None
        return jsonify({
            "operator_connected": True,
            "last_number": last_num,
            "previous_numbers": game.called_numbers,  # De frontend filtert zelf de laatste 5 eruit
            "display_theme": game.display_theme
        })


if __name__ == '__main__':
    # Ruim bij het opstarten alvast verlopen spellen op
    cleanup_stale_games()
    # Achtergrondtaak die verlopen spellen periodiek opruimt.
    # WERKZEUG_RUN_MAIN is alleen 'true' in het echte serverproces (niet de reloader),
    # zodat de thread niet dubbel wordt gestart bij debug=True.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=cleanup_loop, daemon=True).start()
    # Luistert op poort 8000 en is bereikbaar via het lokale netwerk (0.0.0.0)
    app.run(host='0.0.0.0', port=8000, debug=True)
