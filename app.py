from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import os
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from games import GAME_MODULES

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
                email TEXT UNIQUE NOT NULL,
                xp INTEGER DEFAULT 0
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
        try:
            db.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
            db.commit()
        except sqlite3.OperationalError:
            pass
        try:
            db.execute("ALTER TABLE user_scores ADD COLUMN result TEXT")
            db.commit()
        except sqlite3.OperationalError:
            pass
        try:
            db.execute("ALTER TABLE user_scores ADD COLUMN elo INTEGER")
            db.commit()
        except sqlite3.OperationalError:
            pass
        
        # Add sample data if empty
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            categories = [
                ('Action', 'Fast-paced games'),
                ('Puzzle', 'Brain-teasing challenges'),
                ('Adventure', 'Exploration and story'),
                ('Strategy', 'Tactical gameplay'),
                ('Card Games', 'Classic card games'),
            ]
            db.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)
            
            games = [
                ('Space Invaders', 'Classic arcade shooter', 1, 'https://via.placeholder.com/300x200?text=Space+Invaders'),
                ('Tetris', 'Stack the falling blocks', 2, 'https://via.placeholder.com/300x200?text=Tetris'),
                ('Chess Online', 'Strategic board game', 4, 'https://via.placeholder.com/300x200?text=Chess'),
                ('Dragon Quest', 'Epic adventure awaits', 3, 'https://via.placeholder.com/300x200?text=Dragon+Quest'),
                ('Tic-Tac-Toe', 'Classic 3x3 strategy', 2, 'https://via.placeholder.com/300x200?text=Tic+Tac+Toe'),
                ('Memory Match', 'Flip and match cards', 2, 'https://via.placeholder.com/300x200?text=Memory+Match'),
                ('Snake', 'Grow the snake by eating apples', 1, 'https://via.placeholder.com/300x200?text=Snake'),
                ('UNO', 'Match colors and numbers', 5, 'https://via.placeholder.com/300x200?text=UNO'),
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

TYPE_MODULES = {
    'space_invaders': GAME_MODULES['Space Invaders'],
    'tetris': GAME_MODULES['Tetris'],
    'chess_online': GAME_MODULES['Chess Online'],
    'dragon_quest': GAME_MODULES['Dragon Quest'],
    'tic_tac_toe': GAME_MODULES['Tic-Tac-Toe'],
    'memory': GAME_MODULES['Memory Match'],
    'snake': GAME_MODULES['Snake'],
    'uno': GAME_MODULES['UNO'],
}


def initialize_game_state(game_name):
    module = GAME_MODULES.get(game_name)
    return module.initialize_state() if module else {
        'type': 'unknown',
        'status': 'ended',
        'message': 'This game is not yet playable.',
    }


def get_game_module(game_name):
    return GAME_MODULES.get(game_name)


def get_module_for_state(state):
    return TYPE_MODULES.get(state.get('type'))


def award_user_xp(user_id, xp):
    if xp <= 0:
        return
    db = get_db()
    db.execute("UPDATE users SET xp = COALESCE(xp, 0) + ? WHERE id = ?", (xp, user_id))
    db.commit()
    db.close()


def compute_new_elo(user_id, game_id, result):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT MAX(elo) AS current_elo FROM user_scores WHERE user_id = ? AND game_id = ? AND elo IS NOT NULL",
        (user_id, game_id)
    )
    row = cursor.fetchone()
    db.close()
    current_elo = row['current_elo'] if row and row['current_elo'] is not None else 1200
    opponent_elo = 1200
    expected = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))
    k = 20
    score_value = {'won': 1.0, 'draw': 0.5, 'lost': 0.0}.get(result, 0.5)
    new_elo = int(current_elo + k * (score_value - expected))
    return max(100, new_elo)


def record_game_score(user_id, game_id, state):
    if state.get('status') not in ('won', 'lost', 'draw') or state.get('_score_recorded'):
        return state

    if state.get('score') is None and state.get('result') is None:
        state['result'] = state['status']

    score_value = state.get('score')
    result_value = state.get('result')
    elo_value = None
    if result_value:
        elo_value = compute_new_elo(user_id, game_id, result_value)

    if score_value is None and result_value is None:
        return state

    db = get_db()
    db.execute(
        "INSERT INTO user_scores (user_id, game_id, score, result, elo) VALUES (?, ?, ?, ?, ?)",
        (user_id, game_id, score_value, result_value, elo_value)
    )
    db.commit()
    db.close()
    state['_score_recorded'] = True
    return state


