# 太空生存戰
import pygame
import random 
import os
import math

# 獲取當前腳本所在目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FPS = 60 
WIDTH = 500
HEIGHT = 600

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# 遊戲初始化 and 創建視窗
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("第一個遊戲")
clock = pygame.time.Clock()

# 載入圖片
background_img = pygame.image.load(os.path.join(BASE_DIR, "img", "background.png")).convert()
player_img = pygame.image.load(os.path.join(BASE_DIR, "img", "player.png")).convert()
player_mini_img = pygame.transform.scale(player_img, (25, 19))
player_mini_img.set_colorkey(BLACK)
pygame.display.set_icon(player_mini_img)
bullet_img = pygame.image.load(os.path.join(BASE_DIR, "img", "bullet.png")).convert()
rock_imgs = []
for i in range(7):
    rock_imgs.append(pygame.image.load(os.path.join(BASE_DIR, "img", f"rock{i}.png")).convert())
expl_anim = {}
expl_anim['lg'] = []
expl_anim['sm'] = []
expl_anim['player'] = []
for i in range(9):
    expl_img = pygame.image.load(os.path.join(BASE_DIR, "img", f"expl{i}.png")).convert()
    expl_img.set_colorkey(BLACK)
    expl_anim['lg'].append(pygame.transform.scale(expl_img, (75, 75)))
    expl_anim['sm'].append(pygame.transform.scale(expl_img, (30, 30)))
    player_expl_img = pygame.image.load(os.path.join(BASE_DIR, "img", f"player_expl{i}.png")).convert()
    player_expl_img.set_colorkey(BLACK)
    expl_anim['player'].append(player_expl_img)
power_imgs = {}
power_imgs['shield'] = pygame.image.load(os.path.join(BASE_DIR, "img", "shield.png")).convert()
power_imgs['gun'] = pygame.image.load(os.path.join(BASE_DIR, "img", "gun.png")).convert()

# 載入金幣圖片
coin_img = pygame.image.load(os.path.join(BASE_DIR, "img", "coin.png")).convert()
coin_img = pygame.transform.scale(coin_img, (20, 20))
coin_img.set_colorkey(BLACK)

# 載入飛彈圖片
missile_img = pygame.image.load(os.path.join(BASE_DIR, "img", "missile.png")).convert()
missile_img = pygame.transform.scale(missile_img, (15, 25))
missile_img.set_colorkey(BLACK)

# 載入音樂、音效
shoot_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "shoot.wav"))
gun_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "pow1.wav"))
shield_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "pow0.wav"))
die_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "rumble.ogg"))
expl_sounds = [
    pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "expl0.wav")),
    pygame.mixer.Sound(os.path.join(BASE_DIR, "sound", "expl1.wav"))
]
pygame.mixer.music.load(os.path.join(BASE_DIR, "sound", "background.ogg"))
pygame.mixer.music.set_volume(0.4)

font_name = os.path.join(BASE_DIR, "font.ttf")
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)

def new_rock():
    r = Rock()
    all_sprites.add(r)
    rocks.add(r)

def draw_health(surf, hp, max_hp, x, y):
    if hp < 0:
        hp = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (hp/max_hp)*BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

def draw_lives(surf, lives, img, x, y):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 32*i
        img_rect.y = y
        surf.blit(img, img_rect)

def draw_coins(surf, coins, img, x, y):
    coin_rect = img.get_rect()
    coin_rect.x = x
    coin_rect.y = y
    surf.blit(img, coin_rect)
    draw_text(surf, str(coins), 18, x + 50, y)

def draw_init():
    screen.blit(background_img, (0,0))
    draw_text(screen, '太空生存戰!', 64, WIDTH/2, HEIGHT/4)
    draw_text(screen, '← →移動飛船 空白鍵發射子彈~', 22, WIDTH/2, HEIGHT/2)
    draw_text(screen, '按任意鍵開始遊戲!', 18, WIDTH/2, HEIGHT*3/4)
    pygame.display.update()
    waiting = True
    while waiting:
        clock.tick(FPS)
        # 取得輸入
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            elif event.type == pygame.KEYDOWN:
                waiting = False
                return False

