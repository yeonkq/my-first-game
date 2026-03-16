import pygame
import random
import math

# 초기화
pygame.init()

# 설정
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fancy Particle Playground")

clock = pygame.time.Clock()
particles = pygame.sprite.Group()  # 스프라이트 그룹 생성

# 입자 클래스 정의
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((7, 7), pygame.SRCALPHA)  # 투명한 배경을 가진 사각형 생성
        self.color = (
            random.randint(150, 255),
            random.randint(100, 255),
            random.randint(150, 255)
        )
        pygame.draw.circle(self.image, self.color, (3, 3), 3)  # 원 그리기
        self.rect = self.image.get_rect(center=(x, y))

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 6)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = random.randint(40, 80)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.vy += 0.08
        self.life -= 1

        # 생명 주기가 끝난 입자는 제거
        if self.life <= 0:
            self.kill()

def draw_background(surface, t):
    for y in range(HEIGHT):
        c = int(40 + 30 * math.sin(y * 0.01 + t))
        color = (10, c, 50 + c // 2)
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

# 메인 루프
running = True
time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:  # 마우스 버튼 클릭 이벤트
            if event.button == 1:  # 왼쪽 버튼
                # 입자 수 제한 (최대 100개)
                if len(particles) < 100:
                    for _ in range(8):
                        particles.add(Particle(event.pos[0], event.pos[1]))

    time += 0.03

    draw_background(screen, time)

    particles.update()  # 모든 입자 업데이트
    particles.draw(screen)  # 모든 입자 그리기

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

