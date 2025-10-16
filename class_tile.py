#create a class to store tile information for each tile on the game board

class Tile:
    def __init__(self, x_position, y_position, terrain_type, development_level):
        self.x_position = x_position
        self.y_position = y_position
        self.terrain_type = terrain_type
        self.development_level = development_level
        self.owner_number = None
        self.troops = 0
        self.defense_modifier = 1.0
        self.buildings = []

