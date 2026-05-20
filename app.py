from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import os
import random
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database setup
DATABASE = 'games.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );
            
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                category_id INTEGER NOT NULL,
                image_url TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
            
            CREATE TABLE IF NOT EXISTS user_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                score INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (game_id) REFERENCES games(id)
            );
        ''')
        db.commit()
        
        # Add sample data if empty
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            categories = [
                ('Action', 'Fast-paced games'),
                ('Puzzle', 'Brain-teasing challenges'),
                ('Adventure', 'Exploration and story'),
                ('Strategy', 'Tactical gameplay'),
            ]
            db.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)
            
            games = [
                ('Space Invaders', 'Classic arcade shooter', 1, 'https://via.placeholder.com/300x200?text=Space+Invaders'),
                ('Tetris', 'Stack the falling blocks', 2, 'https://via.placeholder.com/300x200?text=Tetris'),
                ('Chess Online', 'Strategic board game', 4, 'https://via.placeholder.com/300x200?text=Chess'),
                ('Dragon Quest', 'Epic adventure awaits', 3, 'https://via.placeholder.com/300x200?text=Dragon+Quest'),
            ]
            db.executemany("INSERT INTO games (name, description, category_id, image_url) VALUES (?, ?, ?, ?)", games)
            db.commit()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Game state helpers

def get_user_game_states():
    return session.get('game_states', {})


def get_game_state(gamename):
    return get_user_game_states().get(gamename)


def save_game_state(gamename, state):
    states = get_user_game_states()
    states[gamename] = state
    session['game_states'] = states
    session.modified = True


def initialize_chess_board():
    return [
        ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
        ['bp'] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        ['wp'] * 8,
        ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr'],
    ]


def initialize_game_state(game_name):
    if game_name == 'Space Invaders':
        return {
            'type': 'space_invaders',
            'width': 5,
            'height': 5,
            'aliens': [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
            'ship_col': 2,
            'bullet': None,
            'score': 0,
            'status': 'playing',
            'message': 'Aim and fire to defend your ship!',
        }
    if game_name == 'Tetris':
        return {
            'type': 'tetris',
            'rows': 10,
            'cols': 6,
            'board': [[0] * 6 for _ in range(10)],
            'piece': {'row': 0, 'col': 2},
            'score': 0,
            'status': 'playing',
            'message': 'Use the controls to move and drop the block.',
        }
    if game_name == 'Chess Online':
        return {
            'type': 'chess_online',
            'board': initialize_chess_board(),
            'turn': 'white',
            'status': 'playing',
            'message': 'White to move. Use squares like e2 and e4.',
        }
    if game_name == 'Dragon Quest':
        return {
            'type': 'dragon_quest',
            'location': 'village',
            'hp': 20,
            'dragon_hp': 30,
            'inventory': ['Healing Potion'],
            'status': 'playing',
            'message': 'Your quest begins in the village. Explore the world and defeat the dragon!',
        }
    return {
        'type': 'unknown',
        'status': 'ended',
        'message': 'This game is not yet playable.',
    }


def render_space_invaders_board(state):
    board = []
    aliens = state['aliens']
    bullet = state['bullet']
    for row_index in range(len(aliens)):
        row = []
        for col_index in range(state['width']):
            if aliens[row_index][col_index] == 1:
                row.append('👾')
            elif bullet and bullet['row'] == row_index and bullet['col'] == col_index:
                row.append('🔺')
            else:
                row.append('·')
        board.append(row)
    ship_row = ['·'] * state['width']
    ship_row[state['ship_col']] = '🚀'
    board.append(ship_row)
    return board


def render_tetris_board(state):
    board = []
    current = {(state['piece']['row'] + dr, state['piece']['col'] + dc) for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]}
    for row_index, row in enumerate(state['board']):
        display_row = []
        for col_index, cell in enumerate(row):
            if (row_index, col_index) in current:
                display_row.append('🟦')
            elif cell:
                display_row.append('🟪')
            else:
                display_row.append('·')
        board.append(display_row)
    return board


def render_chess_board(state):
    icons = {
        'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
        'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟︎',
    }
    board = []
    for row in state['board']:
        display_row = [icons.get(cell, '·') for cell in row]
        board.append(display_row)
    return board


def render_dragon_quest_board(state):
    inventory = ', '.join(state['inventory']) if state['inventory'] else 'Empty'
    return [
        ['Location:', state['location'].title()],
        ['HP:', str(state['hp'])],
        ['Dragon HP:', str(state['dragon_hp'])],
        ['Inventory:', inventory],
    ]


def all_aliens_dead(aliens):
    return all(cell == 0 for row in aliens for cell in row)


def update_space_invaders_bullet(state):
    if not state['bullet']:
        return state
    row = state['bullet']['row']
    col = state['bullet']['col']
    if row < 0:
        state['bullet'] = None
        return state
    if row < len(state['aliens']) and state['aliens'][row][col] == 1:
        state['aliens'][row][col] = 0
        state['bullet'] = None
        state['score'] += 100
        state['message'] = 'Direct hit!'
        return state
    state['bullet']['row'] = row - 1
    if state['bullet']['row'] < 0:
        state['bullet'] = None
        state['message'] = 'You missed this time.'
    return state


def advance_space_invaders_aliens(state):
    if all_aliens_dead(state['aliens']):
        state['status'] = 'won'
        state['message'] = 'You destroyed all invaders!'
        return state
    width = state['width']
    aliens = state['aliens']
    moved = [[0] * width] + aliens[:-1]
    state['aliens'] = moved
    if any(moved[-1]):
        state['status'] = 'lost'
        state['message'] = 'The invaders have reached your ship!'
    elif all_aliens_dead(moved):
        state['status'] = 'won'
        state['message'] = 'You destroyed all invaders!'
    elif state['status'] == 'playing':
        state['message'] = state.get('message', 'Keep shooting!')
    return state


def process_space_invaders_action(state, action):
    if action == 'restart':
        return initialize_game_state('Space Invaders')
    if state['status'] != 'playing':
        return state
    if action and action.startswith('fire_'):
        col = int(action.split('_')[1])
        if state['bullet'] is None:
            state['bullet'] = {'row': len(state['aliens']) - 1, 'col': col}
            state['message'] = f'Fired into column {col + 1}.'
        else:
            state['message'] = 'The bullet is still in the air.'
    state = update_space_invaders_bullet(state)
    if state['status'] == 'playing':
        state = advance_space_invaders_aliens(state)
    return state


def can_place_tetris_piece(board, row, col):
    shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
    rows, cols = len(board), len(board[0])
    for dr, dc in shape:
        r, c = row + dr, col + dc
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c]:
            return False
    return True


def fix_tetris_piece(state):
    shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for dr, dc in shape:
        r = state['piece']['row'] + dr
        c = state['piece']['col'] + dc
        if 0 <= r < state['rows'] and 0 <= c < state['cols']:
            state['board'][r][c] = 1


def clear_tetris_lines(state):
    full_rows = [row for row in state['board'] if all(cell == 1 for cell in row)]
    if not full_rows:
        return 0
    state['board'] = [[0] * state['cols'] for _ in full_rows] + [row for row in state['board'] if any(cell == 0 for cell in row)]
    return len(full_rows)


def spawn_tetris_piece(state):
    state['piece'] = {'row': 0, 'col': 2}
    if not can_place_tetris_piece(state['board'], state['piece']['row'], state['piece']['col']):
        state['status'] = 'lost'
        state['message'] = 'The board is full. Game over!'


def process_tetris_action(state, action):
    if action == 'restart':
        return initialize_game_state('Tetris')
    if state['status'] != 'playing':
        return state
    row = state['piece']['row']
    col = state['piece']['col']
    if action == 'move_left' and can_place_tetris_piece(state['board'], row, col - 1):
        col -= 1
        state['message'] = 'Moved left.'
    elif action == 'move_right' and can_place_tetris_piece(state['board'], row, col + 1):
        col += 1
        state['message'] = 'Moved right.'
    elif action == 'drop':
        while can_place_tetris_piece(state['board'], row + 1, col):
            row += 1
        state['piece']['row'] = row
        fix_tetris_piece(state)
        lines = clear_tetris_lines(state)
        state['score'] += lines * 100
        state['message'] = f'Dropped the block. {lines} line(s) cleared.'
        spawn_tetris_piece(state)
        save_game_state('Tetris', state)
        return state
    elif action == 'move_down':
        if can_place_tetris_piece(state['board'], row + 1, col):
            row += 1
            state['message'] = 'Moved down.'
        else:
            fix_tetris_piece(state)
            lines = clear_tetris_lines(state)
            state['score'] += lines * 100
            state['message'] = f'Block placed. {lines} line(s) cleared.'
            spawn_tetris_piece(state)
            save_game_state('Tetris', state)
            return state
    state['piece']['row'] = row
    state['piece']['col'] = col
    if can_place_tetris_piece(state['board'], row + 1, col):
        state['piece']['row'] += 1
    else:
        fix_tetris_piece(state)
        lines = clear_tetris_lines(state)
        state['score'] += lines * 100
        state['message'] = f'Block placed. {lines} line(s) cleared.'
        spawn_tetris_piece(state)
    return state


def get_piece_color(piece):
    if not piece:
        return None
    return 'white' if piece.startswith('w') else 'black'


def in_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8


def generate_chess_moves(board, row, col):
    piece = board[row][col]
    if not piece:
        return []
    color = get_piece_color(piece)
    direction = -1 if color == 'white' else 1
    moves = []
    kind = piece[1]
    opponent = 'black' if color == 'white' else 'white'
    def is_empty(r, c):
        return in_bounds(r, c) and board[r][c] is None
    def is_opponent(r, c):
        return in_bounds(r, c) and board[r][c] and get_piece_color(board[r][c]) == opponent
    if kind == 'p':
        forward = row + direction
        if is_empty(forward, col):
            moves.append((forward, col))
        for dc in (-1, 1):
            if is_opponent(forward, col + dc):
                moves.append((forward, col + dc))
    if kind == 'n':
        for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            if in_bounds(row + dr, col + dc) and not get_piece_color(board[row + dr][col + dc]) == color:
                moves.append((row + dr, col + dc))
    if kind in ('r', 'q'):
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            r, c = row + dr, col + dc
            while in_bounds(r, c):
                if board[r][c] is None:
                    moves.append((r, c))
                elif get_piece_color(board[r][c]) == opponent:
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
    if kind in ('b', 'q'):
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            r, c = row + dr, col + dc
            while in_bounds(r, c):
                if board[r][c] is None:
                    moves.append((r, c))
                elif get_piece_color(board[r][c]) == opponent:
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
    if kind == 'k':
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if in_bounds(row + dr, col + dc) and not get_piece_color(board[row + dr][col + dc]) == color:
                    moves.append((row + dr, col + dc))
    return moves


def parse_chess_square(square):
    if len(square) != 2:
        return None
    col = ord(square[0].lower()) - ord('a')
    row = 8 - int(square[1]) if square[1].isdigit() else None
    if row is None or not in_bounds(row, col):
        return None
    return row, col


def apply_chess_move(board, from_row, from_col, to_row, to_col):
    board[to_row][to_col] = board[from_row][from_col]
    board[from_row][from_col] = None


def get_all_color_moves(board, color):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] and get_piece_color(board[r][c]) == color:
                for dr, dc in generate_chess_moves(board, r, c):
                    moves.append(((r, c), (dr, dc)))
    return moves


def process_chess_action(state, action, from_square=None, to_square=None):
    if action == 'restart':
        return initialize_game_state('Chess Online')
    if state['status'] != 'playing':
        return state
    if not from_square or not to_square:
        state['message'] = 'Choose a from and to square.'
        return state
    start = parse_chess_square(from_square)
    end = parse_chess_square(to_square)
    if not start or not end:
        state['message'] = 'Invalid square coordinates.'
        return state
    from_row, from_col = start
    to_row, to_col = end
    piece = state['board'][from_row][from_col]
    if not piece or get_piece_color(piece) != 'white':
        state['message'] = 'Select a white piece.'
        return state
    valid = generate_chess_moves(state['board'], from_row, from_col)
    if (to_row, to_col) not in valid:
        state['message'] = 'That move is not legal.'
        return state
    if state['board'][to_row][to_col] == 'bk':
        state['message'] = 'You captured the black king and won!'
        apply_chess_move(state['board'], from_row, from_col, to_row, to_col)
        state['status'] = 'won'
        return state
    apply_chess_move(state['board'], from_row, from_col, to_row, to_col)
    black_moves = get_all_color_moves(state['board'], 'black')
    if not black_moves:
        state['status'] = 'won'
        state['message'] = 'Black has no moves. You win!'
        return state
    (b_from, b_to) = random.choice(black_moves)
    if state['board'][b_to[0]][b_to[1]] == 'wk':
        state['status'] = 'lost'
        state['message'] = 'Black captured your king! You lose.'
        apply_chess_move(state['board'], b_from[0], b_from[1], b_to[0], b_to[1])
        return state
    apply_chess_move(state['board'], b_from[0], b_from[1], b_to[0], b_to[1])
    state['message'] = f'Black moved from {chr(b_from[1] + 97)}{8 - b_from[0]} to {chr(b_to[1] + 97)}{8 - b_to[0]}.'
    return state


def process_dragon_quest_action(state, action):
    if action == 'restart':
        return initialize_game_state('Dragon Quest')
    if state['status'] != 'playing':
        return state
    if action == 'search_forest':
        if 'Healing Potion' not in state['inventory'] and random.random() < 0.7:
            state['inventory'].append('Healing Potion')
            state['message'] = 'You found a Healing Potion in the forest!'
        else:
            state['message'] = 'You explored the forest but found nothing this time.'
        state['location'] = 'forest'
        return state
    if action == 'visit_tavern':
        state['location'] = 'tavern'
        state['message'] = 'You rest at the tavern and hear rumors of the dragon.'
        return state
    if action == 'go_mountain':
        state['location'] = 'mountain'
        state['message'] = 'You climb the mountain and see the dragon in the distance.'
        return state
    if action == 'fight_dragon':
        if state['location'] != 'mountain':
            state['message'] = 'You must first reach the mountain before facing the dragon.'
            return state
        player_hit = random.randint(4, 8)
        dragon_hit = random.randint(3, 7)
        state['dragon_hp'] -= player_hit
        if state['dragon_hp'] <= 0:
            state['status'] = 'won'
            state['message'] = f'You strike the dragon for {player_hit} damage and slay it!'
            return state
        state['hp'] -= dragon_hit
        if state['hp'] <= 0:
            state['status'] = 'lost'
            state['message'] = f'The dragon hits you for {dragon_hit} damage. You have fallen.'
            return state
        state['message'] = f'You hit the dragon for {player_hit}, then it strikes you for {dragon_hit}.'
        return state
    if action == 'heal':
        if 'Healing Potion' not in state['inventory']:
            state['message'] = 'You have no potion to heal.'
            return state
        state['inventory'].remove('Healing Potion')
        state['hp'] = min(state['hp'] + 10, 20)
        state['message'] = 'You drink a potion and recover strength.'
        return state
    if action == 'return_village':
        state['location'] = 'village'
        state['message'] = 'You return to the village and prepare for your journey.'
        return state
    state['message'] = 'Choose your next action carefully.'
    return state

@app.route('/play/<path:gamename>', methods=['GET', 'POST'])
@login_required
def play_game(gamename):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM games WHERE name = ?", (gamename,))
    game = cursor.fetchone()
    db.close()

    if not game:
        flash('Game not found.', 'danger')
        return redirect(url_for('index'))

    state = get_game_state(game['name']) or initialize_game_state(game['name'])
    action = request.form.get('action')

    if request.method == 'POST':
        if state['type'] == 'space_invaders':
            state = process_space_invaders_action(state, action)
        elif state['type'] == 'tetris':
            state = process_tetris_action(state, action)
        elif state['type'] == 'chess_online':
            state = process_chess_action(state, action, request.form.get('from_square'), request.form.get('to_square'))
        elif state['type'] == 'dragon_quest':
            state = process_dragon_quest_action(state, action)
        save_game_state(game['name'], state)

    if state['type'] == 'space_invaders':
        state['board_display'] = render_space_invaders_board(state)
    elif state['type'] == 'tetris':
        state['board_display'] = render_tetris_board(state)
    elif state['type'] == 'chess_online':
        state['board_display'] = render_chess_board(state)
    elif state['type'] == 'dragon_quest':
        state['board_display'] = render_dragon_quest_board(state)

    return render_template('game.html', game=game, play_mode=True, game_state=state)

# Routes
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM games LIMIT 8")
    games = cursor.fetchall()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    return render_template('index.html', games=games, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        db = get_db()
        try:
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            db.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/<gamename>')
def game(gamename):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM games WHERE name = ?", (gamename,))
    game = cursor.fetchone()
    db.close()
    
    if not game:
        flash('Game not found.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('game.html', game=game)

@app.route('/category/<categoryname>')
def category(categoryname):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM categories WHERE name = ?", (categoryname,))
    cat = cursor.fetchone()
    
    if not cat:
        flash('Category not found.', 'danger')
        db.close()
        return redirect(url_for('index'))
    
    cursor.execute("SELECT * FROM games WHERE category_id = ?", (cat['id'],))
    games = cursor.fetchall()
    db.close()
    
    return render_template('category.html', category=cat, games=games)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    games = []
    
    if query:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM games WHERE name LIKE ?", (f'%{query}%',))
        games = cursor.fetchall()
        db.close()
    
    return render_template('search.html', query=query, games=games)

@app.route('/user/<username>')
def user_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        flash('User not found.', 'danger')
        db.close()
        return redirect(url_for('index'))
    
    cursor.execute("""
        SELECT games.name, games.id, user_scores.score 
        FROM user_scores 
        JOIN games ON user_scores.game_id = games.id 
        WHERE user_scores.user_id = ?
        ORDER BY user_scores.score DESC
    """, (user['id'],))
    scores = cursor.fetchall()
    db.close()
    
    return render_template('profile.html', user=user, scores=scores)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
