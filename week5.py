import pygame
import math
import os
import sys
import random

# 1. 초기화
pygame.init()
pygame.mixer.init() # 사운드 출력을 위한 믹서 초기화
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard: Fireball Mastery")
clock = pygame.time.Clock()

# 내부 서피스 (흔들림 효과용)
display_surface = pygame.Surface((WIDTH, HEIGHT))

font = pygame.font.SysFont("arial", 18, bold=True)
small_font = pygame.font.SysFont("arial", 14, bold=True)
large_font = pygame.font.SysFont("arial", 40, bold=True)
title_font = pygame.font.SysFont("arial", 50, bold=True)

# --- [설정 및 밸런스] ---
COLUMNS = 6
BRICK_W = 60
BRICK_H = 30
GAP = 5
SIDE_MARGIN = (WIDTH - (BRICK_W * COLUMNS + GAP * (COLUMNS - 1))) // 2

BALL_GAIN_RATE = 1
HP_MULTIPLIER = 1.2
IRON_HP_MULTIPLIER = 2.5
SPAWN_BASE_CHANCE = 0.5
SPAWN_MAX_CHANCE = 0.8
DEADLINE_Y = HEIGHT - 150 

bricks_destroyed = 0
SKILL_THRESHOLD = 20

# --- [파이어볼 및 특수효과 설정] ---
FIREBALL_SPEED = 12
FIREBALL_AOE_W = 160
FIREBALL_AOE_H = 120
shake_intensity = 0

fireball_flying_animation = []
fireball_impact_animation = []

# --- [경로 수정 함수] ---
def get_path(filename):
    if hasattr(sys, 'frozen'):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, "assets", filename)

# --- [에셋 로드] ---
try:
    # 이미지 로드
    for i in range(6):
        f_img = pygame.image.load(get_path(f"img__{i}.png")).convert_alpha()
        fireball_flying_animation.append(pygame.transform.scale(f_img, (60, 60)))
        i_img = pygame.image.load(get_path(f"img_{i}.png")).convert_alpha()
        fireball_impact_animation.append(pygame.transform.scale(i_img, (180, 180)))
    
    # 사운드 로드
    hit_sound = pygame.mixer.Sound(get_path("MP_Jab.mp3"))
    hit_sound.set_volume(0.4) 
    
    # [추가] 파이어볼 폭발 사운드 로드
    explosion_sound = pygame.mixer.Sound(get_path("MP_Shotgun Old School.mp3"))
    explosion_sound.set_volume(0.6) # 폭발음이므로 조금 더 크게 설정
    
except Exception as e:
    print(f"에셋 로드 실패 (assets 폴더를 확인하세요): {e}")

CHAR_SIZE = 225  
idle_frames = []
try:
    sheet = pygame.image.load(get_path('Idle.png')).convert_alpha()
    f_w = sheet.get_width() // 6
    idle_frames = [pygame.transform.scale(sheet.subsurface(i*f_w, 0, f_w, sheet.get_height()), (CHAR_SIZE, CHAR_SIZE)) for i in range(6)]
except:
    idle_frames = [pygame.Surface((CHAR_SIZE, CHAR_SIZE), pygame.SRCALPHA) for _ in range(6)]

# --- [게임 객체 및 로직] ---
bricks = []
balls = []
projectiles = []
impacts = []

def is_space_empty(rect):
    for br in bricks:
        if rect.colliderect(br["rect"].inflate(-4, -4)): return False
    return True

def spawn_bricks(round_num):
    chance = min(SPAWN_MAX_CHANCE, SPAWN_BASE_CHANCE + (round_num * 0.015))
    for i in range(COLUMNS):
        if random.random() < chance:
            x_pos = SIDE_MARGIN + i * (BRICK_W + GAP)
            rect = pygame.Rect(x_pos, 80, BRICK_W, BRICK_H)
            if is_space_empty(rect):
                rv = random.random()
                if rv < 0.15: b_type, color, hp = "iron", (130, 130, 130), int(round_num * IRON_HP_MULTIPLIER)
                elif rv < 0.30: b_type, color, hp = "multiply", (180, 100, 255), int(round_num * 0.9)
                else: b_type, color, hp = "normal", (220, 60, 60), int(round_num * HP_MULTIPLIER)
                bricks.append({"rect": rect, "hp": max(1, hp), "type": b_type, "color": color})

def spawn_clones(parent_brick):
    offsets = [(-(BRICK_W + GAP), 0), (BRICK_W + GAP, 0), (0, -(BRICK_H + GAP)), (0, BRICK_H + GAP)]
    random.shuffle(offsets)
    spawned = 0
    for dx, dy in offsets:
        if spawned >= 2: break
        new_rect = parent_brick["rect"].move(dx, dy)
        if SIDE_MARGIN <= new_rect.x <= WIDTH - BRICK_W and 40 <= new_rect.y < DEADLINE_Y:
            if is_space_empty(new_rect):
                bricks.append({"rect": new_rect, "hp": max(1, int(parent_brick["hp"] * 0.5)), "type": "clone", "color": (140, 70, 200)})
                spawned += 1

