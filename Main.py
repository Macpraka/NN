import math
import random
import sys

import pygame


pygame.init()
pygame.font.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
STAGE_SECONDS = 60

BLACK = (14, 15, 18)
WHITE = (240, 240, 240)
GRAY = (44, 48, 56)
LIGHT_GRAY = (68, 74, 86)
GREEN = (70, 235, 120)
RED = (245, 76, 76)
PINK = (255, 105, 180)
BROWN = (150, 82, 45)
YELLOW = (255, 215, 72)
CYAN = (80, 220, 255)
ORANGE = (255, 145, 48)
PURPLE = (175, 90, 255)
LASER_COLOR = (54, 150, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Brotato Slayer - Stage Boss")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 20)
small_font = pygame.font.SysFont("arial", 16)
shop_font = pygame.font.SysFont("arial", 24)
title_font = pygame.font.SysFont("arial", 46)
button_font = pygame.font.SysFont("arial", 28)

BTN_START_RECT = pygame.Rect(300, 260, 200, 50)
BTN_RECORDS_RECT = pygame.Rect(300, 340, 200, 50)
BTN_BACK_RECT = pygame.Rect(320, 470, 160, 50)

high_score = {
    "max_stage": 1,
    "max_level": 1,
    "max_kills": 0,
    "max_time": 0,
    "bosses_defeated": 0,
}

player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT // 2
player_radius = 20
player_speed = 5
player_coins = 0
player_max_hp = 100
player_hp = 100
player_level = 1
player_xp = 0
player_xp_needed = 12
total_kills = 0

current_stage = 1
stage_heat = 1.0
stage_start_time = 0
stage_elapsed = 0
stage_clear_bonus_paid = False
boss_spawned_this_stage = False

orbit_knives_count = 1
knife_radius = 8
knife_orbit_distance = 60
knife_angle = 0.0
base_knife_speed = 0.04

laser_base_cooldown = 4200
next_laser_time = 0
laser_duration = 15
active_lasers = []

bullets = []
bullet_radius = 5
bullet_speed = 7
shoot_cooldown = 1000
next_shoot_time = 0
next_spawn_time = 0

enemies = []
coins = []
xp_gems = []
chests = []
boss = None

game_state = "MENU"
current_upgrade_choices = []
level_up_start_time = 0
shop_message = ""
shop_message_timer = 0
chest_message = ""
chest_message_timer = 0
invincible_time = 0


def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


def get_stage_heat(stage):
    return 1.0 + (stage - 1) * 0.32


def reset_stage_entities():
    enemies.clear()
    bullets.clear()
    coins.clear()
    xp_gems.clear()
    chests.clear()
    active_lasers.clear()


def reset_game():
    global player_x, player_y, player_max_hp, player_hp, player_coins, player_speed
    global player_level, player_xp, player_xp_needed, total_kills, orbit_knives_count
    global shoot_cooldown, current_stage, stage_heat, stage_start_time, stage_elapsed
    global next_shoot_time, next_laser_time, next_spawn_time, stage_clear_bonus_paid
    global boss_spawned_this_stage
    global boss, chest_message_timer, shop_message, shop_message_timer, invincible_time

    player_x, player_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    player_max_hp = 100
    player_hp = player_max_hp
    player_coins = 0
    player_speed = 5
    player_level = 1
    player_xp = 0
    player_xp_needed = 12
    total_kills = 0
    orbit_knives_count = 1
    shoot_cooldown = 1000
    current_stage = 1
    stage_heat = get_stage_heat(current_stage)
    stage_start_time = pygame.time.get_ticks()
    stage_elapsed = 0
    stage_clear_bonus_paid = False
    boss_spawned_this_stage = False
    boss = None
    chest_message_timer = 0
    shop_message = ""
    shop_message_timer = 0
    invincible_time = 0

    reset_stage_entities()
    next_shoot_time = stage_start_time + shoot_cooldown
    next_laser_time = stage_start_time + laser_base_cooldown
    next_spawn_time = stage_start_time + 700


def start_next_stage():
    global current_stage, stage_heat, stage_start_time, stage_elapsed
    global next_spawn_time, next_shoot_time, next_laser_time, stage_clear_bonus_paid
    global boss_spawned_this_stage
    global boss, player_hp, game_state, shop_message

    current_stage += 1
    stage_heat = get_stage_heat(current_stage)
    stage_start_time = pygame.time.get_ticks()
    stage_elapsed = 0
    stage_clear_bonus_paid = False
    boss_spawned_this_stage = False
    boss = None
    player_hp = min(player_max_hp, player_hp + 25)
    reset_stage_entities()
    next_spawn_time = stage_start_time + 700
    next_shoot_time = stage_start_time + shoot_cooldown
    next_laser_time = stage_start_time + laser_base_cooldown
    shop_message = ""
    game_state = "GAME"


def generate_level_up_choices():
    pool = [
        {"id": "hp", "text": "Max HP +15 and full heal", "desc": "More room for mistakes."},
        {"id": "speed", "text": "Move Speed +1", "desc": "Dodge faster."},
        {"id": "atk_speed", "text": "Attack Speed +15%", "desc": "Shoot and laser more often."},
        {"id": "knife", "text": "Orbit Knife +1 (max 6)", "desc": "Adds another rotating blade."},
        {"id": "heal", "text": "Emergency Heal +40 HP", "desc": "Recover health immediately."},
    ]
    if orbit_knives_count >= 6:
        pool = [item for item in pool if item["id"] != "knife"]
    return random.sample(pool, min(3, len(pool)))


def spawn_enemy():
    side = random.choice(["left", "right", "top", "bottom"])
    if side == "left":
        ex, ey = -30, random.randint(0, SCREEN_HEIGHT)
    elif side == "right":
        ex, ey = SCREEN_WIDTH + 30, random.randint(0, SCREEN_HEIGHT)
    elif side == "top":
        ex, ey = random.randint(0, SCREEN_WIDTH), -30
    else:
        ex, ey = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 30

    roll = random.random()
    if roll < 0.62:
        enemies.append({
            "x": ex,
            "y": ey,
            "type": "normal",
            "radius": 15,
            "speed": 1.7 + 0.15 * stage_heat,
            "hp": max(1, int(stage_heat)),
            "max_hp": max(1, int(stage_heat)),
            "color": RED,
        })
    elif roll < 0.86:
        enemies.append({
            "x": ex,
            "y": ey,
            "type": "swift",
            "radius": 10,
            "speed": 3.0 + 0.18 * stage_heat,
            "hp": max(1, int(stage_heat * 0.8)),
            "max_hp": max(1, int(stage_heat * 0.8)),
            "color": PINK,
        })
    else:
        elite_hp = 4 + int(stage_heat * 2)
        enemies.append({
            "x": ex,
            "y": ey,
            "type": "elite",
            "radius": 30,
            "speed": 0.9 + 0.1 * stage_heat,
            "hp": elite_hp,
            "max_hp": elite_hp,
            "color": BROWN,
        })


def spawn_boss():
    global boss
    max_hp = 80 + current_stage * 45
    boss = {
        "x": SCREEN_WIDTH // 2,
        "y": -70,
        "type": "boss",
        "radius": 48,
        "speed": 0.9 + current_stage * 0.05,
        "hp": max_hp,
        "max_hp": max_hp,
        "color": PURPLE,
        "touch_damage": 30,
    }


def drop_loot(enemy):
    global chest_message, chest_message_timer

    heat_bonus = max(1, int(stage_heat))
    if enemy["type"] == "boss":
        coins.append({"x": enemy["x"], "y": enemy["y"], "value": 28 + current_stage * 8})
        xp_gems.append({"x": enemy["x"], "y": enemy["y"], "value": 25 + current_stage * 5})
        chests.append({"x": enemy["x"], "y": enemy["y"], "radius": 12})
        return

    if enemy["type"] == "elite":
        coins.append({"x": enemy["x"], "y": enemy["y"], "value": 5 * heat_bonus})
        xp_gems.append({"x": enemy["x"], "y": enemy["y"], "value": 9})
        if random.random() < 0.25:
            chests.append({"x": enemy["x"], "y": enemy["y"], "radius": 12})
    elif enemy["type"] == "swift":
        coins.append({"x": enemy["x"], "y": enemy["y"], "value": heat_bonus})
        xp_gems.append({"x": enemy["x"], "y": enemy["y"], "value": 3})
    else:
        coins.append({"x": enemy["x"], "y": enemy["y"], "value": heat_bonus})
        xp_gems.append({"x": enemy["x"], "y": enemy["y"], "value": 2})


def damage_enemy(enemy, damage):
    global total_kills, boss

    enemy["hp"] -= damage
    if enemy["hp"] > 0:
        return False

    total_kills += 1
    drop_loot(enemy)
    if enemy["type"] == "boss":
        high_score["bosses_defeated"] = max(high_score["bosses_defeated"], current_stage)
        boss = None
    return True


def damage_target(target, damage):
    if target is boss:
        return damage_enemy(boss, damage)
    return damage_enemy(target, damage)


def all_targets():
    targets = enemies[:]
    if boss is not None:
        targets.append(boss)
    return targets


def finish_stage():
    global game_state, shop_message, shop_message_timer, stage_clear_bonus_paid

    if not stage_clear_bonus_paid:
        bonus = 12 + current_stage * 4
        globals()["player_coins"] += bonus
        shop_message = f"Stage {current_stage} cleared! Bonus +{bonus} coins."
        shop_message_timer = pygame.time.get_ticks() + 4000
        stage_clear_bonus_paid = True

    game_state = "SHOP"
    reset_stage_entities()


def apply_shop_purchase(key):
    global player_coins, player_speed, shoot_cooldown, player_hp, orbit_knives_count
    global player_max_hp, shop_message, shop_message_timer

    now = pygame.time.get_ticks()
    purchases = {
        pygame.K_1: ("Move Speed +1", 5),
        pygame.K_KP1: ("Move Speed +1", 5),
        pygame.K_2: ("Attack Speed +15%", 10),
        pygame.K_KP2: ("Attack Speed +15%", 10),
        pygame.K_3: ("Heal +25 HP", 4),
        pygame.K_KP3: ("Heal +25 HP", 4),
        pygame.K_4: ("Orbit Knife +1", 15),
        pygame.K_KP4: ("Orbit Knife +1", 15),
        pygame.K_5: ("Max HP +20", 12),
        pygame.K_KP5: ("Max HP +20", 12),
    }
    if key not in purchases:
        return

    name, cost = purchases[key]
    if player_coins < cost:
        shop_message = "Not enough coins."
    elif key in [pygame.K_4, pygame.K_KP4] and orbit_knives_count >= 6:
        shop_message = "Orbit knives are already maxed."
    elif key in [pygame.K_2, pygame.K_KP2] and shoot_cooldown <= 150:
        shop_message = "Attack speed is already maxed."
    else:
        player_coins -= cost
        if key in [pygame.K_1, pygame.K_KP1]:
            player_speed += 1
        elif key in [pygame.K_2, pygame.K_KP2]:
            shoot_cooldown = max(150, shoot_cooldown - 150)
        elif key in [pygame.K_3, pygame.K_KP3]:
            player_hp = min(player_max_hp, player_hp + 25)
        elif key in [pygame.K_4, pygame.K_KP4]:
            orbit_knives_count += 1
        elif key in [pygame.K_5, pygame.K_KP5]:
            player_max_hp += 20
            player_hp += 20
        shop_message = f"Bought: {name}"
    shop_message_timer = now + 1800


def draw_bar(x, y, w, h, value, max_value, fill, back=GRAY):
    pygame.draw.rect(screen, back, (x, y, w, h))
    ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
    pygame.draw.rect(screen, fill, (x, y, int(w * ratio), h))


def draw_menu():
    title_text = title_font.render("BROTATO: STAGE SLAYER", True, GREEN)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 130))
    pygame.draw.rect(screen, LIGHT_GRAY, BTN_START_RECT, border_radius=8)
    screen.blit(button_font.render("START GAME", True, WHITE), (325, 270))
    pygame.draw.rect(screen, LIGHT_GRAY, BTN_RECORDS_RECT, border_radius=8)
    screen.blit(button_font.render("RECORDS", True, CYAN), (345, 350))
    tip = font.render("Move with WASD or arrows. Survive 60 seconds to shop.", True, YELLOW)
    screen.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 470))


