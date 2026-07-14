from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory state. (Requires running Gunicorn with exactly 1 worker)
game_state = {
    'called_numbers': []
}

@app.route('/')
def index():
    return "<h1>Bingo Server Running</h1><a href='/input'>Operatorscherm (Input)</a> | <a href='/display'>Projectiescherm (Display)</a>"

@app.route('/input')
def input_page():
    return render_template('input.html')

@app.route('/display')
def display_page():
    return render_template('display.html')

@app.route('/api/state')
def get_state():
    called = game_state['called_numbers']
    last = called[-1] if called else ""
    
    # Get up to 5 previous numbers (excluding the current 'last' one)
    previous = called[-6:-1] if len(called) > 1 else []
    
    return jsonify({
        'called_numbers': called,
        'last_number': last,
        'previous_numbers': previous
    })

@app.route('/api/action', methods=['POST'])
def action():
    data = request.json
    action_type = data.get('action')
    
    if action_type == 'call':
        number = data.get('number')
        if number not in game_state['called_numbers']:
            game_state['called_numbers'].append(number)
    
    elif action_type == 'undo':
        if game_state['called_numbers']:
            game_state['called_numbers'].pop()
            
    elif action_type == 'reset':
        game_state['called_numbers'] = []
        
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)