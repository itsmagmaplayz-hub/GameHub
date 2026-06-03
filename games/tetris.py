import random

TETROMINOES = {
    'I': [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    'O': [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    'T': [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    'L': [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
    'J': [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 0)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
    ],
    'S': [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
    ],
    'Z': [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 2), (1, 1), (1, 2), (2, 1)],
    ],
}

SHAPE_COLORS = {
    'I': '🟦',
    'O': '🟩',
    'T': '🟨',
    'L': '🟧',
    'J': '🟪',
    'S': '🟫',
    'Z': '🟥',
}

BOARD_ROWS = 20
BOARD_COLS = 10


def initialize_state():
    next_piece = random.choice(list(TETROMINOES.keys()))
    return {
        'type': 'tetris',
        'rows': BOARD_ROWS,
        'cols': BOARD_COLS,
        'board': [[0] * BOARD_COLS for _ in range(BOARD_ROWS)],
        'piece': {
            'shape': next_piece,
            'rotation': 0,
            'row': 0,
            'col': BOARD_COLS // 2 - 2,
        },
        'next_piece': random.choice(list(TETROMINOES.keys())),
        'score': 0,
        'status': 'playing',
        'message': 'Use the controls to move, rotate, and drop blocks.',
    }


def get_shape_cells(piece):
    shape = piece['shape']
    rotation = piece['rotation'] % len(TETROMINOES[shape])
    return TETROMINOES[shape][rotation]


def can_place_piece(board, piece, row, col):
    for dr, dc in get_shape_cells(piece):
        r, c = row + dr, col + dc
        if r < 0 or r >= len(board) or c < 0 or c >= len(board[0]) or board[r][c] != 0:
            return False
    return True


def fix_piece(state):
    for dr, dc in get_shape_cells(state['piece']):
        r = state['piece']['row'] + dr
        c = state['piece']['col'] + dc
        if 0 <= r < state['rows'] and 0 <= c < state['cols']:
            state['board'][r][c] = SHAPE_COLORS[state['piece']['shape']]


def clear_lines(state):
    full_rows = [row for row in state['board'] if all(cell != 0 for cell in row)]
    if not full_rows:
        return 0
    new_board = [[0] * state['cols'] for _ in full_rows]
    for row in state['board']:
        if any(cell == 0 for cell in row):
            new_board.append(row)
    state['board'] = new_board
    return len(full_rows)


def spawn_piece(state):
    state['piece'] = {
        'shape': state['next_piece'],
        'rotation': 0,
        'row': 0,
        'col': BOARD_COLS // 2 - 2,
    }
    state['next_piece'] = random.choice(list(TETROMINOES.keys()))
    if not can_place_piece(state['board'], state['piece'], state['piece']['row'], state['piece']['col']):
        state['status'] = 'lost'
        state['message'] = 'Game over! The pieces have piled too high.'


def rotate_piece(piece):
    piece['rotation'] = (piece['rotation'] + 1) % len(TETROMINOES[piece['shape']])


def move_piece(state, row_delta, col_delta):
    row = state['piece']['row'] + row_delta
    col = state['piece']['col'] + col_delta
    if can_place_piece(state['board'], state['piece'], row, col):
        state['piece']['row'] = row
        state['piece']['col'] = col
        return True
    return False


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
    if state['status'] != 'playing':
        return state

    if action == 'move_left':
        if move_piece(state, 0, -1):
            state['message'] = 'Moved left.'
        else:
            state['message'] = 'Can\'t move left.'
    elif action == 'move_right':
        if move_piece(state, 0, 1):
            state['message'] = 'Moved right.'
        else:
            state['message'] = 'Can\'t move right.'
    elif action == 'move_down':
        if move_piece(state, 1, 0):
            state['message'] = 'Moved down.'
            return state
        fix_piece(state)
        lines = clear_lines(state)
        state['score'] += lines * 100
        state['message'] = f'Block placed. {lines} line(s) cleared.'
        spawn_piece(state)
        return state
    elif action == 'rotate':
        original_rotation = state['piece']['rotation']
        rotate_piece(state['piece'])
        if can_place_piece(state['board'], state['piece'], state['piece']['row'], state['piece']['col']):
            state['message'] = 'Rotated piece.'
        else:
            state['piece']['rotation'] = original_rotation
            state['message'] = 'Cannot rotate here.'
    elif action == 'drop':
        while move_piece(state, 1, 0):
            pass
        fix_piece(state)
        lines = clear_lines(state)
        state['score'] += lines * 100
        state['message'] = f'Dropped block. {lines} line(s) cleared.'
        spawn_piece(state)
        return state

    if can_place_piece(state['board'], state['piece'], state['piece']['row'] + 1, state['piece']['col']):
        state['piece']['row'] += 1
    else:
        fix_piece(state)
        lines = clear_lines(state)
        state['score'] += lines * 100
        state['message'] = f'Block placed. {lines} line(s) cleared.'
        spawn_piece(state)
    return state


def render_board(state):
    board = [row.copy() for row in state['board']]
    for dr, dc in get_shape_cells(state['piece']):
        r = state['piece']['row'] + dr
        c = state['piece']['col'] + dc
        if 0 <= r < state['rows'] and 0 <= c < state['cols']:
            board[r][c] = '🟦'
    display_board = []
    for row in board:
        display_row = []
        for cell in row:
            display_row.append(cell if cell != 0 else '·')
        display_board.append(display_row)
    return display_board
