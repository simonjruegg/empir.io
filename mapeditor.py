# territorial_map_editor.py
# Terrain map editor with painter + buttons, JSON save/load
# 60x60 square map, square cells

import pygame
import random
import json
import os

pygame.init()
pygame.font.init()

FPS = 30
WIDTH, HEIGHT = 1400, 750  # wider to fit UI buttons
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Terrain Map Editor")

# Map parameters
COLUMNS, ROWS = 60, 60  # square map
CELL_MARGIN = 1
GRID_LEFT = 10
GRID_TOP = 40

# Compute square cells
CELL_SIZE = (HEIGHT - GRID_TOP - 10) // ROWS
CELL_W = CELL_SIZE
CELL_H = CELL_SIZE
GRID_WIDTH = CELL_W * COLUMNS
GRID_HEIGHT = CELL_H * ROWS

# Colors
BG = (25, 25, 30)
GRID_BG = (40, 40, 46)

TERRAIN_ORDER = ["mountain", "water", "earth"]
TERRAIN_COLORS = {
    "mountain": (120, 120, 120),
    "earth": (60, 160, 80),
    "water": (60, 100, 200),
}
SELECTED_BORDER = (255, 255, 255)

# UI parameters
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 40
BUTTON_MARGIN = 20
BUTTON_X = GRID_LEFT + GRID_WIDTH + 20

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)


class Cell:
    def __init__(self, x, y, terrain):
        self.x = x
        self.y = y
        self.terrain = terrain

        # Ownership and city
        self.owner = None
        self.is_city = False

    def rect(self):
        rx = GRID_LEFT + self.x * CELL_W
        ry = GRID_TOP + self.y * CELL_H
        return pygame.Rect(
            rx + CELL_MARGIN,
            ry + CELL_MARGIN,
            CELL_W - 2 * CELL_MARGIN,
            CELL_H - 2 * CELL_MARGIN,
        )

    def color(self):
        base = TERRAIN_COLORS.get(self.terrain, (255, 0, 0))
        if self.is_city:
            return (0, 0, 0)
        return base

    def cycle_terrain(self):
        idx = TERRAIN_ORDER.index(self.terrain)
        self.terrain = TERRAIN_ORDER[(idx + 1) % len(TERRAIN_ORDER)]


def create_grid():
    terrains = list(TERRAIN_COLORS.keys())
    return [
        [Cell(x, y, terrains[1]) for x in range(COLUMNS)]
        for y in range(ROWS)
    ]


def draw_grid(grid, selected):
    pygame.draw.rect(screen, GRID_BG, (GRID_LEFT, GRID_TOP, GRID_WIDTH, GRID_HEIGHT))
    for row in grid:
        for cell in row:
            pygame.draw.rect(screen, cell.color(), cell.rect())

    if selected:
        pygame.draw.rect(screen, SELECTED_BORDER, selected.rect(), 2)


def draw_ui(selected_terrain):
    # Draw terrain buttons
    for i, terrain in enumerate(TERRAIN_ORDER):
        btn_y = GRID_TOP + i * (BUTTON_HEIGHT + BUTTON_MARGIN)
        rect = pygame.Rect(BUTTON_X, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(screen, TERRAIN_COLORS[terrain], rect)
        # highlight selected
        if terrain == selected_terrain:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)
        # text
        txt = font.render(terrain.capitalize(), True, (0, 0, 0))
        txt_rect = txt.get_rect(center=rect.center)
        screen.blit(txt, txt_rect)


def pixel_to_cell(mx, my):
    if mx < GRID_LEFT or my < GRID_TOP:
        return None
    cx = (mx - GRID_LEFT) // CELL_W
    cy = (my - GRID_TOP) // CELL_H
    if 0 <= cx < COLUMNS and 0 <= cy < ROWS:
        return cx, cy
    return None


def save_grid_to_json(grid, filename="map.json"):
    data = {
        "columns": COLUMNS,
        "rows": ROWS,
        "cells": [
            [
                {
                    "x": cell.x,
                    "y": cell.y,
                    "terrain": cell.terrain,
                    "owner": cell.owner,
                    "is_city": cell.is_city,
                }
                for cell in row
            ]
            for row in grid
        ],
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Map saved to {filename}")


def load_grid_from_json(filename="map.json"):
    if not os.path.exists(filename):
        print(f"⚠️ No {filename} found — generating new map.")
        return None

    with open(filename, "r") as f:
        data = json.load(f)

    cols = data.get("columns", COLUMNS)
    rows = data.get("rows", ROWS)
    grid_data = data.get("cells", [])

    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            cell_data = grid_data[y][x]
            terrain = cell_data.get("terrain", "earth")
            cell = Cell(x, y, terrain)
            cell.owner = cell_data.get("owner", None)
            cell.is_city = cell_data.get("is_city", False)
            row.append(cell)
        grid.append(row)

    print(f"✅ Map loaded from {filename}")
    return grid


def main():
    grid = create_grid()
    selected = None
    selected_terrain = TERRAIN_ORDER[0]  # default painter
    running = True
    right_click_held = False

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    grid = create_grid()
                    selected = None
                elif event.key == pygame.K_s:
                    save_grid_to_json(grid)
                elif event.key == pygame.K_l:
                    loaded = load_grid_from_json()
                    if loaded:
                        grid = loaded

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                # Left click for selecting cell & cycling terrain
                if event.button == 1:
                    cell_coords = pixel_to_cell(*pos)
                    if cell_coords:
                        cx, cy = cell_coords
                        selected = grid[cy][cx]
                        selected.cycle_terrain()
                        # Shift+click toggles city
                        keys = pygame.key.get_pressed()
                        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                            selected.is_city = not selected.is_city
                    # Check if clicked a button
                    for i, terrain in enumerate(TERRAIN_ORDER):
                        btn_y = GRID_TOP + i * (BUTTON_HEIGHT + 20)
                        rect = pygame.Rect(BUTTON_X, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT)
                        if rect.collidepoint(pos):
                            selected_terrain = terrain
                # Right click starts painting
                elif event.button == 3:
                    right_click_held = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    right_click_held = False

        # Paint terrain while holding right-click
        if right_click_held:
            mx, my = pygame.mouse.get_pos()
            cell_coords = pixel_to_cell(mx, my)
            if cell_coords:
                cx, cy = cell_coords
                grid[cy][cx].terrain = selected_terrain

        screen.fill(BG)
        draw_grid(grid, selected)
        draw_ui(selected_terrain)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
