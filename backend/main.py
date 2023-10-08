from fastapi import FastAPI, HTTPException, APIRouter, Request
from players import Player
from code_game import Game

from pydantic import BaseModel

import json
import os

app = FastAPI()
# app = APIRouter()

class ComplexNumber(BaseModel):
    real: float
    imag: float

def get_game(game_id:int)-> Game:
    try:
        game = Game.get_all_games()[int(game_id)]
        return game
    except IndexError as e:
        raise HTTPException(status_code=404, detail="Game instance not found")

@app.post("/create_game/", status_code= 201)
async def create_game(_json:dict[str, str|list[str|int]|int])-> dict[str, int|dict|str|list]:
# def create_game(_json:dict)-> dict:
    response = {}

    players = _json["players"]
    initial_state = _json["initial_state"]
    decks = _json["decks"]


    # create game
    if initial_state is not None:
        for i in range(len(initial_state)):
            if isinstance(initial_state[i], ComplexNumber):
                initial_state[i] = complex(initial_state[i].real, initial_state[i].imag)
    else:
        initial_state = [1,0,0,0]

    game = Game(initial_state= initial_state, decks= decks)
    game_id = game.game_id

    # create players
    for player in players:
        Player(name= player+'_'+str(game_id))

    # player names to Player objects

    players = [game.player_ids_to_object(player+'_'+str(game_id)) for player in players]

    # distribute cards
    game.distribute_cards(players= [player.name for player in players], decks= game.num_decks)

    # set target states
    game.set_target_states()

    response['game_id']= game.game_id
    
    details={}
    for player in players:
        details[player.name.split("_")[0]] = {}
        details[player.name.split("_")[0]]['game_id'] = player.game_id
        details[player.name.split("_")[0]]['cards'] = player.cards
        details[player.name.split("_")[0]]['target_state'] = [str(i) for i in player.target_state]
        details[player.name.split("_")[0]]['fidelities'] = game.fidelity(player.target_state, game.game_state).real
        details[player.name.split("_")[0]]['bloch_sphere'] = send_bloch_sphere({"game_id": player.game_id,
                                                       "statevector": player.target_state,
                                                       "player": player.name.split("_")[0]})
        details[player.name.split("_")[0]]['q_sphere'] = send_q_sphere({"game_id": player.game_id,
                                                       "statevector": player.target_state,
                                                       "player": player.name.split("_")[0]})

    response['data'] = details
    return response 


@app.post("/play_card/", status_code= 201)
def play_card(_json:dict[str, None|int|float|str|list[str|int|None|float]])->dict[str, int|dict|str|float|list]:
    _response = {}

    # print(_json)

    game_id = _json['game_id']
    player = _json['player']+'_'+str(game_id)
    card = _json['card']
    qubits = _json['qubits']
    angle = _json['angle']

    game = get_game(game_id= game_id)
    game_players = game.get_players()
    if player not in [i.name for i in game.winning_players] and player not in [i.name for i in game.ejected_players]:
        try:
            measurement, game_state, new_card, _fidelities = game.drop_card(players= game_players, player= player, card= card, qubits= qubits, angle= angle)
        except Exception as e:
            return {"error":str(e)}
    else:
        return {"error": "Player not a part of the game"}
    
    fidelities={}
    for key in _fidelities.keys():
        fidelities[key.split('_')[0]] = _fidelities[key]

    _response[player.split('_')[0]] = {
                                        "measurement": measurement,
                                        "game_state": [str(i) for i in game_state],
                                        "new_card": new_card,
                                        "remaining_cards": len(game.remaining_cards),
                                        "fidelities" : fidelities}

    # print(game.gate_sequence)
    # print(len(game.gate_sequence))
    return _response

@app.post("/show/", status_code= 201)
def show(_json:dict[str, int|str])-> dict[str, str]:
    
    game_id = _json['game_id']
    player = _json['player']+"_"+str(game_id)

    game = get_game(game_id)        
    b = game.show(player= player)    

    if b:
        _response = {"win": "true"}
    else:
        _response = {"lose": "true"}
    
    if len([_ for _ in game.get_top_players()]) == 1:
        game.end_game()
        _response["end"] = "true"
    return _response

@app.post("/drop/", status_code= 201)    
def drop(_json:dict[str, int|str])-> dict[str, str]:
    game_id = _json['game_id']
    player = _json['player']+"_"+str(game_id)

    game = get_game(game_id)
    game.drop(player= player)
    _response = {"lose": "true"}

    if len([_ for _ in game.get_top_players()]) == 1:
        game.end_game()
        _response["end"] = "true"
    return _response

