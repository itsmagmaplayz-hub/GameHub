import random


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


def initialize_state():
    return {
        'type': 'chess_online',
        'board': initialize_chess_board(),
        'turn': 'white',
        'status': 'playing',
        'message': 'White to move. Click a piece, then a destination square.',
    }


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


def process_action(state, action, from_square=None, to_square=None):
    if action == 'restart':
        return initialize_state()
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


def render_board(state):
    icons = {
        'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
        'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟︎',
    }
    board = []
    for row in state['board']:
        display_row = [icons.get(cell, '·') for cell in row]
        board.append(display_row)
    return board
