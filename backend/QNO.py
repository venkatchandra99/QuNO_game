from fastapi import FastAPI, HTTPException, APIRouter
from players import Player
from code_game import Game

from pydantic import BaseModel

app = FastAPI()
# app = APIRouter()

class ComplexNumber(BaseModel):
    real: float
    imag: float

@app.post("/add_player", status_code= 201)
async def add_player(name:str)-> dict:
    try:
        Player(name= name)
        return {'status':"Successful"}
    except Exception as e:
        return {'status':"Failed: "+str(e)}

@app.get("/all_players", status_code= 201)
async def get_all_players()-> dict:
    players_dict = {}
    players = [i.name for i in Player.get_all_players()]
    players_dict['players'] = players
    return players_dict

@app.get("/all_players/{game_id}", status_code= 201)
async def get_all_players(game_id)-> dict:
    game = get_game(game_id= game_id)
    players_dict={}
    players_dict['players'] = game.get_players()
    return players_dict

@app.get("/target_states", status_code= 201)
async def get_all_target_states()-> dict:
    ts = {}
    for i in Player.get_all_players():
        ts[i.name] = str(i.target_state)
    return ts

@app.get("/target_states/{game_id}", status_code= 201)
async def get_all_target_states(game_id)-> dict:
    game = get_game(game_id= game_id)
    ts = {}
    for i in game.get_players():
        ts[i.name] = str(i.target_state)
    return ts

@app.get("/{name}/target_state", status_code=201)
async def get_target_State(name:str)-> None|dict:
    for player in Player.get_all_players():
        if player.name == name:
            return {"target state":str(player.target_state)}
        
@app.get("/{player_name}/cards", status_code=201)
async def get_cards(player_name:str)-> dict:
    for player in Player.get_all_players():
        if player.name == player_name:
            return {"cards":player.cards}
    return {"cards": None}

@app.get("/{name}/details", status_code=201)
async def get_player(name:str)-> dict:
    details = {}
    print(Player.get_all_players())
    for player in Player.get_all_players():
        if player.name == name:
            details['name'] = name
            details['game id'] = player.game_id
            details['cards'] = player.cards
            details['target state'] = str(player.target_state)
            break
    return details

@app.post("/create_game", status_code=201)
async def create_game(initial_state:list[int|float|ComplexNumber] = [1,0,0,0], decks:int|None= None)-> dict:
    print(type(initial_state))
    for i in range(len(initial_state)):
        if isinstance(initial_state[i], ComplexNumber):
            initial_state[i] = complex(initial_state[i].real, initial_state[i].imag)

    Game(initial_state= initial_state, decks= decks)
    return {"game_id":len(Game.get_all_games())-1}

def get_game(game_id:int)-> Game:
    try:
        game = Game.get_all_games()[int(game_id)]
        return game
    except IndexError as e:
        raise HTTPException(status_code=404, detail="Game instance not found")
    
@app.get("/game_state", status_code=201)
async def get_game_state(game_id:int)-> dict:
    return {"game_state":str(get_game(game_id).game_state)}

@app.put("/set_target_states", status_code=204)
async def set_targets(game_id:int, players:list[str])-> None:
    game = get_game(game_id= game_id)
    game.set_target_states(players)
    
@app.get("/num_decks", status_code=201)
async def get_num_decks(game_id:int)-> dict:
    game = get_game(game_id= game_id)
    if game.num_decks is None:
        return {"num decks": "undefined"}
    return {"num decks":game.num_decks}

@app.put("/distribute_cards", status_code=204)
async def distribute_cards(game_id:int, players:list[str]):
    game = get_game(game_id= game_id)
    game.distribute_cards(players= players, decks=game.num_decks)
    
@app.post("/play_card", status_code=201)
async def play_card(game_id:int, player:str, card:str, qubits:list[int], angle:float = None)-> dict:
    game = get_game(game_id= game_id)
    game_players = game.get_players()
    if player not in [i.name for i in game.winning_players] and player not in [i.name for i in game.ejected_players]:
        try:
            measurement, game_state, new_card, fidelities = game.drop_card(players= game_players, player= player, card= card, qubits= qubits, angle= angle)
        except Exception as e:
            return {"Error":str(e)}
    else:
        return {"Error": "Player not a part of the game"}
    return {
        "game id": game_id,
        "player": player,
        "measurement": measurement,
        "game state": str(game_state),
        "new card": new_card,
        "fidelities" : fidelities
    }

@app.post("/{player}/show", status_code=204)
async def show(player:str, game_id:int):
    game = get_game(game_id)
    game.show(player= player)
    player.target_state = None
    player.cards = []
    player.game_id = None

@app.post("/{player}/drop", status_code=204)
async def drop(player:str, game_id:int):
    game = get_game(game_id)
    game.drop(player= player)
    player.target_state = None
    player.cards = []
    player.game_id = None




# Player("Venkat")
# Player("Chandra")
# Player("Daniel")

# g = Game(decks=3)
# g.set_target_states(players= ["Venkat", "Chandra", "Daniel"])
# g.distribute_cards()





    