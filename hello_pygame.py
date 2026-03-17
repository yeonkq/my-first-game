import pygame
import sys

# 1. 초기화 및 설정
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Final First Pygame")

# 2. 색상 및 변수 설정
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# 폰트 설정 (기본 폰트, 크기 30)
font = pygame.font.SysFont("arial", 30)

# 원의 속성
radius = 50
circle_x = SCREEN_WIDTH // 2
circle_y = SCREEN_HEIGHT // 2
speed = 7

clock = pygame.time.Clock()
running = True

# 3. 게임 루프 시작
while running:
    # A. 이벤트 처리 (입력 확인)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # B. 키보드 실시간 입력 확인
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        circle_x -= speed
    if keys[pygame.K_RIGHT]:
        circle_x += speed
    if keys[pygame.K_UP]:
        circle_y -= speed
    if keys[pygame.K_DOWN]:
        circle_y += speed
           
    # C. 경계 처리 (화면 밖 가출 방지)
    if circle_x < radius:
        circle_x = radius
    elif circle_x > SCREEN_WIDTH - radius:
        circle_x = SCREEN_WIDTH - radius

    if circle_y < radius:
        circle_y = radius
    elif circle_y > SCREEN_HEIGHT - radius:
        circle_y = SCREEN_HEIGHT - radius
    
    # D. 화면 그리기
    screen.fill(BLACK)  # 1. 배경 지우기
    
    # 2. 원 그리기
    pygame.draw.circle(screen, RED, (int(circle_x), int(circle_y)), radius)
    
    # 3. FPS 계산 및 그리기
    fps_val = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps_val}", True, WHITE)
    screen.blit(fps_text, (10, 10))
    
    # E. 화면 업데이트 및 프레임 고정
    pygame.display.flip()
    clock.tick(60)

# 4. 종료
pygame.quit()
sys.exit()