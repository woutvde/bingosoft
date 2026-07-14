import random
import string
import time
import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Global in-memory games database
# Structure: { "CODE": { "called_numbers": [], "operator_token": None, "last_heartbeat": 0 } }
games = {}

HEARTBEAT_TIMEOUT = 6  # Seconds before lock automatically releases

def generate_room_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code = ''.join(random.choices(chars, k=4))
        if code not in games:
            return code

def is_operator_active(room):
    """Returns True if an operator has checked in within the timeout window."""
    if not room.get('operator_token'):
        return False
    return (time.time() - room.get('last_heartbeat', 0)) < HEARTBEAT_TIMEOUT

@app.route('/')
def index():
    return "<h1>Bingo Server Running</h1><a href='/input'>Operatorscherm (Input)</a> | <a href='/display'>Projectiescherm (Display)</a>"

@app.route('/input')
def input_page():
    return render_template('input.html')

@app.route('/display')
def display_page():
    return render_template('display.html')

@app.route('/api/create_room', methods=['POST'])
def create_room():
    code = generate_room_code()
    games[code] = {
        'called_numbers': [],
        'operator_token': None,
        'last_heartbeat': 0
    }
    return jsonify({'room_code': code})

@app.route('/api/join_room/<room_code>', methods=['POST'])
def join_room(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Deze room bestaat niet.'}), 404
    
    room = games[room_code]
    
    # Block connection if another operator is currently active
    if is_operator_active(room):
        return jsonify({'error': 'Deze room is al bezet door een andere operator.'}), 403
    
    # Assign unique token to this operator
    token = str(uuid.uuid4())
    room['operator_token'] = token
    room['last_heartbeat'] = time.time()
    
    return jsonify({'token': token})

@app.route('/api/state/<room_code>')
def get_state(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Room not found'}), 404
        
    room = games[room_code]
    called = room['called_numbers']
    last = called[-1] if called else ""
    previous = called[-6:-1] if len(called) > 1 else []
    
    return jsonify({
        'called_numbers': called,
        'last_number': last,
        'previous_numbers': previous,
        'operator_connected': is_operator_active(room)
    })

@app.route('/api/heartbeat/<room_code>', methods=['POST'])
def heartbeat(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Room not found'}), 404
    
    data = request.json or {}
    token = data.get('token')
    room = games[room_code]
    
    # Confirm this heartbeat belongs to the currently registered token
    if room['operator_token'] == token:
        room['last_heartbeat'] = time.time()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Sessie is verlopen of ongeldig.'}), 401

@app.route('/api/action/<room_code>', methods=['POST'])
def action(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Room not found'}), 404
        
    data = request.json or {}
    token = data.get('token')
    room = games[room_code]
    
    # Prevent execution if token does not match active operator
    if not token or room['operator_token'] != token or not is_operator_active(room):
        return jsonify({'error': 'Geen actieve operator privileges.'}), 401
        
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
        
    # Actions extend the heartbeat
    room['last_heartbeat'] = time.time()
    return jsonify({'success': True})

@app.route('/api/disconnect/<room_code>', methods=['POST'])
def disconnect(room_code):
    room_code = room_code.upper().strip()
    if room_code in games:
        data = request.json or {}
        token = data.get('token')
        room = games[room_code]
        if room['operator_token'] == token:
            room['operator_token'] = None
            room['last_heartbeat'] = 0
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)