def draw_records():
    title_text = title_font.render("HALL OF FAME", True, CYAN)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 95))
    records = [
        f"Highest Stage Reached: {high_score['max_stage']}",
        f"Highest Character Level: LV {high_score['max_level']}",
        f"Most Monster Kills: {high_score['max_kills']}",
        f"Longest Survival Time: {high_score['max_time']} seconds",
        f"Highest Boss Defeated: Stage {high_score['bosses_defeated']}",
    ]
    for idx, record in enumerate(records):
        screen.blit(button_font.render(record, True, WHITE), (210, 205 + idx * 45))
    pygame.draw.rect(screen, RED, BTN_BACK_RECT, border_radius=8)
    screen.blit(button_font.render("BACK", True, WHITE), (370, 480))


def draw_world():
    for gem in xp_gems:
        pygame.draw.circle(screen, CYAN, (int(gem["x"]), int(gem["y"])), 5)
    for coin in coins:
        pygame.draw.circle(screen, YELLOW, (int(coin["x"]), int(coin["y"])), 6)
    for bullet in bullets:
        pygame.draw.circle(screen, YELLOW, (int(bullet["x"]), int(bullet["y"])), bullet_radius)
    for enemy in enemies:
        pygame.draw.circle(screen, enemy["color"], (int(enemy["x"]), int(enemy["y"])), enemy["radius"])
        if enemy["max_hp"] > 1:
            draw_bar(enemy["x"] - 22, enemy["y"] - enemy["radius"] - 12, 44, 5, enemy["hp"], enemy["max_hp"], GREEN)
    if boss is not None:
        pygame.draw.circle(screen, boss["color"], (int(boss["x"]), int(boss["y"])), boss["radius"])
        pygame.draw.circle(screen, (225, 210, 255), (int(boss["x"]), int(boss["y"])), 20, 3)
        draw_bar(160, 565, 480, 16, boss["hp"], boss["max_hp"], PURPLE, (42, 28, 54))
        boss_txt = font.render(f"STAGE {current_stage} BOSS", True, WHITE)
        screen.blit(boss_txt, (SCREEN_WIDTH // 2 - boss_txt.get_width() // 2, 540))
    for chest in chests:
        pygame.draw.rect(screen, ORANGE, (int(chest["x"] - 10), int(chest["y"] - 8), 20, 16), border_radius=3)
        pygame.draw.line(screen, YELLOW, (chest["x"] - 10, chest["y"] - 2), (chest["x"] + 10, chest["y"] - 2), 2)
    for laser in active_lasers:
        pygame.draw.line(screen, LASER_COLOR, laser["start"], laser["end"], 12)

    player_color = (145, 255, 145) if pygame.time.get_ticks() < invincible_time else GREEN
    pygame.draw.circle(screen, player_color, (int(player_x), int(player_y)), player_radius)
    for i in range(orbit_knives_count):
        angle = knife_angle + (i * (2 * math.pi / orbit_knives_count))
        kx = player_x + math.cos(angle) * knife_orbit_distance
        ky = player_y + math.sin(angle) * knife_orbit_distance
        pygame.draw.circle(screen, ORANGE, (int(kx), int(ky)), knife_radius)


def draw_hud():
    remaining = max(0, STAGE_SECONDS - stage_elapsed)
    screen.blit(font.render(f"Stage: {current_stage} | Heat: {stage_heat:.1f}x | Time left: {remaining}s", True, CYAN), (10, 10))
    screen.blit(font.render(f"Coins: {player_coins} | Kills: {total_kills}", True, WHITE), (10, 34))
    draw_bar(10, 62, 200, 12, player_hp, player_max_hp, GREEN, RED)
    draw_bar(10, 82, 200, 8, player_xp, player_xp_needed, CYAN, GRAY)
    screen.blit(font.render(f"LV {player_level}", True, WHITE), (220, 55))

    if boss is None and stage_elapsed >= STAGE_SECONDS - 18 and game_state == "GAME":
        warning = font.render("Boss incoming. Survive 60 seconds to reach the shop.", True, YELLOW)
        screen.blit(warning, (SCREEN_WIDTH // 2 - warning.get_width() // 2, 18))

    if current_time < chest_message_timer:
        msg = font.render(chest_message, True, YELLOW)
        pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH // 2 - 200, 105, 400, 34), border_radius=5)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 112))


def draw_level_up():
    panel = pygame.Surface((390, 440))
    panel.set_alpha(238)
    panel.fill(GRAY)
    screen.blit(panel, (25, SCREEN_HEIGHT // 2 - 220))
    title = shop_font.render("LEVEL UP! CHOOSE AN UPGRADE", True, YELLOW)
    screen.blit(title, (45, SCREEN_HEIGHT // 2 - 190))
    for idx, choice in enumerate(current_upgrade_choices):
        card_y = SCREEN_HEIGHT // 2 - 100 + idx * 85
        pygame.draw.rect(screen, LIGHT_GRAY, (45, card_y, 350, 70), border_radius=6)
        pygame.draw.rect(screen, CYAN, (45, card_y, 350, 70), width=2, border_radius=6)
        screen.blit(font.render(choice["text"], True, WHITE), (60, card_y + 12))
        screen.blit(small_font.render(choice["desc"], True, YELLOW), (60, card_y + 40))


def draw_shop():
    panel = pygame.Surface((720, 470))
    panel.set_alpha(244)
    panel.fill(GRAY)
    screen.blit(panel, (40, 70))

    title = shop_font.render(f"SHOP - STAGE {current_stage} CLEARED", True, YELLOW)
    screen.blit(title, (65, 95))
    help_txt = font.render("Buy with number keys. Press ENTER to start the next stage.", True, WHITE)
    screen.blit(help_txt, (65, 128))

    items = [
        "[1] Move Speed +1 (5 coins)",
        "[2] Attack Speed +15% (10 coins)",
        "[3] Heal +25 HP (4 coins)",
        "[4] Orbit Knife +1 (15 coins)",
        "[5] Max HP +20 (12 coins)",
    ]
    for idx, item in enumerate(items):
        screen.blit(font.render(item, True, WHITE), (75, 180 + idx * 38))

    stats = [
        f"Coins: {player_coins}",
        f"HP: {player_hp} / {player_max_hp}",
        f"Move Speed: {player_speed}",
        f"Fire Rate: {int((1000 / shoot_cooldown) * 100)}%",
        f"Orbit Knives: {orbit_knives_count} / 6",
        f"Next Stage Heat: {get_stage_heat(current_stage + 1):.1f}x",
    ]
    for idx, stat in enumerate(stats):
        screen.blit(font.render(stat, True, CYAN if idx == 5 else WHITE), (475, 180 + idx * 38))

    if pygame.time.get_ticks() < shop_message_timer:
        msg = font.render(shop_message, True, YELLOW)
        screen.blit(msg, (65, 480))


def draw_game_over():
    pygame.draw.rect(screen, GRAY, (180, 145, 440, 315), border_radius=12)
    go_text = title_font.render("GAME OVER", True, RED)
    screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 175))
    lines = [
        f"Final Stage: {current_stage}",
        f"Final Character Level: LV {player_level}",
        f"Total Kills: {total_kills}",
        f"Survival Time: {stage_elapsed} seconds",
        "Press SPACE to return to menu",
    ]
    for idx, line in enumerate(lines):
        color = YELLOW if idx == len(lines) - 1 else WHITE
        screen.blit(font.render(line, True, color), (265, 260 + idx * 35))


running = True
while running:
    clock.tick(FPS)
    current_time = pygame.time.get_ticks()

    if game_state == "GAME":
        stage_elapsed = (current_time - stage_start_time) // 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if game_state == "MENU":
                if BTN_START_RECT.collidepoint(mx, my):
                    reset_game()
                    game_state = "GAME"
                elif BTN_RECORDS_RECT.collidepoint(mx, my):
                    game_state = "ACHIEVEMENTS"
            elif game_state == "ACHIEVEMENTS" and BTN_BACK_RECT.collidepoint(mx, my):
                game_state = "MENU"
            elif game_state == "LEVEL_UP":
                for idx, choice in enumerate(current_upgrade_choices):
                    card_y = SCREEN_HEIGHT // 2 - 100 + idx * 85
                    if pygame.Rect(45, card_y, 350, 70).collidepoint(mx, my):
                        if choice["id"] == "hp":
                            player_max_hp += 15
                            player_hp = player_max_hp
                        elif choice["id"] == "speed":
                            player_speed += 1
                        elif choice["id"] == "atk_speed":
                            shoot_cooldown = max(150, shoot_cooldown - 150)
                        elif choice["id"] == "knife" and orbit_knives_count < 6:
                            orbit_knives_count += 1
                        elif choice["id"] == "heal":
                            player_hp = min(player_max_hp, player_hp + 40)
                        stage_start_time += current_time - level_up_start_time
                        game_state = "GAME"
                        break

        if event.type == pygame.KEYDOWN:
            if game_state == "GAMEOVER" and event.key == pygame.K_SPACE:
                game_state = "MENU"
            elif game_state == "SHOP":
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                    start_next_stage()
                else:
                    apply_shop_purchase(event.key)

    if game_state == "GAME":
        attack_speed_modifier = 1000 / shoot_cooldown

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player_y += player_speed
        player_x = max(player_radius, min(SCREEN_WIDTH - player_radius, player_x))
        player_y = max(player_radius, min(SCREEN_HEIGHT - player_radius, player_y))

        knife_angle += base_knife_speed * attack_speed_modifier

        if stage_elapsed < STAGE_SECONDS:
            spawn_cooldown = max(230, int(1500 / stage_heat))
            if current_time >= next_spawn_time:
                spawn_enemy()
                next_spawn_time = current_time + spawn_cooldown
        if stage_elapsed >= 45 and boss is None and not boss_spawned_this_stage:
            boss_spawned_this_stage = True
            spawn_boss()

        targets = all_targets()
        if current_time >= next_shoot_time:
            if targets:
                nearest = min(targets, key=lambda e: (e["x"] - player_x) ** 2 + (e["y"] - player_y) ** 2)
                dist = distance(nearest["x"], nearest["y"], player_x, player_y)
                if dist:
                    bullets.append({
                        "x": player_x,
                        "y": player_y,
                        "dx": (nearest["x"] - player_x) / dist,
                        "dy": (nearest["y"] - player_y) / dist,
                    })
            next_shoot_time = current_time + shoot_cooldown

        laser_cooldown = max(1000, int(laser_base_cooldown / attack_speed_modifier))
        if current_time >= next_laser_time:
            if targets:
                nearest = min(targets, key=lambda e: (e["x"] - player_x) ** 2 + (e["y"] - player_y) ** 2)
                lx, ly = nearest["x"] - player_x, nearest["y"] - player_y
                l_dist = distance(nearest["x"], nearest["y"], player_x, player_y)
                if l_dist:
                    active_lasers.append({
                        "start": (player_x, player_y),
                        "end": (player_x + (lx / l_dist) * 1000, player_y + (ly / l_dist) * 1000),
                        "timer": laser_duration,
                        "dir_x": lx / l_dist,
                        "dir_y": ly / l_dist,
                    })
            next_laser_time = current_time + laser_cooldown

        for enemy in all_targets():
            dx, dy = player_x - enemy["x"], player_y - enemy["y"]
            dist = distance(enemy["x"], enemy["y"], player_x, player_y)
            if dist:
                enemy["x"] += (dx / dist) * enemy["speed"]
                enemy["y"] += (dy / dist) * enemy["speed"]

        removed = []
        targets = all_targets()
        for i in range(orbit_knives_count):
            angle = knife_angle + (i * (2 * math.pi / orbit_knives_count))
            kx = player_x + math.cos(angle) * knife_orbit_distance
            ky = player_y + math.sin(angle) * knife_orbit_distance
            for target in targets[:]:
                if target in removed:
                    continue
                if distance(target["x"], target["y"], kx, ky) < knife_radius + target["radius"]:
                    if damage_target(target, 1):
                        removed.append(target)

        for laser in active_lasers:
            for target in all_targets():
                if target in removed:
                    continue
                vx, vy = target["x"] - player_x, target["y"] - player_y
                dot = vx * laser["dir_x"] + vy * laser["dir_y"]
                if dot > 0:
                    px = player_x + laser["dir_x"] * dot
                    py = player_y + laser["dir_y"] * dot
                    if distance(target["x"], target["y"], px, py) < target["radius"] + 15:
                        if damage_target(target, 3):
                            removed.append(target)

        bullets_to_remove = []
        for bullet in bullets[:]:
            bullet["x"] += bullet["dx"] * bullet_speed
            bullet["y"] += bullet["dy"] * bullet_speed
            for target in all_targets():
                if target in removed:
                    continue
                if distance(target["x"], target["y"], bullet["x"], bullet["y"]) < bullet_radius + target["radius"]:
                    bullets_to_remove.append(bullet)
                    if damage_target(target, 1):
                        removed.append(target)
                    break

        enemies = [enemy for enemy in enemies if enemy not in removed]
        bullets = [
            bullet for bullet in bullets
            if 0 <= bullet["x"] <= SCREEN_WIDTH
            and 0 <= bullet["y"] <= SCREEN_HEIGHT
            and bullet not in bullets_to_remove
        ]

        for laser in active_lasers:
            laser["timer"] -= 1
        active_lasers = [laser for laser in active_lasers if laser["timer"] > 0]

        if current_time > invincible_time:
            for target in all_targets():
                if distance(target["x"], target["y"], player_x, player_y) < player_radius + target["radius"]:
                    damage = target.get("touch_damage", 20)
                    player_hp -= damage
                    invincible_time = current_time + 550
                    if player_hp <= 0:
                        player_hp = 0
                        game_state = "GAMEOVER"
                        high_score["max_stage"] = max(high_score["max_stage"], current_stage)
                        high_score["max_level"] = max(high_score["max_level"], player_level)
                        high_score["max_kills"] = max(high_score["max_kills"], total_kills)
                        high_score["max_time"] = max(high_score["max_time"], stage_elapsed)
                    break

        coins_to_remove = []
        for coin in coins:
            if distance(coin["x"], coin["y"], player_x, player_y) < player_radius + 8:
                player_coins += coin["value"]
                coins_to_remove.append(coin)
        coins = [coin for coin in coins if coin not in coins_to_remove]

        chests_to_remove = []
        for chest in chests:
            if distance(chest["x"], chest["y"], player_x, player_y) < player_radius + 12:
                chests_to_remove.append(chest)
                chest_message_timer = current_time + 2000
                roll = random.random()
                if roll < 0.45:
                    bonus_gold = random.randint(18, 32)
                    player_coins += bonus_gold
                    chest_message = f"Golden chest: +{bonus_gold} coins!"
                elif roll < 0.75:
                    player_max_hp += 15
                    player_hp = min(player_max_hp, player_hp + 35)
                    chest_message = "Golden chest: Max HP +15!"
                elif orbit_knives_count < 6:
                    orbit_knives_count += 1
                    chest_message = "Golden chest: Orbit knife +1!"
                else:
                    player_speed += 1
                    chest_message = "Golden chest: Move speed +1!"
        chests = [chest for chest in chests if chest not in chests_to_remove]

        xp_to_remove = []
        for gem in xp_gems:
            if distance(gem["x"], gem["y"], player_x, player_y) < player_radius + 6:
                xp_to_remove.append(gem)
                player_xp += gem["value"]
                if player_xp >= player_xp_needed:
                    player_xp -= player_xp_needed
                    player_level += 1
                    player_xp_needed = int(player_xp_needed * 1.35)
                    current_upgrade_choices = generate_level_up_choices()
                    level_up_start_time = current_time
                    game_state = "LEVEL_UP"
                    break
        xp_gems = [gem for gem in xp_gems if gem not in xp_to_remove]

        if stage_elapsed >= STAGE_SECONDS and not stage_clear_bonus_paid:
            finish_stage()

    screen.fill(BLACK)
    if game_state == "MENU":
        draw_menu()
    elif game_state == "ACHIEVEMENTS":
        draw_records()
    elif game_state in ["GAME", "LEVEL_UP", "SHOP", "GAMEOVER"]:
        draw_world()
        draw_hud()
        if game_state == "LEVEL_UP":
            draw_level_up()
        elif game_state == "SHOP":
            draw_shop()
        elif game_state == "GAMEOVER":
            draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
