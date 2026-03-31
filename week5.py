import pygame
import math

# 1. 초기화
pygame.init()
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Keyboard Control - Round Display")
clock = pygame.time.Clock()

# 폰트 설정 (시스템 기본 폰트 사용)
font = pygame.font.SysFont("arial", 20)
large_font = pygame.font.SysFont("arial", 30, bold=True) # 라운드용 큰 폰트

# 2. 게임 변수
bricks = []
balls = []
last_shot_time = 0
shot_interval = 200 

current_angle = -math.pi / 2 # 초기 각도 (위쪽)
rotate_speed = 0.05          # 조준 회전 속도

last_row_time = pygame.time.get_ticks()
row_interval = 5000 
round_count = 1

def spawn_bricks(round_num):
    for i in range(5):
        if i % 2 == 0 or round_num % 2 == 0:
            rect = pygame.Rect(i * 80 + 5, 70, 70, 30) # 상단 여백을 위해 y 시작점 조정
            bricks.append([rect, round_num])

spawn_bricks(round_count)

# 3. 메인 루프
running = True
while running:
    current_time = pygame.time.get_ticks()
    screen.fill((30, 30, 30))
    
    # 키보드 입력 처리
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        current_angle -= rotate_speed
    if keys[pygame.K_RIGHT]:
        current_angle += rotate_speed

    # 각도 제한
    if current_angle > -0.2: current_angle = -0.2
    if current_angle < -math.pi + 0.2: current_angle = -math.pi + 0.2

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 자동 발사 로직
    if current_time - last_shot_time > shot_interval:
        dx = math.cos(current_angle) * 7
        dy = math.sin(current_angle) * 7
        balls.append({"pos": [WIDTH // 2, HEIGHT - 30], "vel": [dx, dy]})
        last_shot_time = current_time

    # 5초마다 타일 하강
    if current_time - last_row_time > row_interval:
        round_count += 1
        for br in bricks:
            br[0].y += 40
            if br[0].y >= HEIGHT - 60: running = False
        spawn_bricks(round_count)
        last_row_time = current_time

    # 끼임 방지 충돌 로직
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
    
    # 1. 상단 UI (라운드 표시)
    round_txt = large_font.render(f"ROUND {round_count}", True, (255, 255, 255))
    screen.blit(round_txt, (WIDTH // 2 - round_txt.get_width() // 2, 15))
    
    # 2. 게임 요소들
    pygame.draw.line(screen, (100, 100, 100), (0, HEIGHT-50), (WIDTH, HEIGHT-50), 2)
    pygame.draw.circle(screen, (0, 255, 0), (WIDTH // 2, HEIGHT - 20), 15)
    
    # 조준 가이드선
    lx = WIDTH // 2 + math.cos(current_angle) * 80
    ly = (HEIGHT - 20) + math.sin(current_angle) * 80
    pygame.draw.line(screen, (255, 255, 0), (WIDTH // 2, HEIGHT - 20), (lx, ly), 2)

    # 벽돌 및 체력 표시
    for br in bricks:
        pygame.draw.rect(screen, (200, 50, 50), br[0])
        hp_txt = font.render(str(br[1]), True, (255, 255, 255))
        screen.blit(hp_txt, (br[0].x + br[0].width//2 - hp_txt.get_width()//2, br[0].y + 5))

    # 공 그리기
    for b in balls:
        pygame.draw.circle(screen, (255, 255, 255), (int(b["pos"][0]), int(b["pos"][1])), 5)

    # 하단 타이머 표시
    time_left = max(0, (row_interval - (current_time - last_row_time)) // 1000)
    timer_txt = font.render(f"Next Down: {time_left}s", True, (255, 255, 0))
    screen.blit(timer_txt, (10, HEIGHT - 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()