class Player(pygame.sprite.Sprite):
    def __init__(self, max_health_bonus=0, permanent_gun_level=1):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.radius = 20
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 8
        self.health = 100 + max_health_bonus
        self.max_health = 100 + max_health_bonus
        self.lives = 3
        self.hidden = False
        self.hide_time = 0
        self.gun = permanent_gun_level
        self.gun_time = 0
        self.permanent_gun_level = permanent_gun_level

    def update(self):
        now = pygame.time.get_ticks()
        # 升級超過永久等級的武器會在5秒後降回永久等級
        if self.gun > self.permanent_gun_level and now - self.gun_time > 5000:
            self.gun = self.permanent_gun_level
            self.gun_time = now

        if self.hidden and now - self.hide_time > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_RIGHT]:
            self.rect.x += self.speedx
        if key_pressed[pygame.K_LEFT]:
            self.rect.x -= self.speedx

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        if not(self.hidden):
            if self.gun == 1:
                # 1級：單發中間
                bullet = Bullet(self.rect.centerx, self.rect.top, angle=0)
                all_sprites.add(bullet)
                bullets.add(bullet)
                shoot_sound.play()
            elif self.gun == 2:
                # 2級：雙槍 - 左右兩側垂直往上
                bullet1 = Bullet(self.rect.left + 10, self.rect.top, angle=0)
                bullet2 = Bullet(self.rect.right - 10, self.rect.top, angle=0)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
                shoot_sound.play()
            elif self.gun == 3:
                # 3級：三槍 - 中間正負60度角
                bullet1 = Bullet(self.rect.left + 10, self.rect.top, angle=-60)
                bullet2 = Bullet(self.rect.centerx, self.rect.top - 5, angle=0)
                bullet3 = Bullet(self.rect.right - 10, self.rect.top, angle=60)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                all_sprites.add(bullet3)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(bullet3)
                shoot_sound.play()
            elif self.gun == 4:
                # 4級：四槍 - 中間兩道直射 + 兩側60度
                bullet1 = Bullet(self.rect.centerx - 8, self.rect.top - 5, angle=-30)
                bullet2 = Bullet(self.rect.centerx + 8, self.rect.top - 5, angle=30)
                bullet3 = Bullet(self.rect.left + 10, self.rect.top, angle=-60)
                bullet4 = Bullet(self.rect.right - 10, self.rect.top, angle=60)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                all_sprites.add(bullet3)
                all_sprites.add(bullet4)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(bullet3)
                bullets.add(bullet4)
                shoot_sound.play()
            elif self.gun >= 5:
                # 5級：五槍 - 發射追蹤飛彈（有冷卻時間）
                now = pygame.time.get_ticks()
                if not hasattr(self, 'missile_cooldown'):
                    self.missile_cooldown = 0
                    self.missile_shots = 0
                
                # 冷卻時間檢查：5秒或30次攻擊
                if now - self.missile_cooldown > 5000 or self.missile_shots >= 30:
                    self.missile_cooldown = now
                    self.missile_shots = 0
                
                # 只在冷卻完成後發射飛彈
                if self.missile_shots == 0 or (now - self.missile_cooldown < 5000 and self.missile_shots < 30):
                    # 發射單發追蹤飛彈
                    missile = Missile(self.rect.centerx, self.rect.top - 10, rocks)
                    all_sprites.add(missile)
                    missiles.add(missile)
                    self.missile_shots += 1
                    shoot_sound.play()
                else:
                    # 冷卻中則改發普通子彈
                    bullet1 = Bullet(self.rect.centerx, self.rect.top - 10, angle=0)
                    bullet2 = Bullet(self.rect.centerx - 12, self.rect.top - 5, angle=-45)
                    bullet3 = Bullet(self.rect.centerx + 12, self.rect.top - 5, angle=45)
                    bullet4 = Bullet(self.rect.left + 10, self.rect.top, angle=-80)
                    bullet5 = Bullet(self.rect.right - 10, self.rect.top, angle=80)
                    all_sprites.add(bullet1)
                    all_sprites.add(bullet2)
                    all_sprites.add(bullet3)
                    all_sprites.add(bullet4)
                    all_sprites.add(bullet5)
                    bullets.add(bullet1)
                    bullets.add(bullet2)
                    bullets.add(bullet3)
                    bullets.add(bullet4)
                    bullets.add(bullet5)
                    shoot_sound.play()

    def hide(self):
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH/2, HEIGHT+500)

    def gunup(self):
        self.gun += 1
        self.gun_time = pygame.time.get_ticks()

