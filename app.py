import random
import string
import time
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Global in-memory databases
# games: { "GAME_CODE": { "called_numbers": [], "operator_token": "...", "last_heartbeat": timestamp } }
games = {}
# displays: { "DISPLAY_CODE": { "linked_game_code": "..." or None } }
displays = {}

HEARTBEAT_TIMEOUT = 6  # Seconds before game lock releases

def generate_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(chars, k=4))

def is_game_active(game_code):
    if game_code not in games:
        return False
    room = games[game_code]
    if not room.get('operator_token'):
        return False
    return (time.time() - room.get('last_heartbeat', 0)) < HEARTBEAT_TIMEOUT

@app.route('/')
def index():
    return "<h1>Bingo Server Running</h1><a href='/input'>Operatorscherm (Input)</a> | <a href='/display'>Projectiescherm (Display)</a>"

@app.route('/input')
def input_page():
    return render_template('input.html')

# Base display landing: generates a code for the physical screen and redirects
@app.route('/display')
def display_landing():
    while True:
        code = generate_code()
        if code not in displays:
            break
    displays[code] = {'linked_game_code': None}
    return redirect(url_for('display_page', display_code=code))

# The actual screen view
@app.route('/display/<display_code>')
def display_page(display_code):
    display_code = display_code.upper().strip()
    if display_code not in displays:
        displays[display_code] = {'linked_game_code': None}
    return render_template('display.html', display_code=display_code)


# --- OPERATOR API ENDPOINTS ---

@app.route('/api/create_game', methods=['POST'])
def create_game():
    while True:
        game_code = generate_code()
        if game_code not in games:
            break
            
    token = str(uuid.uuid4())
    games[game_code] = {
        'called_numbers': [],
        'operator_token': token,
        'last_heartbeat': time.time()
    }
    return jsonify({'game_code': game_code, 'token': token})

@app.route('/api/join_game/<game_code>', methods=['POST'])
def join_game(game_code):
    game_code = game_code.upper().strip()
    if game_code not in games:
        return jsonify({'error': 'Dit spel bestaat niet.'}), 404
        
    room = games[game_code]
    if is_game_active(game_code):
        return jsonify({'error': 'Dit spel wordt al beheerd door een actieve operator.'}), 403
        
    token = str(uuid.uuid4())
    room['operator_token'] = token
    room['last_heartbeat'] = time.time()
    return jsonify({'token': token})

@app.route('/api/operator_state/<game_code>')
def get_operator_state(game_code):
    game_code = game_code.upper().strip()
    if game_code not in games:
        return jsonify({'error': 'Game not found'}), 404
        
    room = games[game_code]
    called = room['called_numbers']
    
    # Identify which displays are currently routed to this game
    linked = [code for code, data in displays.items() if data['linked_game_code'] == game_code]
    
    return jsonify({
        'called_numbers': called,
        'linked_displays': linked
    })

@app.route('/api/link_display/<game_code>', methods=['POST'])
def link_display(game_code):
    game_code = game_code.upper().strip()
    if not is_game_active(game_code):
        return jsonify({'error': 'Geen actieve sessie.'}), 401
        
    data = request.json or {}
    display_code = data.get('display_code', '').upper().strip()
    token = data.get('token')
    
    if games[game_code]['operator_token'] != token:
        return jsonify({'error': 'Unauthorized'}), 401
        
    if not display_code:
        return jsonify({'error': 'Voer een geldige display code in.'}), 400
        
    # Auto-register display if it doesn't exist yet
    if display_code not in displays:
        displays[display_code] = {'linked_game_code': None}
        
    displays[display_code]['linked_game_code'] = game_code
    return jsonify({'success': True})

@app.route('/api/unlink_display/<game_code>', methods=['POST'])
def unlink_display(game_code):
    game_code = game_code.upper().strip()
    data = request.json or {}
    display_code = data.get('display_code', '').upper().strip()
    token = data.get('token')
    
    if game_code in games and games[game_code]['operator_token'] == token:
        if display_code in displays and displays[display_code]['linked_game_code'] == game_code:
            displays[display_code]['linked_game_code'] = None
            
    return jsonify({'success': True})


# --- SHARED & KEEP-ALIVE ENDPOINTS ---

@app.route('/api/heartbeat/<game_code>', methods=['POST'])
def heartbeat(game_code):
    game_code = game_code.upper().strip()
    if game_code not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.json or {}
    token = data.get('token')
    room = games[game_code]
    
    if room['operator_token'] == token:
        room['last_heartbeat'] = time.time()
        return jsonify({'success': True})
    return jsonify({'error': 'Sessie is verlopen.'}), 401

@app.route('/api/action/<game_code>', methods=['POST'])
def action(game_code):
    game_code = game_code.upper().strip()
    if not is_game_active(game_code):
        return jsonify({'error': 'Sessie niet actief.'}), 401
        
    data = request.json or {}
    token = data.get('token')
    room = games[game_code]
    
    if room['operator_token'] != token:
        return jsonify({'error': 'Unauthorized'}), 401
        
    action_type = data.get('action')
    called_list = room['called_numbers']
    
    if action_type == 'call':
        number = data.get('number')
        if number not in called_list:
            called_list.append(number)
    elif action_type == 'undo':
        if called_list:
            called_list.pop()
    elif action_type == 'reset':
        room['called_numbers'] = []
        
    room['last_heartbeat'] = time.time()
    return jsonify({'success': True})

@app.route('/api/state/<display_code>')
def get_display_state(display_code):
    display_code = display_code.upper().strip()
    if display_code not in displays:
        displays[display_code] = {'linked_game_code': None}
        
    linked_game = displays[display_code]['linked_game_code']
    
    # If display is mapped to an ACTIVE game, return game state
    if linked_game and is_game_active(linked_game):
        room = games[linked_game]
        called = room['called_numbers']
        last = called[-1] if called else ""
        previous = called[-6:-1] if len(called) > 1 else []
        return jsonify({
            'called_numbers': called,
            'last_number': last,
            'previous_numbers': previous,
            'operator_connected': True
        })
    else:
        # Auto-unlink if game is dead, revert to showing local code
        displays[display_code]['linked_game_code'] = None
        return jsonify({
            'called_numbers': [],
            'last_number': '',
            'previous_numbers': [],
            'operator_connected': False
        })

@app.route('/api/disconnect/<game_code>', methods=['POST'])
def disconnect(game_code):
    game_code = game_code.upper().strip()
    if game_code in games:
        data = request.json or {}
        token = data.get('token')
        room = games[game_code]
        if room['operator_token'] == token:
            room['operator_token'] = None
            room['last_heartbeat'] = 0
            # Instantly unlock all displays hooked to this game
            for d_code, d_data in displays.items():
                if d_data['linked_game_code'] == game_code:
                    d_data['linked_game_code'] = None
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)