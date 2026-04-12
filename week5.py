import pygame
import math
import os

# 1. 초기화
pygame.init()
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard Brick Breaker")
clock = pygame.time.Clock()

# 폰트 설정
font = pygame.font.SysFont("arial", 20)
large_font = pygame.font.SysFont("arial", 30, bold=True)

# ── [추가] 마법사 애니메이션 로드 ──────────────────
current_path = os.path.dirname(__file__)
img_path = os.path.join(current_path, 'Idle.png')

try:
    sheet = pygame.image.load(img_path).convert_alpha()
    frame_count = 6
    frame_width = sheet.get_width() // frame_count
    frame_height = sheet.get_height()
    
    # 이미지 자르기
    idle_frames = []
    for i in range(frame_count):
        crop_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        # 이미지가 작을 수 있어 1.5배 키웠습니다 (필요 없으면 제거)
        frame_img = sheet.subsurface(crop_rect)
        scaled_img = pygame.transform.scale(frame_img, (int(frame_width*1.5), int(frame_height*1.5)))
        idle_frames.append(scaled_img)
except:
    print("Idle.png 파일을 찾을 수 없어 기본 도형으로 대체합니다.")
    idle_frames = [pygame.Surface((50, 50))] # 에러 방지

anim_index = 0
anim_timer = 0
anim_speed = 100 # 0.1초마다 프레임 변경
# ────────────────────────────────────────────────

# 2. 게임 변수
bricks = []
balls = []
last_shot_time = 0
shot_interval = 200 

current_angle = -math.pi / 2
rotate_speed = 0.05 

last_row_time = pygame.time.get_ticks()
row_interval = 5000 
round_count = 1

def spawn_bricks(round_num):
    for i in range(5):
        if i % 2 == 0 or round_num % 2 == 0:
            rect = pygame.Rect(i * 80 + 5, 70, 70, 30)
            bricks.append([rect, round_num])

spawn_bricks(round_count)

# 3. 메인 루프
running = True
while running:
    dt = clock.tick(60) # 델타 타임(ms)
    current_time = pygame.time.get_ticks()
    screen.fill((30, 30, 30))
    
    # 키보드 입력
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: current_angle -= rotate_speed
    if keys[pygame.K_RIGHT]: current_angle += rotate_speed

    if current_angle > -0.2: current_angle = -0.2
    if current_angle < -math.pi + 0.2: current_angle = -math.pi + 0.2

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # 애니메이션 업데이트
    anim_timer += dt
    if anim_timer >= anim_speed:
        anim_timer = 0
        anim_index = (anim_index + 1) % len(idle_frames)

    # 자동 발사
    if current_time - last_shot_time > shot_interval:
        dx = math.cos(current_angle) * 7
        dy = math.sin(current_angle) * 7
        # 발사 위치를 마법사 지팡이 근처(중앙 하단)로 설정
        balls.append({"pos": [WIDTH // 2, HEIGHT - 55], "vel": [dx, dy]})
        last_shot_time = current_time

    # 타일 하강 (5초마다)
    if current_time - last_row_time > row_interval:
        round_count += 1
        for br in bricks:
            br[0].y += 40
            if br[0].y >= HEIGHT - 80: running = False
        spawn_bricks(round_count)
        last_row_time = current_time

    # 공 충돌 로직 (수정 없이 유지)
    for b in balls[:]:
        b["pos"][0] += b["vel"][0]
        ball_rect_x = pygame.Rect(b["pos"][0]-5, b["pos"][1]-5, 10, 10)
        for br in bricks[:]:
            if ball_rect_x.colliderect(br[0]):
                b["vel"][0] *= -1
                if b["vel"][0] > 0: b["pos"][0] = br[0].right + 6
                else: b["pos"][0] = br[0].left - 6
                br[1] -= 1
                if br[1] <= 0: bricks.remove(br)
                break

        b["pos"][1] += b["vel"][1]
        ball_rect_y = pygame.Rect(b["pos"][0]-5, b["pos"][1]-5, 10, 10)
        for br in bricks[:]:
            if ball_rect_y.colliderect(br[0]):
                b["vel"][1] *= -1
                if b["vel"][1] > 0: b["pos"][1] = br[0].bottom + 6
                else: b["pos"][1] = br[0].top - 6
                br[1] -= 1
                if br[1] <= 0: bricks.remove(br)
                break

        if b["pos"][0] <= 0 or b["pos"][0] >= WIDTH: b["vel"][0] *= -1
        if b["pos"][1] <= 0: b["vel"][1] *= -1
        if b["pos"][1] >= HEIGHT: balls.remove(b)

    # --- [그리기 섹션] ---
    round_txt = large_font.render(f"ROUND {round_count}", True, (255, 255, 255))
    screen.blit(round_txt, (WIDTH // 2 - round_txt.get_width() // 2, 15))
    
    # 가이드 라인 (바닥선)
    pygame.draw.line(screen, (100, 100, 100), (0, HEIGHT-80), (WIDTH, HEIGHT-80), 2)
    
    # ── [핵심] 마법사 그리기 ──────────────────────
    current_img = idle_frames[anim_index]
    # 발사 방향에 따라 이미지 좌우 반전 (선택 사항)
    if math.cos(current_angle) > 0:
        current_img = pygame.transform.flip(current_img, True, False)
        
    img_rect = current_img.get_rect(center=(WIDTH // 2, HEIGHT - 45))
    screen.blit(current_img, img_rect)
    # ──────────────────────────────────────────────
    
    # 조준선
    lx = WIDTH // 2 + math.cos(current_angle) * 60
    ly = (HEIGHT - 55) + math.sin(current_angle) * 60
    pygame.draw.line(screen, (255, 255, 0), (WIDTH // 2, HEIGHT - 55), (lx, ly), 1)

    for br in bricks:
        pygame.draw.rect(screen, (200, 50, 50), br[0])
        hp_txt = font.render(str(br[1]), True, (255, 255, 255))
        screen.blit(hp_txt, (br[0].x + br[0].width//2 - hp_txt.get_width()//2, br[0].y + 5))

    for b in balls:
        pygame.draw.circle(screen, (255, 255, 255), (int(b["pos"][0]), int(b["pos"][1])), 5)

    time_left = max(0, (row_interval - (current_time - last_row_time)) // 1000)
    timer_txt = font.render(f"Next Down: {time_left}s", True, (255, 255, 0))
    screen.blit(timer_txt, (10, HEIGHT - 30))

    pygame.display.flip()

pygame.quit()