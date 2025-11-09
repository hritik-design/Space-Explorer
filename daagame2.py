import pygame
import random
import heapq
import math
import time

pygame.init()
ROWS, COLS = 16, 20
CELL = 40
TOP_UI = 80
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL + TOP_UI
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Explorer")

WHITE = (255, 255, 255)
BLACK = (8, 10, 18)
ORB_YELLOW = (255, 220, 80)
HUD_COLOR = (200, 220, 255)
SHUTTLE_WHITE = (238, 240, 245)
SHUTTLE_METAL = (200, 205, 210)
ENGINE_INNER = (255, 150, 60)
ENGINE_OUTER = (100, 190, 255)
DOCK_PURPLE = (160, 90, 220)

clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 48)
menu_font = pygame.font.Font(None, 64)

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(maze, start, end):
    pq = []
    heapq.heappush(pq, (0, start))
    came, gscore = {}, {start: 0}
    while pq:
        _, cur = heapq.heappop(pq)
        if cur == end:
            path = []
            while cur in came:
                path.append(cur)
                cur = came[cur]
            return path[::-1]
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nb = (cur[0]+dr, cur[1]+dc)
            if 0 <= nb[0] < ROWS and 0 <= nb[1] < COLS and maze[nb[0]][nb[1]] == 0:
                tentative = gscore[cur] + 1
                if tentative < gscore.get(nb, 1e9):
                    came[nb] = cur
                    gscore[nb] = tentative
                    heapq.heappush(pq, (tentative + heuristic(nb, end), nb))
    return []

def generate_solvable_maze():
    for _ in range(200):
        maze = [[0 if random.random() > 0.28 else 1 for _ in range(COLS)] for _ in range(ROWS)]
        maze[0][0] = 0
        maze[ROWS-1][COLS-1] = 0
        path = a_star(maze, (0,0), (ROWS-1,COLS-1))
        if path:
            return maze, path
    maze = [[1]*COLS for _ in range(ROWS)]
    for r in range(ROWS): maze[r][0] = 0
    for c in range(COLS): maze[ROWS-1][c] = 0
    return maze, a_star(maze,(0,0),(ROWS-1,COLS-1))

