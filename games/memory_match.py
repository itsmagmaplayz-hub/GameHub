import random


def initialize_state():
    pairs = list(range(8)) * 2
    random.shuffle(pairs)
    cards = [{'value': v, 'matched': False} for v in pairs]
    return {
        'type': 'memory',
        'cards': cards,
        'flipped': [],
        'matches': 0,
        'status': 'playing',
        'message': 'Flip two cards to find a match.',
        'score': 0,
    }


def render_board(state):
    display = []
    for idx, card in enumerate(state['cards']):
        if card['matched'] or idx in state['flipped']:
            display.append(str(card['value']))
        else:
            display.append('■')
    return [display[i:i+4] for i in range(0, len(display), 4)]


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
    if state['status'] != 'playing':
        return state
    if action and action.startswith('flip_'):
        idx = int(action.split('_')[1])
        if state['cards'][idx]['matched'] or idx in state['flipped']:
            state['message'] = 'Cannot flip that card.'
            return state
        state['flipped'].append(idx)
        if len(state['flipped']) == 2:
            a, b = state['flipped']
            if state['cards'][a]['value'] == state['cards'][b]['value']:
                state['cards'][a]['matched'] = True
                state['cards'][b]['matched'] = True
                state['matches'] += 1
                state['score'] += 10
                state['message'] = 'Match found!'
            else:
                state['message'] = 'Not a match.'
            state['flipped'] = []
            if state['matches'] == len(state['cards']) // 2:
                state['status'] = 'won'
                state['message'] = 'You matched all cards!'
    return state
