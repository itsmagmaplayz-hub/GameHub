import random


COLORS = ['Red', 'Yellow', 'Green', 'Blue']
NUMBERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
ACTION_CARDS = ['Skip', 'Reverse', 'Draw Two']
WILD_CARDS = ['Wild', 'Wild Draw Four']


def create_deck():
    deck = []
    for color in COLORS:
        for number in NUMBERS:
            deck.append({'color': color, 'value': number, 'type': 'number'})
            if number != '0':
                deck.append({'color': color, 'value': number, 'type': 'number'})
        for action in ACTION_CARDS:
            for _ in range(2):
                deck.append({'color': color, 'value': action, 'type': 'action'})
    for _ in range(4):
        deck.append({'color': None, 'value': 'Wild', 'type': 'wild'})
        deck.append({'color': None, 'value': 'Wild Draw Four', 'type': 'wild'})
    random.shuffle(deck)
    return deck


def can_play_card(card, discard_pile_top):
    if card['type'] == 'wild':
        return True
    if card['color'] == discard_pile_top['color']:
        return True
    if card['value'] == discard_pile_top['value']:
        return True
    return False


def draw_cards(deck, discard_pile, num_cards):
    cards = []
    for _ in range(num_cards):
        if not deck:
            discard_pile_copy = discard_pile[:-1]
            random.shuffle(discard_pile_copy)
            deck.extend(discard_pile_copy)
            discard_pile.clear()
            discard_pile.append(discard_pile[-1])
        if deck:
            cards.append(deck.pop())
    return cards


def initialize_state():
    deck = create_deck()
    player_hand = draw_cards(deck, [], 7)
    ai_hand = draw_cards(deck, [], 7)
    discard_pile = [deck.pop()]
    return {
        'type': 'uno',
        'deck': deck,
        'player_hand': player_hand,
        'ai_hand': ai_hand,
        'discard_pile': discard_pile,
        'current_player': 'player',
        'current_color': None,
        'status': 'playing',
        'message': 'Your turn! Play a card or draw.',
        'score': 0,
        'ai_score': 0,
    }


def render_board(state):
    display = []
    discard_top = state['discard_pile'][-1] if state['discard_pile'] else None
    
    color = discard_top.get('color') or state.get('current_color', 'Black')
    value = discard_top.get('value', '?')
    
    display.append([f"Discard: {color} {value}"])
    display.append([f"AI Hand: {len(state['ai_hand'])} cards"])
    display.append([f"Deck: {len(state['deck'])} cards"])
    
    hand_display = []
    for idx, card in enumerate(state['player_hand']):
        color = card.get('color') or 'Wild'
        value = card.get('value', '?')
        hand_display.append(f"{idx}: {color} {value}")
    
    display.append(hand_display if hand_display else ["No cards in hand"])
    
    return display


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
    
    if state['status'] != 'playing' or state['current_player'] != 'player':
        return state
    
    if action == 'draw':
        cards = draw_cards(state['deck'], state['discard_pile'], 1)
        state['player_hand'].extend(cards)
        state['current_player'] = 'ai'
        state['message'] = f"Drew 1 card. AI's turn."
        return play_ai_turn(state)
    
    if action and action.startswith('play_'):
        try:
            card_idx = int(action.split('_')[1])
            if card_idx < 0 or card_idx >= len(state['player_hand']):
                state['message'] = 'Invalid card index.'
                return state
            
            card = state['player_hand'][card_idx]
            discard_top = state['discard_pile'][-1]
            
            if not can_play_card(card, discard_top):
                state['message'] = 'Cannot play that card.'
                return state
            
            state['player_hand'].pop(card_idx)
            state['discard_pile'].append(card)
            
            if len(state['player_hand']) == 0:
                state['status'] = 'won'
                state['message'] = 'You won!'
                state['score'] += 50
                return state
            
            if card['type'] == 'wild':
                state['current_color'] = None
                state['message'] = f"Played Wild. Choose a color. (Press play to continue)"
            elif card['type'] == 'action':
                if card['value'] == 'Skip':
                    state['message'] = 'Played Skip. AI skipped.'
                elif card['value'] == 'Reverse':
                    state['message'] = 'Played Reverse. Your turn again.'
                elif card['value'] == 'Draw Two':
                    ai_cards = draw_cards(state['deck'], state['discard_pile'], 2)
                    state['ai_hand'].extend(ai_cards)
                    state['message'] = 'Played Draw Two. AI draws 2 cards.'
            else:
                state['message'] = f"Played {card['color']} {card['value']}."
            
            state['current_player'] = 'ai'
            return play_ai_turn(state)
        except (ValueError, IndexError):
            state['message'] = 'Invalid action.'
            return state
    
    return state


def play_ai_turn(state):
    playable_cards = []
    discard_top = state['discard_pile'][-1]
    
    for idx, card in enumerate(state['ai_hand']):
        if can_play_card(card, discard_top):
            playable_cards.append((idx, card))
    
    if not playable_cards:
        cards = draw_cards(state['deck'], state['discard_pile'], 1)
        state['ai_hand'].extend(cards)
        state['current_player'] = 'player'
        state['message'] = 'AI drew a card. Your turn.'
        return state
    
    card_idx, card = random.choice(playable_cards)
    state['ai_hand'].pop(card_idx)
    state['discard_pile'].append(card)
    
    if len(state['ai_hand']) == 0:
        state['status'] = 'lost'
        state['message'] = 'AI won!'
        state['ai_score'] += 50
        return state
    
    state['current_player'] = 'player'
    if card['type'] == 'action':
        if card['value'] == 'Draw Two':
            player_cards = draw_cards(state['deck'], state['discard_pile'], 2)
            state['player_hand'].extend(player_cards)
            state['message'] = f"AI played Draw Two. You drew 2 cards. Your turn."
        elif card['value'] == 'Skip':
            state['message'] = f"AI played Skip. Your turn skipped. AI's turn again."
            state['current_player'] = 'ai'
            return play_ai_turn(state)
        else:
            state['message'] = f"AI played {card['value']}. Your turn."
    else:
        state['message'] = f"AI played {card['color']} {card['value']}. Your turn."
    
    return state