def new_level(level_num):
    maze, path = generate_solvable_maze()
    open_tiles = [(r,c) for r in range(ROWS) for c in range(COLS) if maze[r][c]==0 and (r,c)!=(0,0) and (r,c)!=(ROWS-1,COLS-1)]
    orb_count = min(6 + level_num, max(6, len(open_tiles)//6))
    orbs = set(random.sample(open_tiles, orb_count))
    return maze, path, orbs

def draw_starfield(offset):
    screen.fill(BLACK)
    random.seed(0)
    for i in range(120):
        x = (i * 37 + offset*0.6) % WIDTH
        y = (i * 91 + offset*0.3) % (HEIGHT - TOP_UI) + TOP_UI
        brightness = 120 + (i % 5) * 20
        pygame.draw.circle(screen, (brightness, brightness, brightness), (int(x), int(y)), (i % 3 == 0) + 1)

def draw_vignette():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    maxr = max(WIDTH, HEIGHT)//2
    for r in range(maxr, 0, -24):
        alpha = max(0, min(200, int(200 * (1 - r/(maxr*1.1)))))
        pygame.draw.circle(overlay, (0,0,0,alpha), (WIDTH//2, (HEIGHT+TOP_UI)//2), r)
    screen.blit(overlay, (0,0))

def lerp(a, b, t): return a + (b - a) * t

def reset_game(level=1):
    maze, path, orbs = new_level(level)
    player_cell = [0,0]
    player_pos = [CELL//2, TOP_UI + CELL//2]
    target_cell = player_cell[:]
    steps, score = 0, 0
    start_time = time.time()
    return maze, path, orbs, player_cell, player_pos, target_cell, steps, score, start_time, []

def draw_asteroid(x, y):
    cx, cy, rad = x + CELL//2, y + CELL//2, CELL//2 - 4
    pygame.draw.circle(screen, (64,64,64), (cx, cy), rad)
    for i in range(3):
        ox, oy = random.randint(-6,6), random.randint(-6,6)
        pygame.draw.circle(screen, (84,80,78), (cx+ox, cy+oy), random.randint(4,10))

def draw_orb(x, y, t):
    pulse = 0.5 + 0.5 * math.sin(t*6 + x*0.03 + y*0.03)
    r = int(CELL*0.22 + pulse*CELL*0.07)
    glow = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
    pygame.draw.circle(glow, (ORB_YELLOW[0], ORB_YELLOW[1], ORB_YELLOW[2], 90), (r*2, r*2), r*2)
    screen.blit(glow, (x - r*2, y - r*2), special_flags=pygame.BLEND_ADD)
    pygame.draw.circle(screen, ORB_YELLOW, (x, y), r)
    pygame.draw.circle(screen, WHITE, (x, y), max(2, r//3))

def draw_dock(cx, cy, t):
    outer = pygame.Surface((CELL*3, CELL*3), pygame.SRCALPHA)
    ox, oy = CELL*1.5, CELL*1.5
    for i in range(6):
        a = max(0, 140 - i*18)
        pygame.draw.circle(outer, (DOCK_PURPLE[0], DOCK_PURPLE[1], DOCK_PURPLE[2], a), (int(ox), int(oy)), int(CELL*1.1 - i*6), 6)
    screen.blit(outer, (cx - CELL*1.5, cy - CELL*1.5), special_flags=pygame.BLEND_ADD)
    pygame.draw.rect(screen, (40,30,60), (cx-26, cy-8, 52, 16), border_radius=6)
    pygame.draw.rect(screen, (220,220,240), (cx-10, cy-10, 20, 20), 2, border_radius=4)
    label = font.render("DOCK", True, (230,230,250))
    screen.blit(label, (cx - label.get_width()//2, cy + 22))

def draw_shuttle(px, py, angle, moving, thruster, trail_particles):
    surf = pygame.Surface((CELL*3, CELL*3), pygame.SRCALPHA)
    cx, cy = CELL*1.5, CELL*1.5
    body = [(cx, cy-20), (cx+18, cy+10), (cx-18, cy+10)]
    pygame.draw.polygon(surf, SHUTTLE_WHITE, body)
    pygame.draw.polygon(surf, SHUTTLE_METAL, body, 2)
    cockpit = [(cx, cy-8), (cx+6, cy+4), (cx-6, cy+4)]
    pygame.draw.polygon(surf, (64,120,160,220), cockpit)
    if moving:
        flame_len = 12 + 6 * math.sin(thruster*20)
        core = [(cx, cy+12), (cx-6, cy+12+flame_len), (cx+6, cy+12+flame_len)]
        pygame.draw.polygon(surf, ENGINE_OUTER, core)
        inner = [(cx, cy+10), (cx-3, cy+10+flame_len*0.6), (cx+3, cy+10+flame_len*0.6)]
        pygame.draw.polygon(surf, ENGINE_INNER, inner)
        for _ in range(2):
            trail_particles.append([px + random.uniform(-6,6), py + random.uniform(6, 12), random.uniform(-20,20), random.uniform(10,40), 0.6])
    rotated = pygame.transform.rotate(surf, -math.degrees(angle) + 90)
    screen.blit(rotated, (px - rotated.get_width()//2, py - rotated.get_height()//2), special_flags=pygame.BLEND_ADD)
    for p in trail_particles[:]:
        p[0] += p[2]/60; p[1] += p[3]/60; p[4] -= 1/60
        if p[4] <= 0: trail_particles.remove(p)
        else:
            alpha = int(200 * p[4] / 0.6)
            s = pygame.Surface((6,6), pygame.SRCALPHA)
            pygame.draw.circle(s, (ENGINE_OUTER[0], ENGINE_OUTER[1], ENGINE_OUTER[2], alpha), (3,3), 3)
            screen.blit(s, (int(p[0]), int(p[1])), special_flags=pygame.BLEND_ADD)

def game_loop():
    level = 1
    maze, path, orbs, player_cell, player_pos, target_cell, steps, score, start_time, particles = reset_game(level)
    star_offset, thruster = 0, 0
    FPS, started, paused, next_ready = 60, False, False, False
    trail_particles = []
    last_dir = (0, 0)
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        star_offset += 80 * dt
        thruster += dt
        t = time.time()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: running = False
                if ev.key == pygame.K_s: started = True
                if ev.key == pygame.K_p: paused = not paused
                if ev.key == pygame.K_n and next_ready:
                    level += 1
                    maze, path, orbs, player_cell, player_pos, target_cell, steps, score, start_time, particles = reset_game(level)
                    next_ready, started = False, True
        if not started:
            draw_starfield(int(star_offset))
            title = menu_font.render("Space Explorer", True, WHITE)
            sub = font.render("Press S to start | ESC to quit", True, HUD_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 10))
            draw_vignette(); pygame.display.flip(); continue
        if paused:
            draw_starfield(int(star_offset))
            ptxt = title_font.render("Paused - P to resume", True, ORB_YELLOW)
            screen.blit(ptxt, (WIDTH//2 - ptxt.get_width()//2, HEIGHT//2))
            draw_vignette(); pygame.display.flip(); continue
        keys = pygame.key.get_pressed()
        new_cell = player_cell[:]; moved = False
        if keys[pygame.K_UP]: new_cell = [player_cell[0]-1, player_cell[1]]; last_dir=(0,-1); moved=True
        elif keys[pygame.K_DOWN]: new_cell = [player_cell[0]+1, player_cell[1]]; last_dir=(0,1); moved=True
        elif keys[pygame.K_LEFT]: new_cell = [player_cell[0], player_cell[1]-1]; last_dir=(-1,0); moved=True
        elif keys[pygame.K_RIGHT]: new_cell = [player_cell[0], player_cell[1]+1]; last_dir=(1,0); moved=True
        if moved:
            r, c = new_cell
            if 0 <= r < ROWS and 0 <= c < COLS and maze[r][c] == 0:
                target_cell, player_cell = new_cell, new_cell[:]; steps += 1
        target_px, target_py = target_cell[1]*CELL + CELL//2, TOP_UI + target_cell[0]*CELL + CELL//2
        player_pos[0] = lerp(player_pos[0], target_px, min(1, 12*dt))
        player_pos[1] = lerp(player_pos[1], target_py, min(1, 12*dt))
        for orb in list(orbs):
            orby, orbx = TOP_UI + orb[0]*CELL + CELL//2, orb[1]*CELL + CELL//2
            if math.hypot(player_pos[0]-orbx, player_pos[1]-orby) < CELL*0.45:
                orbs.remove(orb); score += 100
        if (player_cell[0], player_cell[1]) == (ROWS-1, COLS-1): next_ready = True
        draw_starfield(int(star_offset))
        for r in range(ROWS):
            for c in range(COLS):
                if maze[r][c] == 1: draw_asteroid(c*CELL, TOP_UI + r*CELL)
        for orb in orbs: draw_orb(orb[1]*CELL + CELL//2, TOP_UI + orb[0]*CELL + CELL//2, t)
        goal_x, goal_y = (COLS-1)*CELL + CELL//2, TOP_UI + (ROWS-1)*CELL + CELL//2
        draw_dock(goal_x, goal_y, t)
        angle = math.atan2(last_dir[1], last_dir[0]) if any(last_dir) else -math.pi/2
        draw_shuttle(player_pos[0], player_pos[1], angle, moved, thruster, trail_particles)
        elapsed = int(time.time() - start_time)
        title = title_font.render(f"Space Explorer  •  Level {level}", True, HUD_COLOR)
        info = font.render(f"Score: {score}   Orbs: {len(orbs)}   Steps: {steps}   Time: {elapsed}s   (P pause)", True, HUD_COLOR)
        screen.blit(title, (12, 8)); screen.blit(info, (12, 44))
        if next_ready:
            msg = title_font.render("Dock reached! Press N for Next level", True, ORB_YELLOW)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
        draw_vignette(); pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    game_loop()