@app.post("/game_circuit/", status_code= 201)
def send_game_circuit(_json:dict[str, int|str|float|dict[str, list[str|list[int]|int|float|None]]])-> dict[str, int|str]:
    
    game_id = _json['game_id']
    gates = []
    qubits = []
    angles = []
    print(len(_json['data']))
    for _ in range(len(_json['data'])):
        try:
            gates.append(_json['data'][str(_)][0])
            qubits.append(_json['data'][str(_)][1])
            if gates[-1] in ['Rx', 'Ry', 'Rz']:
                angles.append(_json['data'][str(_)][2])
            else:
                angles.append(None)
        except KeyError as e:
            pass

    game = get_game(game_id)
    path = "circuit_"+str(game_id)+".png"
    game.save_circuit_image(gates=gates, qubits=qubits, angles=angles, path= path)
    
    print(type(game.image_to_base64(file_path= path)))
    _response =  {"circuit": game.image_to_base64(file_path= path)}
    os.remove(path= path)
    return _response

# @app.post("/bloch_sphere/", status_code= 201)    
def send_bloch_sphere(_json:dict[str, int|str])-> dict[str, str]:
    game_id = _json['game_id']
    statevetor = _json['statevector']
    player  = _json['player']

    for i in range(len(statevetor)):
        statevetor[i] = complex(statevetor[i])

    print(statevetor)
    game = get_game(game_id)
    path = 'blochsphere_'+player+'_'+str(game_id)+'.png'
    game.save_bloch_sphere(state_vector= statevetor, path= path, reverse=True)

    _response =  {"circuit": game.image_to_base64(file_path= path)}
    os.remove(path= path)
    return _response

# @app.post("/q_sphere/", status_code= 201)
def send_q_sphere(_json:dict[str, int|str])-> dict[str, str]:
    game_id = _json['game_id']
    statevetor = _json['statevector']
    player  = _json['player']

    for i in range(len(statevetor)):
        statevetor[i] = complex(statevetor[i])

    # print(statevetor)
    game = get_game(game_id)
    path = 'qsphere_'+player+'_'+str(game_id)+'.png'
    game.save_q_sphere(state_vector= statevetor, path= path, reverse=True)

    _response =  {"circuit": game.image_to_base64(file_path= path)}
    os.remove(path= path)
    return _response

@app.post("/add_deck/", status_code= 201)
def add_deck(_json:dict[str, int|str])-> dict[str, str|int]:

    game_id = _json['game_id']
    game = get_game(game_id= game_id)
    game.add_deck()

    return {'remaining_cards':len(game.remaining_cards)}


# print("--------------------------------------------------------------------------------------")
# print("----------------Create game Response------------------------")
# create_game_json_file = {
    # "players": ["Venkat", "Chandra", "Suresh"],
    # "initial_state": [1,0,0,0],
    # "decks": 3
# }

# rep = create_game(create_game_json_file)
# game_id = rep['game_id']
# print(json.dumps(rep, indent=4))

# print("---------------------add_deck-------------------")
# add_card_json_file={
#     'game_id': game_id
# }
# print(add_deck(_json= add_card_json_file))

# print("----------------play card Response------------------------")
# play_card_json_file = {
#     'game_id': game_id,
#     'player': "Chandra",
#     'card': "X",
#     'qubits': [1],
#     'angle': 0
# }


# rep = play_card(play_card_json_file)
# print(json.dumps(rep, indent=4))

# if 'error' not in rep.keys():
#     print(json.dumps(show({"player":"Chandra", "game_id":game_id}), indent=4))
#     print(json.dumps(show({"player":"Venkat", "game_id":game_id}), indent=4))

# play_card_json_file = {
#     'game_id': game_id,
#     'player': "Venkat",
#     'card': "X",
#     'qubits': [1],
#     'angle': 0
# }

# print("----------------play card Response------------------------")
# rep = play_card(play_card_json_file)
# print(json.dumps(rep, indent=4))

# print("------------------Circuit data---------------------")
# circuit_data_json_file = {
#     'game_id': game_id,
#     'data': {
#         '0': ['H', [1], 'null'],
#         '1': ['Rx', [1], 3.141592653589793],
#         '2': ['CNOT', [0,1], 'null'],
#         '3': ['X', [0], 'null'],
#         '4': ['Y', [1], 'null'],
#         '5': ['Z', [0], 'null']
#     }
# }

# # print(send_game_circuit(circuit_data_json_file))


# print("------------------Bloch sphere data---------------------")
# circuit_data_json_file = {
#     'game_id': game_id,
#     'statevector': ['(0j)', '1', '0', '0'] ,
#     'player': "Venkat"
# }

# # print(send_bloch_sphere(circuit_data_json_file))

# print("------------------q sphere data---------------------")
# circuit_data_json_file = {
#     'game_id': game_id,
#     'statevector': ['(0j)', '1', '0', '0'] ,
#     'player': "Venkat"
# }

# # print(send_q_sphere(circuit_data_json_file))