def destroy_brick(br):
    global bricks_destroyed
    if br["type"] == "multiply": spawn_clones(br)
    bricks.remove(br)
    if not skill_slots["FIRE"]:
        bricks_destroyed += 1
        if bricks_destroyed >= SKILL_THRESHOLD:
            skill_slots["FIRE"] = True
            bricks_destroyed = 0

def launch_fireball(target_pos):
    start_pos = [WIDTH // 2, DEADLINE_Y]
    dx = target_pos[0] - start_pos[0]
    dy = target_pos[1] - start_pos[1]
    dist = math.hypot(dx, dy) or 1
    projectiles.append({
        "pos": start_pos,
        "vel": [(dx/dist) * FIREBALL_SPEED, (dy/dist) * FIREBALL_SPEED],
        "target": target_pos,
        "angle": math.degrees(math.atan2(-dy, dx)),
        "frame": 0, "timer": 0
    })

def create_impact(pos):
    global shake_intensity
    # [추가] 파이어볼 폭발 사운드 재생
    try: explosion_sound.play()
    except: pass

    impacts.append({"pos": pos, "frame": 0, "timer": pygame.time.get_ticks()})
    shake_intensity = 12
    aoe_rect = pygame.Rect(0, 0, FIREBALL_AOE_W, FIREBALL_AOE_H)
    aoe_rect.center = pos
    for br in bricks[:]:
        if aoe_rect.colliderect(br["rect"]):
            destroy_brick(br)

# --- [초기 세팅] ---
round_count = 1
ball_count = 5
balls_to_fire = 0
last_fire_time = 0
fire_interval = 60
current_angle = -math.pi / 2
rotate_speed = 0.05
game_state = "START" 
skill_slots = {"FIRE": True}
FIRE_Y = DEADLINE_Y 

spawn_bricks(round_count)
anim_index, anim_timer = 0, 0
running = True

while running:
    dt = clock.tick(60)
    current_time = pygame.time.get_ticks()
    display_surface.fill((25, 25, 35))
    m_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "START":
                if event.key == pygame.K_SPACE: game_state = "AIMING"
            elif game_state == "AIMING":
                if event.key == pygame.K_SPACE:
                    game_state = "FIRING"
                    balls_to_fire = ball_count
                if event.key == pygame.K_1 and skill_slots["FIRE"]:
                    game_state = "FIREBALL_TARGETING"
            elif game_state == "FIREBALL_TARGETING" and event.key == pygame.K_1:
                game_state = "AIMING"
            if game_state == "GAMEOVER" and event.key == pygame.K_r:
                bricks, balls, projectiles, impacts, round_count, ball_count, bricks_destroyed = [], [], [], [], 1, 5, 0
                skill_slots = {"FIRE": True}; spawn_bricks(round_count); game_state = "AIMING"

        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "FIREBALL_TARGETING":
            launch_fireball(event.pos)
            skill_slots["FIRE"] = False
            game_state = "AIMING"

    # 업데이트
    if game_state != "START":
        if shake_intensity > 0: shake_intensity -= 1
        for p in projectiles[:]:
            p["pos"][0] += p["vel"][0]; p["pos"][1] += p["vel"][1]
            p["timer"] += dt
            if p["timer"] > 60: p["frame"] = (p["frame"] + 1) % 6; p["timer"] = 0
            if math.hypot(p["pos"][0] - p["target"][0], p["pos"][1] - p["target"][1]) < 15:
                create_impact(p["target"]); projectiles.remove(p)
        for imp in impacts[:]:
            if current_time - imp["timer"] > 80:
                imp["frame"] += 1; imp["timer"] = current_time
                if imp["frame"] >= 6: impacts.remove(imp)
        if game_state == "FIRING" and balls_to_fire > 0:
            if current_time - last_fire_time > fire_interval:
                dx, dy = math.cos(current_angle) * 8, math.sin(current_angle) * 8
                balls.append({"pos": [WIDTH // 2, FIRE_Y], "vel": [dx, dy]})
                balls_to_fire -= 1; last_fire_time = current_time
            if balls_to_fire == 0: game_state = "WAITING"
        
        for b in balls[:]:
            b["pos"][0] += b["vel"][0]; b["pos"][1] += b["vel"][1]
            if b["pos"][0] <= 5 or b["pos"][0] >= WIDTH - 5: b["vel"][0] *= -1
            if b["pos"][1] <= 5: b["vel"][1] *= -1
            if b["pos"][1] >= HEIGHT: balls.remove(b)
            ball_r = pygame.Rect(b["pos"][0]-4, b["pos"][1]-4, 8, 8)
            for br in bricks[:]:
                if ball_r.colliderect(br["rect"]):
                    if abs(ball_r.centerx - br["rect"].centerx) > abs(ball_r.centery - br["rect"].centery): b["vel"][0] *= -1
                    else: b["vel"][1] *= -1
                    
                    # 일반 공 타격 사운드
                    try: hit_sound.play()
                    except: pass
                    
                    br["hp"] -= 1
                    if br["hp"] <= 0: destroy_brick(br)
                    break

        if game_state == "WAITING" and len(balls) == 0:
            round_count += 1; ball_count += BALL_GAIN_RATE
            for br in bricks:
                br["rect"].y += BRICK_H + GAP
                if br["rect"].y + br["rect"].height >= DEADLINE_Y: game_state = "GAMEOVER"
            if game_state != "GAMEOVER": spawn_bricks(round_count); game_state = "AIMING"
        if game_state == "AIMING":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: current_angle -= rotate_speed
            if keys[pygame.K_RIGHT]: current_angle += rotate_speed
            current_angle = max(-math.pi + 0.2, min(-0.2, current_angle))

    # 그리기
    anim_timer += dt
    if anim_timer >= 100: anim_timer, anim_index = 0, (anim_index + 1) % 6
    if game_state == "START":
        title_txt = title_font.render("WIZARD BALL", True, (255, 200, 50))
        start_txt = font.render("PRESS SPACE TO START", True, (255, 255, 255))
        display_surface.blit(idle_frames[anim_index], idle_frames[anim_index].get_rect(center=(WIDTH//2, HEIGHT//2)))
        display_surface.blit(title_txt, (WIDTH//2 - title_txt.get_width()//2, HEIGHT//2 - 150))
        if (current_time // 500) % 2 == 0:
            display_surface.blit(start_txt, (WIDTH//2 - start_txt.get_width()//2, HEIGHT//2 + 100))
    else:
        display_surface.blit(idle_frames[anim_index], idle_frames[anim_index].get_rect(center=(WIDTH//2, FIRE_Y + 70)))
        if game_state == "AIMING":
            ep = (WIDTH//2 + math.cos(current_angle)*80, FIRE_Y + math.sin(current_angle)*80)
            pygame.draw.line(display_surface, (255, 255, 0), (WIDTH//2, FIRE_Y), ep, 2)
        elif game_state == "FIREBALL_TARGETING":
            target_rect = pygame.Rect(0, 0, FIREBALL_AOE_W, FIREBALL_AOE_H); target_rect.center = m_pos
            pygame.draw.ellipse(display_surface, (255, 100, 0), target_rect, 2)
        for br in bricks:
            pygame.draw.rect(display_surface, br["color"], br["rect"], border_radius=4)
            txt = font.render(str(br["hp"]), True, (255, 255, 255))
            display_surface.blit(txt, (br["rect"].centerx - txt.get_width()//2, br["rect"].centery - txt.get_height()//2))
        for b in balls: pygame.draw.circle(display_surface, (255, 255, 255), (int(b["pos"][0]), int(b["pos"][1])), 5)
        for p in projectiles:
            img = fireball_flying_animation[p["frame"]]; rot_img = pygame.transform.rotate(img, p["angle"])
            display_surface.blit(rot_img, rot_img.get_rect(center=p["pos"]))
        for imp in impacts:
            img = fireball_impact_animation[imp["frame"]]
            display_surface.blit(img, img.get_rect(center=imp["pos"]))
        pygame.draw.line(display_surface, (255, 50, 50), (0, DEADLINE_Y), (WIDTH, DEADLINE_Y), 2)
        
        skill_r = pygame.Rect(10, HEIGHT - 45, 40, 40)
        pygame.draw.rect(display_surface, (60, 60, 70), skill_r, border_radius=5)
        if skill_slots["FIRE"]:
            pygame.draw.rect(display_surface, (220, 60, 60), skill_r.inflate(-10, -10), border_radius=3)
            display_surface.blit(font.render("1", True, (255, 255, 255)), (skill_r.x+2, skill_r.y+2))
        else:
            status_txt = small_font.render(str(SKILL_THRESHOLD - bricks_destroyed), True, (200, 200, 200))
            display_surface.blit(status_txt, (skill_r.centerx - status_txt.get_width()//2, skill_r.centery - status_txt.get_height()//2))

        display_surface.blit(font.render(f"ROUND: {round_count}  BALLS: {ball_count}", True, (255, 255, 255)), (10, 10))
        if game_state == "GAMEOVER":
            display_surface.blit(large_font.render("GAME OVER", True, (255, 50, 50)), (WIDTH//2-100, HEIGHT//2-50))

    # 화면 표시
    render_offset = [random.randint(-shake_intensity, shake_intensity), random.randint(-shake_intensity, shake_intensity)] if shake_intensity > 0 else [0, 0]
    screen.fill((0, 0, 0))
    screen.blit(display_surface, render_offset)
    pygame.display.flip()

pygame.quit()
