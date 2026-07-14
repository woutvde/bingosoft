import random
import string
import time
import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory database voor actieve games en schermen
games = {}             # Sleutel: game_code (str) -> BingoGame object
pending_displays = set() # Verzameling van actieve TV-codes die nog wachten op koppeling
display_to_game = {}    # Sleutel: display_code (str) -> game_code (str)

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
    code = generate_code()
    while code in pending_displays or code in display_to_game:
        code = generate_code()
    
    pending_displays.add(code)
    return render_template('display.html', display_code=code)


@app.route('/display/auto_link/<game_code>')
def display_auto_link(game_code):
    """
    Voor 1-op-1 (zelfde computer): opent de TV in een nieuw venster
    en koppelt deze direct op de achtergrond aan het spel.
    """
    game_code = game_code.upper()
    code = generate_code()
    while code in pending_displays or code in display_to_game:
        code = generate_code()
    
    if game_code in games:
        game = games[game_code]
        game.linked_displays.append(code)
        display_to_game[code] = game_code
        
    return render_template('display.html', display_code=code)


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.route('/api/create_game', methods=['POST'])
def create_game():
    """Start een nieuw bingospel en geeft de game_code en een veiligheidstoken terug."""
    game_code = generate_code()
    while game_code in games:
        game_code = generate_code()
        
    token = str(uuid.uuid4())
    games[game_code] = BingoGame(game_code, token)
    return jsonify({"game_code": game_code, "token": token})


@app.route('/api/join_game/<game_code>', methods=['POST'])
def join_game(game_code):
    """Laat een operator een bestaand spel hervatten via de spelcode."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spelcode niet gevonden"}), 404
    
    game = games[game_code]
    game.touch()
    return jsonify({"token": game.token})


@app.route('/api/heartbeat/<game_code>', methods=['POST'])
def heartbeat(game_code):
    """Controleert of de operator nog online is en houdt de sessie actief."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spel niet gevonden"}), 404
        
    data = request.json or {}
    token = data.get('token')
    game = games[game_code]
    
    if game.token != token:
        return jsonify({"error": "Niet geautoriseerd"}), 401
        
    game.touch()
    return jsonify({"status": "alive"})


@app.route('/api/link_display/<game_code>', methods=['POST'])
def link_display(game_code):
    """Koppelt een fysiek TV-scherm (via de 4-lettercode) aan een spel."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spel niet gevonden"}), 404
        
    data = request.json or {}
    token = data.get('token')
    display_code = data.get('display_code', '').upper()
    
    game = games[game_code]
    if game.token != token:
        return jsonify({"error": "Niet geautoriseerd"}), 401
        
    if display_code not in pending_displays and display_code not in display_to_game:
        return jsonify({"error": "Ongeldige of verlopen TV-code. Herstart het TV-scherm."}), 400
        
    # Ontkoppel eerst van eventueel vorig spel
    if display_code in display_to_game:
        old_game = display_to_game[display_code]
        if old_game in games:
            try:
                games[old_game].linked_displays.remove(display_code)
            except ValueError:
                pass
                
    if display_code in pending_displays:
        pending_displays.remove(display_code)
        
    display_to_game[display_code] = game_code
    if display_code not in game.linked_displays:
        game.linked_displays.append(display_code)
        
    game.touch()
    return jsonify({"status": "linked"})


@app.route('/api/unlink_display/<game_code>', methods=['POST'])
def unlink_display(game_code):
    """Ontkoppelt een TV-scherm zodat het weer terug naar het koppelscherm gaat."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spel niet gevonden"}), 404
        
    data = request.json or {}
    token = data.get('token')
    display_code = data.get('display_code', '').upper()
    
    game = games[game_code]
    if game.token != token:
        return jsonify({"error": "Niet geautoriseerd"}), 401
        
    if display_code in game.linked_displays:
        game.linked_displays.remove(display_code)
    if display_code in display_to_game:
        del display_to_game[display_code]
        
    pending_displays.add(display_code)
    game.touch()
    return jsonify({"status": "unlinked"})


@app.route('/api/disconnect/<game_code>', methods=['POST'])
def disconnect(game_code):
    """Beëindigt de sessie en stuurt alle gekoppelde TV's terug naar het startscherm."""
    game_code = game_code.upper()
    if game_code in games:
        data = request.json or {}
        token = data.get('token')
        game = games[game_code]
        if game.token == token:
            for d_code in list(game.linked_displays):
                if d_code in display_to_game:
                    del display_to_game[d_code]
                pending_displays.add(d_code)
            del games[game_code]
    return jsonify({"status": "disconnected"})


@app.route('/api/action/<game_code>', methods=['POST'])
def game_action(game_code):
    """Verwerkt acties van de operator (getal trekken, herstellen, reset, thema wijzigen)."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spel niet gevonden"}), 404
        
    data = request.json or {}
    token = data.get('token')
    action = data.get('action')
    number = data.get('number')
    
    game = games[game_code]
    if game.token != token:
        return jsonify({"error": "Niet geautoriseerd"}), 401
        
    game.touch()
    
    if action == 'call':
        try:
            num = int(number)
            if 1 <= num <= 90 and num not in game.called_numbers:
                game.called_numbers.append(num)
        except (ValueError, TypeError):
            pass
    elif action == 'undo':
        if game.called_numbers:
            game.called_numbers.pop()
    elif action == 'reset':
        game.called_numbers = []
    elif action == 'set_display_theme':
        theme = data.get('theme', 'dark')
        if theme in ['dark', 'light']:
            game.display_theme = theme
            return jsonify({"status": "success", "display_theme": game.display_theme})
            
    return jsonify({"status": "success"})


@app.route('/api/operator_state/<game_code>')
def operator_state(game_code):
    """Geeft de actuele status van het spel door aan het operatorscherm."""
    game_code = game_code.upper()
    if game_code not in games:
        return jsonify({"error": "Spel niet gevonden"}), 404
        
    game = games[game_code]
    return jsonify({
        "called_numbers": game.called_numbers,
        "linked_displays": game.linked_displays,
        "display_theme": game.display_theme
    })


@app.route('/api/state/<display_code>')
def display_state(display_code):
    """Laat de TV periodiek peilen naar het getrokken getal en het thema."""
    display_code = display_code.upper()
    game_code = display_to_game.get(display_code)
    
    if not game_code or game_code not in games:
        return jsonify({
            "operator_connected": False
        })
        
    game = games[game_code]
    last_num = game.called_numbers[-1] if game.called_numbers else None
    
    return jsonify({
        "operator_connected": True,
        "last_number": last_num,
        "previous_numbers": game.called_numbers, # De frontend filtert zelf de laatste 5 eruit
        "display_theme": game.display_theme
    })


if __name__ == '__main__':
    # Luistert op poort 8000 en is bereikbaar via het lokale netwerk (0.0.0.0)
    app.run(host='0.0.0.0', port=8000, debug=True)