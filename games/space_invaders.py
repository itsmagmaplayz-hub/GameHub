import random


def initialize_state():
    return {
        'type': 'space_invaders',
        'width': 5,
        'height': 5,
        'aliens': [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        'ship_col': 2,
        'bullet': None,
        'score': 0,
        'status': 'playing',
        'message': 'Aim and fire to defend your ship!',
    }


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


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
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


def render_board(state):
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
