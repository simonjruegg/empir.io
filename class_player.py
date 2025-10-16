# create class for player

class Player:
    def __init__(self, playernumber, name, troops, resources, territories):
        self.playernumber = playernumber
        self.troops = troops
        self.resources = resources
        self.territories = territories
        self.name = name

