import random
import string
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Global in-memory dictionary holding multiple games
# Structure: { "CODE": { "called_numbers": [] } }
games = {}

def generate_room_code():
    # Filtered characters to prevent human reading errors (No O, 0, I, 1)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code = ''.join(random.choices(chars, k=4))
        if code not in games:
            return code

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
        'called_numbers': []
    }
    return jsonify({'room_code': code})

@app.route('/api/check_room/<room_code>')
def check_room(room_code):
    room_code = room_code.upper().strip()
    exists = room_code in games
    return jsonify({'exists': exists})

@app.route('/api/state/<room_code>')
def get_state(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Room not found'}), 404
        
    called = games[room_code]['called_numbers']
    last = called[-1] if called else ""
    
    # Get up to 5 previous numbers (excluding the current 'last' one)
    previous = called[-6:-1] if len(called) > 1 else []
    
    return jsonify({
        'called_numbers': called,
        'last_number': last,
        'previous_numbers': previous
    })

@app.route('/api/action/<room_code>', methods=['POST'])
def action(room_code):
    room_code = room_code.upper().strip()
    if room_code not in games:
        return jsonify({'error': 'Room not found'}), 404
        
    data = request.json
    action_type = data.get('action')
    called_list = games[room_code]['called_numbers']
    
    if action_type == 'call':
        number = data.get('number')
        if number not in called_list:
            called_list.append(number)
    
    elif action_type == 'undo':
        if called_list:
            called_list.pop()
            
    elif action_type == 'reset':
        games[room_code]['called_numbers'] = []
        
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)