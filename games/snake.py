import random


def initialize_state():
    rows, cols = 10, 12
    snake = [(rows // 2, cols // 2), (rows // 2, cols // 2 - 1)]
    apple = None
    while apple is None or apple in snake:
        apple = (random.randint(0, rows - 1), random.randint(0, cols - 1))
    return {
        'type': 'snake',
        'rows': rows,
        'cols': cols,
        'snake': snake,
        'direction': 'right',
        'apple': apple,
        'status': 'playing',
        'message': 'Use the controls to move the snake.',
        'score': 0,
    }


def render_board(state):
    rows, cols = state['rows'], state['cols']
    board = [['·'] * cols for _ in range(rows)]
    for r, c in state['snake']:
        board[r][c] = '◼'
    ar, ac = state['apple']
    board[ar][ac] = '●'
    return board


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
    if state['status'] != 'playing':
        return state
    dir_map = {
        'up': (-1, 0),
        'down': (1, 0),
        'left': (0, -1),
        'right': (0, 1),
    }
    if action and action.startswith('move_'):
        new_dir = action.split('_')[1]
        if new_dir in dir_map:
            state['direction'] = new_dir
    dr, dc = dir_map[state['direction']]
    head = state['snake'][0]
    new_head = (head[0] + dr, head[1] + dc)
    rows, cols = state['rows'], state['cols']
    if not (0 <= new_head[0] < rows and 0 <= new_head[1] < cols) or new_head in state['snake']:
        state['status'] = 'lost'
        state['message'] = 'You crashed! Game over.'
        return state
    state['snake'].insert(0, new_head)
    if new_head == state['apple']:
        state['score'] += 5
        apple = None
        while apple is None or apple in state['snake']:
            apple = (random.randint(0, rows - 1), random.randint(0, cols - 1))
        state['apple'] = apple
        state['message'] = 'Yum!'
    else:
        state['snake'].pop()
    return state