def process_game_action(game, state, action, form):
    game_module = get_game_module(game['name'])
    if not game_module:
        return state
    if game['name'] == 'Chess Online':
        return game_module.process_action(state, action, form.get('from_square'), form.get('to_square'))
    return game_module.process_action(state, action)

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
        state = process_game_action(game, state, action, request.form)
        if action == 'restart':
            state.pop('_score_recorded', None)
            state.pop('_final_xp_awarded', None)
        else:
            xp_gain = 0
            if state.get('status') == 'playing' and action:
                xp_gain += 1
            if state.get('status') == 'won' and not state.get('_final_xp_awarded'):
                xp_gain += 10
                state['_final_xp_awarded'] = True
            elif state.get('status') == 'lost' and not state.get('_final_xp_awarded'):
                xp_gain += 5
                state['_final_xp_awarded'] = True
            elif state.get('status') == 'draw' and not state.get('_final_xp_awarded'):
                xp_gain += 3
                state['_final_xp_awarded'] = True
            if xp_gain > 0:
                award_user_xp(session['user_id'], xp_gain)
            state = record_game_score(session['user_id'], game['id'], state)
        save_game_state(game['name'], state)

    game_module = get_game_module(game['name'])
    if game_module:
        state['board_display'] = game_module.render_board(state)

    return render_template('game.html', game=game, play_mode=True, game_state=state)


@app.route('/play/<path:gamename>/action', methods=['POST'])
@login_required
def play_game_action(gamename):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM games WHERE name = ?", (gamename,))
    game = cursor.fetchone()
    db.close()

    if not game:
        return jsonify({'success': False, 'message': 'Game not found.'}), 404

    state = get_game_state(game['name']) or initialize_game_state(game['name'])
    action = request.form.get('action')
    state = process_game_action(game, state, action, request.form)
    if action == 'restart':
        state.pop('_score_recorded', None)
        state.pop('_final_xp_awarded', None)
    else:
        xp_gain = 0
        if state.get('status') == 'playing' and action:
            xp_gain += 1
        if state.get('status') == 'won' and not state.get('_final_xp_awarded'):
            xp_gain += 10
            state['_final_xp_awarded'] = True
        elif state.get('status') == 'lost' and not state.get('_final_xp_awarded'):
            xp_gain += 5
            state['_final_xp_awarded'] = True
        elif state.get('status') == 'draw' and not state.get('_final_xp_awarded'):
            xp_gain += 3
            state['_final_xp_awarded'] = True
        if xp_gain > 0:
            award_user_xp(session['user_id'], xp_gain)
        state = record_game_score(session['user_id'], game['id'], state)
    save_game_state(game['name'], state)

    game_module = get_game_module(game['name'])
    board_display = game_module.render_board(state) if game_module else []

    return jsonify({
        'success': True,
        'message': state.get('message'),
        'status': state.get('status'),
        'score': state.get('score'),
        'type': state.get('type'),
        'board_display': board_display,
        'next_piece': state.get('next_piece'),
    })


# Routes
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT g.*, COUNT(us.id) AS play_count FROM games g "
        "LEFT JOIN user_scores us ON g.id = us.game_id "
        "GROUP BY g.id ORDER BY play_count DESC, g.id ASC LIMIT 4"
    )
    top_games = cursor.fetchall()
    cursor.execute("SELECT * FROM games ORDER BY id DESC LIMIT 4")
    new_games = cursor.fetchall()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    return render_template('index.html', top_games=top_games, new_games=new_games, categories=categories)

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
    
    cursor.execute("SELECT * FROM games WHERE category_id = ? ORDER BY id DESC", (cat['id'],))
    games = cursor.fetchall()
    cursor.execute("SELECT * FROM games WHERE category_id = ? ORDER BY id DESC LIMIT 4", (cat['id'],))
    new_games = cursor.fetchall()
    db.close()
    
    return render_template('category.html', category=cat, games=games, new_games=new_games)

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

@app.route('/rank/<path:gamename>')
def rank_game(gamename):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM games WHERE name = ?", (gamename,))
    game = cursor.fetchone()

    if not game:
        flash('Game not found.', 'danger')
        db.close()
        return redirect(url_for('index'))

    cursor.execute(
        "SELECT COUNT(*) AS result_count FROM user_scores WHERE game_id = ? AND result IS NOT NULL",
        (game['id'],)
    )
    has_results = cursor.fetchone()['result_count'] > 0

    if has_results:
        cursor.execute("""
            SELECT users.username,
                   SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS wins,
                   SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) AS draws,
                   SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS losses,
                   MAX(elo) AS elo
            FROM user_scores
            JOIN users ON user_scores.user_id = users.id
            WHERE user_scores.game_id = ? AND user_scores.result IS NOT NULL
            GROUP BY users.id
            ORDER BY wins DESC, elo DESC, draws DESC
            LIMIT 20
        """, (game['id'],))
        rankings = cursor.fetchall()
        rank_type = 'wins_elo'
    else:
        cursor.execute("""
            SELECT users.username, MAX(user_scores.score) AS best_score
            FROM user_scores
            JOIN users ON user_scores.user_id = users.id
            WHERE user_scores.game_id = ?
            GROUP BY users.id
            ORDER BY best_score DESC
            LIMIT 20
        """, (game['id'],))
        rankings = cursor.fetchall()
        rank_type = 'score'

    db.close()
    return render_template('rank.html', game=game, rankings=rankings, rank_type=rank_type)

@app.route('/rankxp')
def rank_xp():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username, xp FROM users ORDER BY xp DESC, username ASC")
    rankings = cursor.fetchall()
    db.close()
    return render_template('rankxp.html', rankings=rankings)

@app.route('/user/<username>')
def user_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, email, COALESCE(xp, 0) AS xp FROM users WHERE username = ?", (username,))
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
