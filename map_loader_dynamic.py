# map_loader_dynamic.py
# Handles dynamic map loading, saving, shading, and temporary map updates with 2 players

import json
import os
import random
from collections import deque
import shutil

# Default colors
COLORS = {
    "mountain": (120, 120, 120),
    "earth": (60, 160, 80),
    "water": (60, 100, 200),
    "light_water": (100, 160, 240),
    "snow_mountain": (240, 240, 240),
}

# Player zone and city colors
PLAYER_COLORS = {
    1: (180, 80, 80),   # Player 1 = red
    2: (80, 120, 200),  # Player 2 = blue
    3: (200, 180, 80),  # Player 3 = yellow
    4: (255, 255, 255),  # Player 4 = white
    5: (80, 200, 120),  # Player 5 = green
    6: (200, 80, 200),  # Player 6 = purple
    7: (255, 165, 0),   # Player 7 = orange
    8: (50,50,50)      # Player 8 = gray
}

CITY_COLORS = {
    1: (0, 0, 0),
    2: (0, 0, 0),
    3: (0, 0, 0),
    4: (0, 0, 0),
    5: (0, 0, 0),
    6: (0, 0, 0),
    7: (0, 0, 0),
    8: (0, 0, 0)

}

TEMP_MAP_FILE = "temp_map.json"


class Cell:
    def __init__(self, x, y, terrain, owner=None, is_city=False):
        self.x = x
        self.y = y
        self.terrain = terrain
        self.owner = owner  # Player ID
        self.is_city = is_city
        self.in_zone = False
        self.display_color = COLORS.get(terrain, (255, 0, 0))


def copy_to_temp_map(filename="map.json"):
    """Copy the original map to temp_map.json for a fresh start."""
    if os.path.exists(TEMP_MAP_FILE):
        os.remove(TEMP_MAP_FILE)
    shutil.copyfile(filename, TEMP_MAP_FILE)
    print(f"📝 Temporary map created: {TEMP_MAP_FILE}")


def load_grid(filename=TEMP_MAP_FILE):
    """Load temp map, create Cell objects, return grid and size."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"No map file found at {filename}")

    with open(filename, "r") as f:
        data = json.load(f)

    rows = data.get("rows", 18)
    cols = data.get("columns", 30)
    grid_data = data.get("cells", [])

    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            cell_data = grid_data[y][x]
            terrain = cell_data.get("terrain", "earth")
            owner = cell_data.get("owner")
            is_city = cell_data.get("is_city", False)
            cell = Cell(x, y, terrain, owner, is_city)
            row.append(cell)
        grid.append(row)

    return grid, rows, cols


def save_temp_map(grid, filename=TEMP_MAP_FILE):
    """Save the current grid state to temp_map.json."""
    rows = len(grid)
    cols = len(grid[0])
    data = {
        "columns": cols,
        "rows": rows,
        "cells": [
            [
                {
                    "terrain": cell.terrain,
                    "owner": cell.owner,
                    "is_city": cell.is_city
                }
                for cell in row
            ]
            for row in grid
        ],
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def neighbors(grid, x, y, radius=1):
    h = len(grid)
    w = len(grid[0])
    neigh = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                neigh.append(grid[ny][nx])
    return neigh


def orthogonal_neighbors(grid, x, y, distance=1):
    """Return top, bottom, left, right neighbors only."""
    h = len(grid)
    w = len(grid[0])
    neigh = []
    for d in range(1, distance + 1):
        for dx, dy in [(-d, 0), (d, 0), (0, -d), (0, d)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                neigh.append(grid[ny][nx])
    return neigh


def apply_variance(color, amount=0):
    r, g, b = color
    variation = random.randint(-amount, amount)
    return (
        max(0, min(255, r + variation // 3)),
        max(0, min(255, g + variation)),
        max(0, min(255, b + variation // 3)),
    )


def shade_grid(grid):
    """Compute display colors once for all cells, based on terrain and adjacency."""
    h = len(grid)
    w = len(grid[0])

    for y in range(h):
        for x in range(w):
            cell = grid[y][x]

            if cell.terrain == "water":
                near_land_1 = any(n.terrain != "water" for n in neighbors(grid, x, y, 1))
                near_land_2 = any(n.terrain != "water" for n in neighbors(grid, x, y, 2))

                if near_land_1:
                    base = COLORS["light_water"]
                elif near_land_2 and random.random() < 0.5:
                    base = COLORS["light_water"]
                else:
                    base = COLORS["water"]

            elif cell.terrain == "mountain":
                neigh = neighbors(grid, x, y, 1)
                if all(n.terrain == "mountain" for n in neigh):
                    base = COLORS["snow_mountain"] if random.random() < 0.5 else COLORS["mountain"]
                else:
                    base = COLORS["mountain"]

            elif cell.terrain == "earth":
                base = COLORS["earth"]

            else:
                base = (255, 0, 0)

            cell.display_color = apply_variance(base)


def add_city_with_zone(grid, zone_size=36, player_id=1):
    """Place a city on earth and assign a zone of control of given size (only on earth)."""
    earth_cells = [c for row in grid for c in row if c.terrain == "earth" and c.owner is None]

    if not earth_cells:
        raise RuntimeError(f"No earth cells to place a city for player {player_id}!")

    attempts = 0
    while attempts < 100:
        attempts += 1
        city = random.choice(earth_cells)
        zone = compute_zone(grid, city, zone_size)

        if zone:  # successfully assigned all zone cells
            city.is_city = True
            city.owner = player_id
            for cell in zone:
                cell.in_zone = True
                cell.owner = player_id
            save_temp_map(grid)
            return city

    raise RuntimeError(f"Could not place a city with enough earth for player {player_id}.")


def compute_zone(grid, city, max_cells):
    """Compute a more round-looking zone of control using BFS with randomized orthogonal expansion."""
    visited = set()
    zone_cells = []

    queue = deque()
    queue.append(city)
    visited.add((city.x, city.y))

    while queue and len(zone_cells) < max_cells:
        current = queue.popleft()
        if current != city and current.terrain == "earth":
            zone_cells.append(current)

        orth_neigh = orthogonal_neighbors(grid, current.x, current.y)
        random.shuffle(orth_neigh)

        for n in orth_neigh:
            if (n.x, n.y) in visited or n.terrain != "earth" or n.owner is not None:
                continue
            visited.add((n.x, n.y))
            queue.append(n)

    if len(zone_cells) < max_cells:
        return None
    return zone_cells


def shade_city_and_zone(grid):
    """Shade zones based on ownership with orthogonal borders."""
    for row in grid:
        for cell in row:
            # Base color from terrain
            base_terrain_color = COLORS.get(cell.terrain, (255, 0, 0))

            if cell.is_city:
                cell.display_color = CITY_COLORS.get(cell.owner, (0, 0, 0))
            elif cell.in_zone:
                border = any(
                    n.owner != cell.owner for n in orthogonal_neighbors(grid, cell.x, cell.y)
                )
                color = PLAYER_COLORS.get(cell.owner, (180, 180, 180))
                if border:
                    cell.display_color = color
                else:
                    overlay = color
                    cell.display_color = tuple(
                        int(base_terrain_color[i] * 0.5 + overlay[i] * 0.5) for i in range(3)
                    )
