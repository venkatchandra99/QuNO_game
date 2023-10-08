import cmath
import random
import warnings
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit

from qiskit.visualization import plot_bloch_vector, plot_bloch_multivector
from qiskit.visualization.bloch import Bloch

from gates import QuantumGates
from players import Player
from utils import Operations, Constants

class Game(Operations):
    all_games=[]

    def __init__(self, initial_state:list = [1, 0, 0, 0], decks:int = None):
        if self.is_valid_statevector(initial_state):
            self.initial_state = initial_state
            self.game_state = initial_state
            self.num_qubits = int(cmath.log(len(initial_state), 2).real)
            self.num_decks = decks
            self.gate_sequence = None
            self.random_angles = []
            self.target_sequence_num = None
            self.players = None
            self.ejected_players = []
            self.winning_players = []
            self.game_started = False
            self.cards = [i.name for i in list(QuantumGates)]
            for i in ['Rx', 'Ry', 'Rz']:
                self.cards.append(i)
            if decks is not None:
                self.cards = self.cards * decks
            self.remaining_cards = []
            Game.all_games.append(self)
            self.game_id = len(Game.all_games)-1
        else:
            raise Exception("Initial state provided in not a Statevector")
        
    @classmethod
    def get_all_games(g):
        return g.all_games

    def set_target_states(self, players:list|None= None, total_qubits:int = None):
        if not self.game_started:
            raise Exception("Distribure cards for players")
        if players is None:
            players = self.get_players()
        if not isinstance(players[0], Player):
            players = self.player_ids_to_object(players= players)
        target_state = self.initial_state.copy()
        target_state = self.row_to_coloumn_vector(target_state)
        if total_qubits is None:
            total_qubits = self.num_qubits
        if self.num_decks != None:
            if self.num_decks < len(players):
                warnings.warn("Cards insufficient, add more decks")
                return
            gate_sequence = [i.name for i in list(QuantumGates)]
            for i in ['Rx', 'Ry', 'Rz']:
                gate_sequence.append(i)
            gate_sequence = gate_sequence* self.num_decks
            # for i in range(2*self.num_decks):
            #     ii = random.randrange(8)

            random.shuffle(gate_sequence)
            target_sequence_num = random.sample(list(range(len(gate_sequence))), len(players))
            target_sequence_num.sort()
            self.target_sequence_num = target_sequence_num
            self.gate_sequence = gate_sequence
            target_states = []
            for i in range(len(gate_sequence)):
                if gate_sequence[i] in ['Rx', 'Ry', 'Rz']:
                    angle = random.choice(Constants.R_angles.value)
                else:
                    angle = None
                gate = self.get_gate_matrix(gate= gate_sequence[i], angle= angle)
                self.random_angles.append(angle)
                qubit = random.sample(list(range(total_qubits)), self.num_qubits_required(gate))
                gate = self.get_total_unitary(unitary= gate, total_qubits= total_qubits, qubit_num= qubit)
                target_state = self.multiply_gates(gate1= gate, gate2= target_state)
                if i in target_sequence_num:
                    if True not in [cmath.isclose(self.fidelity(self.coloumn_to_row_vector(target_state), present_state), 1) for present_state in target_states]:
                        target_states.append(self.coloumn_to_row_vector(target_state))
                        random.shuffle(target_states)
                    else:
                        target_states =self.set_target_states(players= players, total_qubits = total_qubits)
            try:
                for i, player in enumerate(players):
                    player.target_state = list(target_states[i])
            except AttributeError as e:
                # print(e)
                pass

            return target_states
        else:
            for player in players:
                try:
                    player.target_state = self.random_statevector(total_qubits)
                except AttributeError as e:
                    print(e)
        return None, None

    def apply_gate_on_game_state(self, gate:str, angle:float= 0):
        gate_matrix = self.get_gate_matrix(gate= gate, angle= angle)
        if gate_matrix is None:
            raise Exception("Given gate is not in the game.")
        self.game_state = self.row_to_coloumn_vector(self.game_state)
        self.game_state = self.multiply_gates(gate_matrix, self.game_state)
        self.game_state = self.coloumn_to_row_vector(self.game_state)

    def get_gate_matrix(self, gate:str, angle:float= 0):
        if (angle not in Constants.R_angles.value) and (angle is not None):
            raise Exception("Gate not valid")
        if gate == 'Rx':
            return QuantumGates.Rx(angle)
        elif gate == 'Ry':
            return QuantumGates.Ry(angle)
        elif gate == 'Rz':
            return QuantumGates.Rz(angle)
        else:
            for i in list(QuantumGates):
                if i.name == gate:
                    return i.value

    def distribute_cards(self, players:list|None = None, decks:int|None=None, num_cards:int= 7):
        if self.game_started:
            raise Exception("Game: "+str(self.game_id)+" already started. Check for other games.")
        self.game_started = True
        player_flag = players.copy()
        if players is not None:
            if len(players)!=0 and (not isinstance(players[0], Player)):
                players = self.player_ids_to_object(players= players)

            for _ in player_flag:
                if _ not in [i.name for i in players]:
                    raise Exception(_ + " is not a player.")

            for player in players:
                if player.game_id is None: 
                    player.game_id = self.game_id
                elif player.game_id != self.game_id:
                    raise Exception(player.name+" doesn't belong to this game.")

        for i in self.get_players():
            if i not in players:
                players.append(i)

        if len(players) == 0 or (players is None):
            raise Exception("No players found")
        
        
        if (decks is None) and (self.num_decks is not None):
            decks = self.num_decks

        cards = [i.name for i in list(QuantumGates)]
        for i in ['Rx', 'Ry', 'Rz', 'add_card', 'remove_card']:
            cards.append(i)
        self.players = players.copy()
        if decks is None:
            for i in range(num_cards):
                for player in players:
                    player.add_card(random.choice(cards))
        else:
            if num_cards*len(players) >= len(cards)*decks:
                raise Exception("Insufficient number of cards to distribute/play")
            self.remaining_cards = self.total_cards() * decks
            for i in range(num_cards):
                for player in players:
                    random_card = random.choice(self.remaining_cards)
                    player.add_card(random_card)
                    self.remaining_cards.remove(random_card)
            # print("After distribution:", len(self.remaining_cards))

    def check_top_fedility(self, player):
        if not isinstance(player, Player):
            player = self.player_ids_to_object(players= player)
        top_fedility = 0
        top_player = None
        player_fedility = self.fidelity(player.target_state, self.game_state).real
        for _player in self.players:
            if (_player not in self.ejected_players) and (_player not in self.winning_players) and (top_fedility < self.fidelity(_player.target_state, self.game_state).real):
                top_fedility = self.fidelity(_player.target_state, self.game_state).real
                top_player = _player
        if (player_fedility > top_fedility) or (player_fedility == 1) or (player == top_player):
            return True
        else:
            return False
                
    def player_cards(self, player:str|Player)-> list:
        if not isinstance(player, Player):
            player = self.player_ids_to_object(players= player)
        if self.is_player_of_game(player):
            return player.cards
        else:
            return Exception("Player not part of the game.")

    def set_game_id(self, players:list|str|Player, game_id:int):
        if isinstance(players, list):
            if not isinstance(players[0], Player):
                players = self.player_ids_to_object(players= players)
            for player in players:
                player.game_id(game_id)
        elif isinstance(player, str):
            if not isinstance(players, Player):
                players = self.player_ids_to_object(players= players)
            players.game_id(game_id)

    def get_players(self, game_id:int|None = None)-> list:
        if game_id is None:
            game_id = self.game_id
        players = []
        for player in Player.get_all_players():
            if player.game_id == game_id:
                players.append(player)

        return players

    def is_player_of_game(self, player:str|Player, game_id:int|None =None)-> bool:
        if not isinstance(player, Player):
            player = self.player_ids_to_object(players= player)
        return player.game_id == game_id

    def total_cards(self):
        _ = [i.name for i in list(QuantumGates)]
        for i in ["add_card", "remove_card", "Rx", "Ry", "Rz"]:
            _.append(i)
        return _.copy()

    def player_ids_to_object(self, players:list|str|int, game_id:int|None= None)-> list|Player:
        if game_id == None: game_id = self.game_id
        if isinstance(players, list):
            players_obj = []
            for _player in players:
                for player in Player.get_all_players():
                    if player.name == _player:
                        players_obj.append(player)
                        break
            return players_obj
        elif isinstance(players, str|int):
            player = str(players)
            for player in Player.get_all_players():
                if player.name == players:
                    return player

    def players_fedilites(self, players:list)-> dict:
        fedilities = {}
        if not isinstance(players[0], Player):
            players = self.player_ids_to_object(players= players)
        for player in players:
            fedilities[player.name] = self.fidelity(player.target_state, self.game_state).real
        return fedilities
    
    def drop_card(self, players:list, player:Player|str, card:str, qubits:list= [], angle:float = None, game_id:int|None =None)-> (int|None, list, str, dict):
        self.players = self.get_players(game_id= self.game_id)
        if game_id is None:
            game_id = self.game_id
        if not self.is_player_of_game(player= player, game_id= game_id):
            raise Exception("Player not a part of the game.")
        if isinstance(player, str):
            player = self.player_ids_to_object(players= player)
        if not isinstance(players[0], Player):
            players = self.player_ids_to_object(players= players)
        for _player_ in players:
            if not self.is_player_of_game(player= _player_, game_id= game_id):
                raise Exception("Player not a part of the game.")
        measurement = None
        try:
            player.cards.remove(card)
        except ValueError as e:
            raise Exception("Card not in Player's cards")
        if card == "add_card":
            self.game_state = QuantumGates.add_qubit(statevector= self.game_state)
        elif card == "remove_card":
            if len(self.game_state) == 2:
                raise Exception("Remove card is not allowded here")
            measurement, self.game_state = QuantumGates.measure_and_remove_qubit(qubit= qubits[0], statevector= self.game_state)
        else:
            gate_matrix = self.get_gate_matrix(gate= card)
            num_qubits = self.num_qubits_required(gate_matrix)
            if len(qubits)!=num_qubits or  qubits[0] not in range(int(cmath.log(len(self.game_state), 2).real)):
                player.add_card(card= card)
                raise Exception("Gate is not applicable for this set of qubits.")
            total_unitary = self.get_total_unitary(unitary= gate_matrix, total_qubits = int(cmath.log(len(self.game_state), 2).real),qubit_num = qubits)
            self.game_state = self.multiply_gates(total_unitary, self.row_to_coloumn_vector(self.game_state))
            self.game_state = self.coloumn_to_row_vector(self.game_state)
        
        if self.num_decks is not None:
            new_card = random.choice(self.remaining_cards)
            self.remaining_cards.remove(new_card)
        else:
            new_card = random.choice(self.total_cards())
        player.add_card(new_card)

        fidelities = self.players_fedilites(players=players)
        # print("After dfropping:", len(self.remaining_cards))

        return measurement, self.game_state, new_card, fidelities
        
    def get_top_players(self, current_players:list= []):
        """Returns top players in the given list of players or given an empty list it returns top players from the current players

        Args:
            current_players (list, optional): Players. Defaults to [].

        Returns:
            list
        """
        current_players = self.player_ids_to_object(players= current_players)        
        if current_players == []:
            for _player in self.players:
                if (_player not in self.ejected_players) and (_player not in self.winning_players):
                    current_players.append(_player)
        
        top_players = sorted(current_players, key=lambda player: self.fidelity(player.target_state, self.game_state).real)
        return top_players       

    def add_deck(self):
        """Adds one deck of cards to the game.
        """
        if self.num_decks is not None:  
            self.num_decks = self.num_decks+1
            for i in self.total_cards():
                self.remaining_cards.append(i)

    def winners_list(self)->list:
        """ Returns list of all players in winning order.

        Returns:
            list
        """        
        top_list = []
        current_top_players = self.get_top_players()
        for player in self.winning_players:
            top_list.append(player)
        for player in current_top_players:
            top_list.append(player)
        for player in self.ejected_players:
            top_list.append(player)
        return top_list

    def won_players(self)-> list:
        return self.winning_players
    
    def lost_players(self)-> list:
        return self.ejected_players
    
    def get_game_sequence(self)-> (list, list, list):
        return self.gate_sequence, self.target_sequence_num, self.random_angles

    def show(self, player:str):
        player = self.player_ids_to_object(players= player)
        if self.check_top_fedility(player):
            self.winning_players.append(player)
            b = True
        else:
            self.ejected_players.insert(0, player)
            b = False
        player.target_state = None 
        player.empty_cards()
        player.game_id = None
        return b

    def drop(self, player:str):
        player = self.player_ids_to_object(players= player)
        self.ejected_players.append(player)
        player.target_state = None 
        player.empty_cards()
        player.game_id = None

    def end_game(self):
        players = self.get_top_players()
        for player in players:
            self.winning_players.append(player)
            player.target_state = None 
            player.empty_cards()
            player.game_id = None


        
gates = ['X', 'Z', 'Rx', 'CX', 'Ry','Reset']
qubits  =[[1], [0], [2], [0,1], [2], [1]]
angles = [None, None, cmath.pi, None, cmath.pi/4, None]

Game().save_circuit_image(gates=gates, qubits=qubits, angles=angles)