class Rock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_ori = random.choice(rock_imgs) 
        self.image_ori.set_colorkey(BLACK)
        self.image = self.image_ori.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.85 / 2)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-180, -100)
        self.speedy = random.randrange(2, 5)
        self.speedx = random.randrange(-3, 3)
        self.total_degree = 0
        self.rot_degree = random.randrange(-3, 3)

    def rotate(self):
        self.total_degree += self.rot_degree
        self.total_degree = self.total_degree % 360
        self.image = pygame.transform.rotate(self.image_ori, self.total_degree)
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center

    def update(self):
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(2, 10)
            self.speedx = random.randrange(-3, 3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        
        # 根據角度計算速度（角度為0時向上，正值向右傾斜）
        self.speedy = -10 * math.cos(math.radians(angle))
        self.speedx = 10 * math.sin(math.radians(angle))

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # 如果子彈超出螢幕則刪除
        if self.rect.bottom < 0 or self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_group):
        pygame.sprite.Sprite.__init__(self)
        self.image = missile_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.target_group = target_group
        self.current_target = None
        self.speed = 8
        self.lifetime = 0
        self.MAX_LIFETIME = 300  # 5秒（假設FPS=60）

    def find_nearest_target(self):
        """尋找最近的隕石作為目標"""
        nearest = None
        nearest_dist = float('inf')
        
        for rock in self.target_group:
            dist = math.sqrt((rock.rect.centerx - self.rect.centerx)**2 + 
                            (rock.rect.centery - self.rect.centery)**2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = rock
        
        return nearest

    def update(self):
        self.lifetime += 1
        
        # 如果目前的目標已死亡或不存在，尋找新目標
        if not self.current_target or not self.current_target.alive():
            self.current_target = self.find_nearest_target()
        
        if self.current_target:
            # 追蹤目標
            dx = self.current_target.rect.centerx - self.rect.centerx
            dy = self.current_target.rect.centery - self.rect.centery
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
        else:
            # 如果沒有目標，直接往上飛
            self.rect.y -= self.speed
        
        # 超時自動刪除
        if self.lifetime >= self.MAX_LIFETIME:
            self.kill()
        
        # 超出螢幕刪除
        if self.rect.bottom < 0 or self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top > HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = expl_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(expl_anim[self.size]):
                self.kill()
            else:
                self.image = expl_anim[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center

class Power(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = power_imgs[self.type]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


pygame.mixer.music.play(-1)

# =========================================================
# 【新增：關卡計時與暫停相關變數】
# =========================================================
game_state = "playing"     # "playing" (進行中) 或 "select_item" (選道具畫面)
is_paused = False          # 是否處於 ESC 暫停選單
current_level = 1          # 當前關卡數
LEVEL_DURATION = 30        # 每關秒數

start_time = 0             # 關卡計時錨點
total_paused_time = 0      # 累積暫停時間
pause_start_tick = 0       # 按下暫停的瞬間時間點

# 【新增：永久升級狀態】
permanent_max_health_bonus = 0  # 永久最大血量增加
permanent_gun_level = 1  # 永久武器等級 (1-5)
# =========================================================

# 遊戲迴圈
show_init = True
running = True
while running:
    if show_init:
        close = draw_init()
        if close:
            break
        show_init = False
        all_sprites = pygame.sprite.Group()
        rocks = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        missiles = pygame.sprite.Group()
        powers = pygame.sprite.Group()
        player = Player(max_health_bonus=permanent_max_health_bonus, permanent_gun_level=permanent_gun_level)
        all_sprites.add(player)
        for i in range(8):
            new_rock()
        score = 0
        coins = 0  # 初始化金幣
        
        # 遊戲真正開始時，初始化計時錨點
        game_state = "playing"
        is_paused = False
        current_level = 1
        start_time = pygame.time.get_ticks()
        total_paused_time = 0
    
    clock.tick(FPS)
    
    # 1. 取得輸入事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # 只有在遊戲進行中，按下 ESC 才能開關暫停
            if event.key == pygame.K_ESCAPE and game_state == "playing":
                if not is_paused:
                    is_paused = True
                    pause_start_tick = pygame.time.get_ticks()
                    pygame.mixer.music.pause() # 暫停背景音樂
                else:
                    is_paused = False
                    total_paused_time += (pygame.time.get_ticks() - pause_start_tick)
                    pygame.mixer.music.unpause() # 恢復背景音樂
            
            # 空白鍵發射子彈（必須在沒暫停且正在玩的狀態）
            if event.key == pygame.K_SPACE:
                if game_state == "playing" and not is_paused:
                    player.shoot()
                # 如果在選道具畫面，按空白鍵模擬選擇道具並進入下一關
                elif game_state == "select_item":
                    current_level += 1
                    game_state = "playing"
                    # 重要：重置下一關的計時錨點與暫停累積時間
                    start_time = pygame.time.get_ticks()
                    total_paused_time = 0
                    # 清空場上的隕石與寶物，讓下一關重新生成（保持畫面乾淨）
                    for rock in rocks:
                        rock.kill()
                    for pow in powers:
                        pow.kill()
                    for missile in missiles:
                        missile.kill()
                    for i in range(8):
                        new_rock()
            
            # 購買道具（只在select_item狀態有效）
            if game_state == "select_item":
                if event.key == pygame.K_1:  # 購買防護罩
                    if coins >= 50:
                        coins -= 50
                        permanent_max_health_bonus += 20
                        player.max_health = 100 + permanent_max_health_bonus
                        player.health = player.max_health
                        shield_sound.play()
                elif event.key == pygame.K_2:  # 升級到三槍
                    if coins >= 80 and permanent_gun_level < 3:
                        coins -= 80
                        permanent_gun_level = 3
                        player.permanent_gun_level = 3
                        player.gun = 3
                        player.gun_time = pygame.time.get_ticks()
                        gun_sound.play()
                elif event.key == pygame.K_3:  # 升級到四槍
                    if coins >= 120 and permanent_gun_level < 4:
                        coins -= 120
                        permanent_gun_level = 4
                        player.permanent_gun_level = 4
                        player.gun = 4
                        player.gun_time = pygame.time.get_ticks()
                        gun_sound.play()
                elif event.key == pygame.K_4:  # 升級到五槍
                    if coins >= 200 and permanent_gun_level < 5:
                        coins -= 200
                        permanent_gun_level = 5
                        player.permanent_gun_level = 5
                        player.gun = 5
                        player.gun_time = pygame.time.get_ticks()
                        gun_sound.play()

    # 2. 遊戲狀態判斷與更新
    if is_paused:
        # 暫停狀態：不更新任何精靈的位置（畫面定格）
        pass
        
    elif game_state == "playing":
        # 正常遊戲進行中：更新精靈與碰撞偵測
        all_sprites.update()
        
        # 判斷石頭 子彈相撞
        hits = pygame.sprite.groupcollide(rocks, bullets, True, True)
        for hit in hits:
            random.choice(expl_sounds).play()
            score += hit.radius
            coins += max(1, hit.radius // 2)  # 獲得金幣為隕石大小的一半
            expl = Explosion(hit.rect.center, 'lg')
            all_sprites.add(expl)
            if random.random() > 0.9:
                pow = Power(hit.rect.center)
                all_sprites.add(pow)
                powers.add(pow)
            new_rock()

        # 判斷飛彈 石頭相撞 - 更大的爆炸半徑
        hits = pygame.sprite.groupcollide(rocks, missiles, True, True)
        for hit in hits:
            random.choice(expl_sounds).play()
            score += hit.radius * 2  # 飛彈擊中得分加倍
            coins += max(2, hit.radius)  # 飛彈擊中金幣加倍
            
            # 飛彈爆炸：更大的爆炸並清除周圍隕石
            expl = Explosion(hit.rect.center, 'lg')
            all_sprites.add(expl)
            
            # 清除爆炸半徑內的其他隕石
            blast_radius = 80
            for rock in rocks:
                dist = math.sqrt((rock.rect.centerx - hit.rect.centerx)**2 + 
                                (rock.rect.centery - hit.rect.centery)**2)
                if dist < blast_radius:
                    rock.kill()
                    # 只在殺死額外隕石時獲得一部分分數
                    score += rock.radius
                    coins += max(1, rock.radius // 3)
            
            if random.random() > 0.8:
                pow = Power(hit.rect.center)
                all_sprites.add(pow)
                powers.add(pow)
            new_rock()

        # 判斷石頭 飛船相撞
        hits = pygame.sprite.spritecollide(player, rocks, True, pygame.sprite.collide_circle)
        for hit in hits:
            new_rock()
            player.health -= hit.radius * 2
            expl = Explosion(hit.rect.center, 'sm')
            all_sprites.add(expl)
            if player.health <= 0:
                death_expl = Explosion(player.rect.center, 'player')
                all_sprites.add(death_expl)
                die_sound.play()
                player.lives -= 1
                player.health = player.max_health
                player.hide()
                
        # 判斷寶物 飛船相撞
        hits = pygame.sprite.spritecollide(player, powers, True)
        for hit in hits:
            if hit.type == 'shield':
                player.health += 20
                if player.health > player.max_health:
                    player.health = player.max_health
                shield_sound.play()
            elif hit.type == 'gun':
                player.gunup()
                gun_sound.play()

        if player.lives == 0 and not(death_expl.alive()):
            show_init = True
            
        # -------------------------------------------------
        # 【新增：關卡時間與結束判斷】
        # -------------------------------------------------
        current_tick = pygame.time.get_ticks()
        passed_seconds = (current_tick - start_time - total_paused_time) / 1000
        remaining_time = max(0, LEVEL_DURATION - passed_seconds)
        
        # 檢查 30 秒是否到了
        if passed_seconds >= LEVEL_DURATION:
            game_state = "select_item"

    elif game_state == "select_item":
        # 選道具狀態：精靈不更新，畫面定格
        pass

    # 3. 畫面顯示與繪製
    screen.fill(BLACK)
    screen.blit(background_img, (0,0))
    all_sprites.draw(screen)
    
    # 繪製原本的UI
    draw_text(screen, str(score), 18, WIDTH/2, 10)
    draw_health(screen, player.health, player.max_health, 5, 15)
    draw_lives(screen, player.lives, player_mini_img, WIDTH - 100, 15)
    draw_coins(screen, coins, coin_img, 5, 40)
    
    # -------------------------------------------------
    # 【新增：疊加繪製倒數計時、暫停與結算文字】
    # -------------------------------------------------
    if is_paused:
        # 疊加灰底與暫停文字
        pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 150)) # 半透明黑底
        screen.blit(pause_surface, (0, 0))
        draw_text(screen, "暫停中", 40, WIDTH/2, HEIGHT/2 - 40)
        draw_text(screen, "按 ESC 鍵恢復遊戲", 20, WIDTH/2, HEIGHT/2 + 20)
        
    elif game_state == "playing":
        # 疊加顯示當前關卡、倒數計時和武器等級
        draw_text(screen, f"關卡: {current_level}", 18, 50, 65)
        draw_text(screen, f"時間: {remaining_time:.1f}s", 18, WIDTH/2, 40)
        
        # 顯示當前武器等級
        weapon_names = {1: "單槍", 2: "雙槍", 3: "三槍", 4: "四槍", 5: "五槍"}
        weapon_name = weapon_names.get(player.gun, "未知")
        draw_text(screen, f"武器: {weapon_name}", 16, WIDTH - 120, 65)
        
    elif game_state == "select_item":
        # 疊加半透明黑底與過關選擇畫面
        clear_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        clear_surface.fill((0, 0, 0, 180))
        screen.blit(clear_surface, (0, 0))
        
        draw_text(screen, f"第 {current_level} 關 突破！", 36, WIDTH/2, HEIGHT/3 - 40)
        
        # 顯示金幣
        draw_text(screen, "你的金幣：", 18, WIDTH/2 - 70, HEIGHT/3 + 5)
        coin_display_rect = coin_img.get_rect()
        coin_display_rect.x = WIDTH/2 + 5
        coin_display_rect.y = HEIGHT/3 + 5
        screen.blit(coin_img, coin_display_rect)
        draw_text(screen, str(coins), 18, WIDTH/2 + 60, HEIGHT/3 + 3)
        
        # 顯示購買選項
        draw_text(screen, "升級武器系統 (按數字鍵選擇):", 16, WIDTH/2, HEIGHT/2 - 45)
        draw_text(screen, "1. 永久增加血量 (消耗 50 金幣) - +20 HP", 14, WIDTH/2, HEIGHT/2 - 20)
        
        gun_level_2_status = "已擁有" if permanent_gun_level >= 2 else "可購買"
        draw_text(screen, f"2. 三槍模式 (消耗 80 金幣) - {gun_level_2_status}", 14, WIDTH/2, HEIGHT/2 + 2)
        
        gun_level_3_status = "已擁有" if permanent_gun_level >= 4 else "可購買"
        draw_text(screen, f"3. 四槍模式 (消耗 120 金幣) - {gun_level_3_status}", 14, WIDTH/2, HEIGHT/2 + 24)
        
        gun_level_4_status = "已擁有" if permanent_gun_level >= 5 else "可購買"
        draw_text(screen, f"4. 追蹤飛彈系統 (消耗 200 金幣) - {gun_level_4_status}", 14, WIDTH/2, HEIGHT/2 + 46)
        draw_text(screen, "   (冷卻5秒或30次攻擊，爆炸範圍更大)", 12, WIDTH/2, HEIGHT/2 + 62)
        
        draw_text(screen, "按空白鍵不購買，直接進入下一關", 12, WIDTH/2, HEIGHT * 2/3 + 80)
    # -------------------------------------------------

    pygame.display.update()

pygame.quit()