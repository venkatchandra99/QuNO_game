
class Player:
    all_players = []

    def __init__(self, name, target_state = None, game_id = None):
        if name not in [i.name for i in Player.all_players]:
            self.__name = name
            self.__target_state = target_state
            self.__cards = []
            self.__game_id = game_id
            Player.all_players.append(self)
        else:
            raise Exception("Player id already taken. Choose another")

    def __str__(self):
        return f"{self.__name} (Target state: {self.__target_state}, Game id: {self.__game_id})"

    @classmethod
    def get_players_count(cls):
        return len(cls.all_players)

    @classmethod
    def get_all_players(cls):
        return cls.all_players

    @property
    def name(self):
        return self.__name

    @property
    def target_state(self):
        return self.__target_state

    @property
    def game_id(self):
        return self.__game_id

    @target_state.setter
    def target_state(self, target):
        self.__target_state = target
        
    @game_id.setter
    def game_id(self, _id):
        if self.__game_id is None:
            self.__game_id = _id
        elif (self.__game_id is not None) and (_id is None):
            self.__game_id = None
        elif (self.__game_id is not None) and (_id is not None):
            raise AttributeError("Game id already assigned")

    @name.setter
    def name(self, name):
        print(self.__name, end = " --) ")
        self.__name = name
        print(self.__name)

    @property
    def cards(self):
        if self.__cards == []:
            return None
        else:
            return self.__cards
    
    def add_card(self, card:str):
        self.__cards.append(card)

    def empty_cards(self):
        self.__cards = []