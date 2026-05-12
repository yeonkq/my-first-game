import pygame
import math
import os
import sys
import random

# --- [1. 리소스 경로 설정 함수] ---
def get_path(filename):
    """ PyInstaller 환경과 일반 실행 환경을 모두 지원하는 경로 함수 """
    if hasattr(sys, '_MEIPASS'):
        # exe로 빌드되었을 때 임시 폴더 경로
        base_path = sys._MEIPASS
    else:
        # .py 파일로 실행 중일 때 현재 폴더 경로
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, "assets", filename)

# --- [2. 초기화 및 화면 설정] ---
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 400, 600
# 중요: 이미지를 로드하기 전에 화면(Display)이 반드시 먼저 생성되어야 합니다.
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard: Dungeon Defense")
clock = pygame.time.Clock()

# 내부 서피스 (흔들림 효과용)
display_surface = pygame.Surface((WIDTH, HEIGHT))

# --- [3. 에셋 변수 선언 및 로드 함수] ---
mob_images = {}
fireball_flying_animation = []
fireball_impact_animation = []
idle_frames = []
background_img = pygame.Surface((WIDTH, HEIGHT))
background_img.fill((25, 25, 35))
hit_sound = None
explosion_sound = None

def load_assets():
    global background_img, hit_sound, explosion_sound, idle_frames
    try:
        # 배경 로드
        b_path = get_path("dungeon.png")
        if os.path.exists(b_path):
            background_img = pygame.image.load(b_path).convert()
            background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
            bg_overlay = pygame.Surface((WIDTH, HEIGHT))
            bg_overlay.fill((20, 20, 20))
            background_img.blit(bg_overlay, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

        # 몬스터 로드
        names = ["mob1.png", "mob2.png", "mob3.png", "mob4.png"]
        keys = ["iron", "multiply", "clone", "normal"]
        for k, n in zip(keys, names):
            m_path = get_path(n)
            if os.path.exists(m_path):
                img = pygame.image.load(m_path).convert_alpha()
                mob_images[k] = pygame.transform.scale(img, (60, 45)) # BRICK_W, BRICK_H

        # 애니메이션 로드 (0~5번 프레임)
        for i in range(6):
            f_path = get_path(f"img__{i}.png")
            if os.path.exists(f_path):
                f_img = pygame.image.load(f_path).convert_alpha()
                fireball_flying_animation.append(pygame.transform.scale(f_img, (60, 60)))
            
            i_path = get_path(f"img_{i}.png")
            if os.path.exists(i_path):
                i_img = pygame.image.load(i_path).convert_alpha()
                fireball_impact_animation.append(pygame.transform.scale(i_img, (180, 180)))

        # 캐릭터 Idle 애니메이션
        idle_path = get_path('Idle.png')
        if os.path.exists(idle_path):
            sheet = pygame.image.load(idle_path).convert_alpha()
            f_w = sheet.get_width() // 6
            for i in range(6):
                frame = sheet.subsurface(i*f_w, 0, f_w, sheet.get_height())
                idle_frames.append(pygame.transform.scale(frame, (225, 225)))
        else:
            idle_frames = [pygame.Surface((225, 225), pygame.SRCALPHA) for _ in range(6)]

        # 사운드 로드
        h_sound_path = get_path("MP_Jab.mp3")
        if os.path.exists(h_sound_path):
            hit_sound = pygame.mixer.Sound(h_sound_path)
            
        e_sound_path = get_path("MP_Shotgun Old School.mp3")
        if os.path.exists(e_sound_path):
            explosion_sound = pygame.mixer.Sound(e_sound_path)

    except Exception as e:
        print(f"에셋 로드 중 오류 발생: {e}")

# 화면 설정 직후에 에셋 로드 호출
load_assets()

# --- [4. 게임 설정 및 로직] ---
# 폰트 설정
font = pygame.font.SysFont("arial", 18, bold=True)
small_font = pygame.font.SysFont("arial", 14, bold=True)
large_font = pygame.font.SysFont("arial", 40, bold=True)
title_font = pygame.font.SysFont("arial", 50, bold=True)

# 밸런스 변수
COLUMNS = 6
BRICK_W, BRICK_H, GAP = 60, 45, 5
SIDE_MARGIN = (WIDTH - (BRICK_W * COLUMNS + GAP * (COLUMNS - 1))) // 2
BALL_GAIN_RATE, HP_MULTIPLIER, IRON_HP_MULTIPLIER = 1, 1.2, 2.5
SPAWN_BASE_CHANCE, SPAWN_MAX_CHANCE = 0.5, 0.8
DEADLINE_Y = HEIGHT - 150 
FIREBALL_SPEED, FIREBALL_AOE_W, FIREBALL_AOE_H = 12, 160, 120
SKILL_THRESHOLD = 20

bricks, balls, projectiles, impacts = [], [], [], []
bricks_destroyed, shake_intensity = 0, 0

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
                if rv < 0.15: b_type, hp = "iron", int(round_num * IRON_HP_MULTIPLIER)
                elif rv < 0.30: b_type, hp = "multiply", int(round_num * 0.9)
                else: b_type, hp = "normal", int(round_num * HP_MULTIPLIER)
                bricks.append({"rect": rect, "hp": max(1, hp), "type": b_type})

def destroy_brick(br):
    global bricks_destroyed
    if br["type"] == "multiply":
        offsets = [(-(BRICK_W + GAP), 0), (BRICK_W + GAP, 0), (0, -(BRICK_H + GAP)), (0, BRICK_H + GAP)]
        random.shuffle(offsets)
        spawned = 0
        for dx, dy in offsets:
            if spawned >= 2: break
            new_rect = br["rect"].move(dx, dy)
            if SIDE_MARGIN <= new_rect.x <= WIDTH - BRICK_W and 40 <= new_rect.y < DEADLINE_Y:
                if is_space_empty(new_rect):
                    bricks.append({"rect": new_rect, "hp": max(1, int(br["hp"] * 0.5)), "type": "clone"})
                    spawned += 1
    if br in bricks: bricks.remove(br)
    if not skill_slots["FIRE"]:
        bricks_destroyed += 1
        if bricks_destroyed >= SKILL_THRESHOLD:
            skill_slots["FIRE"], bricks_destroyed = True, 0

def launch_fireball(target_pos):
    start_pos = [WIDTH // 2, DEADLINE_Y]
    dx, dy = target_pos[0] - start_pos[0], target_pos[1] - start_pos[1]
    dist = math.hypot(dx, dy) or 1
    projectiles.append({
        "pos": list(start_pos), "vel": [(dx/dist) * FIREBALL_SPEED, (dy/dist) * FIREBALL_SPEED],
        "target": target_pos, "angle": math.degrees(math.atan2(-dy, dx)), "frame": 0, "timer": 0
    })

def create_impact(pos):
    global shake_intensity
    if explosion_sound: explosion_sound.play()
    impacts.append({"pos": pos, "frame": 0, "timer": pygame.time.get_ticks()})
    shake_intensity = 12
    aoe_rect = pygame.Rect(0, 0, FIREBALL_AOE_W, FIREBALL_AOE_H)
    aoe_rect.center = pos
    for br in bricks[:]:
        if aoe_rect.colliderect(br["rect"]): destroy_brick(br)

# --- [5. 상태 변수 및 게임 루프] ---
round_count, ball_count = 1, 5
balls_to_fire, last_fire_time = 0, 0
fire_interval, current_angle, rotate_speed = 60, -math.pi / 2, 0.05
game_state = "START" 
skill_slots = {"FIRE": True}
FIRE_Y = DEADLINE_Y 
spawn_bricks(round_count)
anim_index, anim_timer = 0, 0
running = True

while running:
    dt = clock.tick(60)
    current_time = pygame.time.get_ticks()
    display_surface.blit(background_img, (0, 0)) 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "START" and event.key == pygame.K_SPACE: game_state = "AIMING"
            elif game_state == "AIMING":
                if event.key == pygame.K_SPACE:
                    game_state, balls_to_fire = "FIRING", ball_count
                if event.key == pygame.K_1 and skill_slots["FIRE"]: game_state = "FIREBALL_TARGETING"
            elif game_state == "FIREBALL_TARGETING" and event.key == pygame.K_1: game_state = "AIMING"
            if game_state == "GAMEOVER" and event.key == pygame.K_r:
                bricks, balls, projectiles, impacts, round_count, ball_count, bricks_destroyed = [], [], [], [], 1, 5, 0
                skill_slots = {"FIRE": True}; spawn_bricks(round_count); game_state = "AIMING"

        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "FIREBALL_TARGETING":
            launch_fireball(event.pos)
            skill_slots["FIRE"], game_state = False, "AIMING"

    # 로직 업데이트
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
                    if hit_sound: hit_sound.play()
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

    # 그리기 로직
    anim_timer += dt
    if anim_timer >= 100: anim_timer, anim_index = 0, (anim_index + 1) % 6
    
    if game_state == "START":
        title_txt = title_font.render("DUNGEON BALL", True, (255, 200, 50))
        display_surface.blit(idle_frames[anim_index], idle_frames[anim_index].get_rect(center=(WIDTH//2, HEIGHT//2)))
        display_surface.blit(title_txt, (WIDTH//2 - title_txt.get_width()//2, HEIGHT//2 - 150))
    else:
        display_surface.blit(idle_frames[anim_index], idle_frames[anim_index].get_rect(center=(WIDTH//2, FIRE_Y + 70)))
        if game_state == "AIMING":
            ep = (WIDTH//2 + math.cos(current_angle)*80, FIRE_Y + math.sin(current_angle)*80)
            pygame.draw.line(display_surface, (255, 255, 0), (WIDTH//2, FIRE_Y), ep, 2)
        elif game_state == "FIREBALL_TARGETING":
            m_pos = pygame.mouse.get_pos()
            target_rect = pygame.Rect(0, 0, FIREBALL_AOE_W, FIREBALL_AOE_H); target_rect.center = m_pos
            pygame.draw.ellipse(display_surface, (255, 100, 0), target_rect, 2)

        for br in bricks:
            img = mob_images.get(br["type"])
            if img: display_surface.blit(img, br["rect"])
            hp_txt = font.render(str(br["hp"]), True, (255, 255, 255))
            display_surface.blit(hp_txt, (br["rect"].centerx - hp_txt.get_width()//2, br["rect"].centery - hp_txt.get_height()//2))

        for b in balls: pygame.draw.circle(display_surface, (255, 255, 255), (int(b["pos"][0]), int(b["pos"][1])), 5)
        for p in projectiles:
            if fireball_flying_animation:
                img = fireball_flying_animation[p["frame"]]
                display_surface.blit(pygame.transform.rotate(img, p["angle"]), img.get_rect(center=p["pos"]))
        for imp in impacts:
            if fireball_impact_animation:
                img = fireball_impact_animation[imp["frame"]]
                display_surface.blit(img, img.get_rect(center=imp["pos"]))
        
        pygame.draw.line(display_surface, (255, 50, 50), (0, DEADLINE_Y), (WIDTH, DEADLINE_Y), 2)
        display_surface.blit(font.render(f"ROUND: {round_count}  BALLS: {ball_count}", True, (255, 255, 255)), (10, 10))

        # 스킬 UI
        skill_rect = pygame.Rect(15, HEIGHT - 60, 45, 45)
        pygame.draw.rect(display_surface, (40, 40, 50), skill_rect, border_radius=8)
        if skill_slots["FIRE"]:
            inner_rect = skill_rect.inflate(-12, -12)
            pygame.draw.rect(display_surface, (230, 50, 50), inner_rect, border_radius=4)
            display_surface.blit(small_font.render("1", True, (255, 255, 255)), (skill_rect.x + 5, skill_rect.y + 2))
        else:
            count_txt = font.render(str(SKILL_THRESHOLD - bricks_destroyed), True, (150, 150, 160))
            display_surface.blit(count_txt, (skill_rect.centerx - count_txt.get_width()//2, skill_rect.centery - count_txt.get_height()//2))
            gauge_w = (bricks_destroyed / SKILL_THRESHOLD) * (skill_rect.width - 10)
            pygame.draw.rect(display_surface, (200, 50, 50), (skill_rect.x + 5, skill_rect.bottom - 8, gauge_w, 4))

        if game_state == "GAMEOVER":
            over_txt = large_font.render("GAME OVER", True, (255, 50, 50))
            display_surface.blit(over_txt, (WIDTH//2 - over_txt.get_width()//2, HEIGHT//2 - 50))

    # 최종 렌더링 (화면 흔들림 적용)
    render_offset = [random.randint(-shake_intensity, shake_intensity), random.randint(-shake_intensity, shake_intensity)] if shake_intensity > 0 else [0, 0]
    screen.fill((0, 0, 0))
    screen.blit(display_surface, render_offset)
    pygame.display.flip()

pygame.quit()