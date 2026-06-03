import random


def initialize_state():
    return {
        'type': 'dragon_quest',
        'location': 'village',
        'hp': 20,
        'dragon_hp': 30,
        'inventory': ['Healing Potion'],
        'status': 'playing',
        'message': 'Your quest begins in the village. Explore the world and defeat the dragon!',
    }


def render_board(state):
    inventory = ', '.join(state['inventory']) if state['inventory'] else 'Empty'
    return [
        ['Location:', state['location'].title()],
        ['HP:', str(state['hp'])],
        ['Dragon HP:', str(state['dragon_hp'])],
        ['Inventory:', inventory],
    ]


def process_action(state, action):
    if action == 'restart':
        return initialize_state()
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
