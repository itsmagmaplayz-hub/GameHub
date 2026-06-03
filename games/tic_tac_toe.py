import random


def initialize_state():
    return {
        'type': 'tic_tac_toe',
        'board': [[None] * 3 for _ in range(3)],
        'turn': 'X',
        'status': 'playing',
        'message': 'Make your move. You are X.',
        'score': 0,
    }


def render_board(state):
    display = []
    for row in state['board']:
        display.append([cell if cell else '·' for cell in row])
    return display


def check_tictactoe_winner(board):
    lines = []
    lines.extend(board)
    lines.extend([[board[r][c] for r in range(3)] for c in range(3)])
    lines.append([board[i][i] for i in range(3)])
    lines.append([board[i][2 - i] for i in range(3)])
    for line in lines:
        if line[0] and line.count(line[0]) == 3:
            return line[0]
    if all(cell for row in board for cell in row):
        return 'Draw'
    return None


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
    if state['status'] != 'playing':
        return state
    if action and action.startswith('move_'):
        _, r, c = action.split('_')
        r, c = int(r), int(c)
        if state['board'][r][c] is not None:
            state['message'] = 'Cell already taken.'
            return state
        state['board'][r][c] = state['turn']
        winner = check_tictactoe_winner(state['board'])
        if winner:
            if winner == 'Draw':
                state['status'] = 'draw'
                state['message'] = 'The game is a draw.'
            else:
                state['status'] = 'won'
                state['message'] = f'{winner} wins!'
                if winner == 'X':
                    state['score'] += 1
            return state
        state['turn'] = 'O' if state['turn'] == 'X' else 'X'
        if state['turn'] == 'O':
            empties = [(i, j) for i in range(3) for j in range(3) if state['board'][i][j] is None]
            if empties:
                move = random.choice(empties)
                state['board'][move[0]][move[1]] = 'O'
            winner = check_tictactoe_winner(state['board'])
            if winner:
                if winner == 'Draw':
                    state['status'] = 'draw'
                    state['message'] = 'The game is a draw.'
                else:
                    state['status'] = 'lost' if winner == 'O' else 'won'
                    state['message'] = f'{winner} wins!'
                return state
            state['turn'] = 'X'
            state['message'] = 'Your turn.'
    return state
