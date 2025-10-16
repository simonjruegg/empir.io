import pygame
import random
from map_loader_dynamic import (
    copy_to_temp_map,
    load_grid,
    shade_grid,
    add_city_with_zone,
    shade_city_and_zone,
    orthogonal_neighbors,
    PLAYER_COLORS,
    CITY_COLORS
)

# Ensure temp map exists
copy_to_temp_map()

pygame.init()
WIDTH, HEIGHT = 1200, 600  # extra width for scoreboard
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("City and Zone Viewer")

GRID_LEFT, GRID_TOP = 10, 40
UI_WIDTH = 250  # space for scoreboard on the right
FONT = pygame.font.SysFont(None, 28)
INFO_FONT = pygame.font.SysFont(None, 22)


def draw_grid(grid, cell_w, cell_h):
    for row in grid:
        for cell in row:
            rect = pygame.Rect(
                GRID_LEFT + cell.x * cell_w,
                GRID_TOP + cell.y * cell_h,
                cell_w,
                cell_h
            )
            pygame.draw.rect(screen, cell.display_color, rect)


def draw_scoreboard(grid):
    # Count tiles per player
    player_tiles = {}
    for row in grid:
        for cell in row:
            if cell.owner:
                player_tiles[cell.owner] = player_tiles.get(cell.owner, 0) + 1

    # Draw sidebar background
    sidebar_rect = pygame.Rect(WIDTH - UI_WIDTH, 0, UI_WIDTH, HEIGHT)
    pygame.draw.rect(screen, (50, 50, 60), sidebar_rect)

    y_offset = 20
    for player_id, count in sorted(player_tiles.items()):
        if count > 0:
            color = PLAYER_COLORS.get(player_id, (180, 180, 180))
            text = FONT.render(f"Player {player_id}: {count}", True, color)
            screen.blit(text, (WIDTH - UI_WIDTH + 20, y_offset))
            y_offset += 40


def draw_tile_info(grid, cell_w, cell_h):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x = (mouse_x - GRID_LEFT) // cell_w
    grid_y = (mouse_y - GRID_TOP) // cell_h

    if 0 <= grid_x < len(grid[0]) and 0 <= grid_y < len(grid):
        cell = grid[grid_y][grid_x]
        owner_text = str(cell.owner) if cell.owner else "None"
        type_text = "City" if cell.is_city else "Zone" if cell.in_zone else "Normal"
        info_lines = [
            f"X: {cell.x}, Y: {cell.y}",
            f"Terrain: {cell.terrain}",
            f"Type: {type_text}",
            f"Owner: {owner_text}"
        ]
        x_pos = WIDTH - UI_WIDTH + 20
        y_pos = HEIGHT - 100
        for line in info_lines:
            text_surf = INFO_FONT.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (x_pos, y_pos))
            y_pos += 20


def main():
    # Load map dynamically
    grid, rows, cols = load_grid()  # unpack rows and cols

    # Compute square cell size to fit screen
    cell_w = cell_h = min(
        (HEIGHT - GRID_TOP - 10) // rows,
        (WIDTH - GRID_LEFT - UI_WIDTH) // cols
    )

    # Shade terrain
    shade_grid(grid)

    # Add player cities
    add_city_with_zone(grid, zone_size=200, player_id=1)
    add_city_with_zone(grid, zone_size=750, player_id=2)
    for i in range(3,9):
        add_city_with_zone(grid, zone_size=150, player_id=i)
    # Initial shading
    shade_city_and_zone(grid)

    running = True
    clock = pygame.time.Clock()

    def check_owner(pos):
        x, y = pos
        grid_x = (x - GRID_LEFT) // cell_w
        grid_y = (y - GRID_TOP) // cell_h
        if 0 <= grid_x < cols and 0 <= grid_y < rows:
            cell = grid[grid_y][grid_x]
            if not cell.owner:
                return "unowned"
            return cell.owner
        return None

    def launch_attack(targetplayer):
        if targetplayer == "unowned":
            targetplayer = None
        print(f"Attacking player {targetplayer}!")
        attackable_cells = []
        for row in grid:
            for cell in row:
                if cell.owner == targetplayer:
                    for nx, ny in [(cell.x-1, cell.y), (cell.x+1, cell.y), (cell.x, cell.y-1), (cell.x, cell.y+1)]:
                        if 0 <= nx < cols and 0 <= ny < rows:
                            neighbor_cell = grid[ny][nx]
                            if neighbor_cell.owner == 1 and neighbor_cell.in_zone:
                                if cell.terrain == "earth" and not cell.is_city:
                                    attackable_cells.append(cell)
                                elif cell.terrain == "mountain" and not cell.is_city:
                                    # check amount of neighbors (distance of 2) owned by player 1
                                    owned_near = sum(1 for n in orthogonal_neighbors(grid, cell.x, cell.y, distance=2) if n.owner == 1)
                                    owned_neighbors = sum(1 for n in orthogonal_neighbors(grid, cell.x, cell.y, distance=1) if n.owner == 1)
                                    # handle cells nea
                                    if random.random() < 0.02*owned_near and owned_neighbors > 0:

                                        attackable_cells.append(cell)
                                elif cell.terrain == "water" and not cell.is_city:
                                    if random.random() < 0:
                                        attackable_cells.append(cell)
                                elif cell.is_city:
                                    owned_near = sum(1 for n in orthogonal_neighbors(grid, cell.x, cell.y, distance=2) if n.owner == 1)
                                    owned_neighbors = sum(1 for n in orthogonal_neighbors(grid, cell.x, cell.y, distance=1) if n.owner == 1)
                                    # handle cells nea
                                    if random.random() < 0.01*owned_near and owned_neighbors > 0:

                                        attackable_cells.append(cell)
                                break
        if attackable_cells:
            for cell in attackable_cells:
                cell.owner = 1
                cell.in_zone = True
            # Reshade after attack
            shade_city_and_zone(grid)

    while running:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    targetplayer = check_owner(pygame.mouse.get_pos())
                    if targetplayer and targetplayer != 1:
                        launch_attack(targetplayer)

        screen.fill((30, 30, 40))
        draw_grid(grid, cell_w, cell_h)
        draw_scoreboard(grid)
        draw_tile_info(grid, cell_w, cell_h)
        pygame.display.flip()


if __name__ == "__main__":
    main()
