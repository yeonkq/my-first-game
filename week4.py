import pygame
import sys
import math

# 초기화 및 화면 설정
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3 Collision Methods: Circle, AABB, OBB")

# 색상 및 폰트 정의
WHITE, GRAY = (255, 255, 255), (150, 150, 150)
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)
BLACK = (0, 0, 0)
font = pygame.font.SysFont("Arial", 24, bold=True)

# 오브젝트 설정
fixed_center = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
fixed_size = pygame.Vector2(160, 100)
fixed_radius = fixed_size.x // 2
angle = 0

player_rect = pygame.Rect(100, 100, 80, 80)
player_radius = player_rect.width // 2
speed = 5

# --- SAT(OBB) 충돌 함수들 ---
def get_obb_points(center, size, angle):
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    half_w, half_h = size.x / 2, size.y / 2
    corners = [pygame.Vector2(-half_w, -half_h), pygame.Vector2(half_w, -half_h),
               pygame.Vector2(half_w, half_h), pygame.Vector2(-half_w, half_h)]
    return [pygame.Vector2(p.x * cos_a - p.y * sin_a, p.x * sin_a + p.y * cos_a) + center for p in corners]

def check_obb_collision(poly1, poly2):
    def get_axes(points):
        axes = []
        for i in range(len(points)):
            edge = points[(i + 1) % len(points)] - points[i]
            axes.append(pygame.Vector2(-edge.y, edge.x).normalize())
        return axes

    def project(points, axis):
        dots = [p.dot(axis) for p in points]
        return min(dots), max(dots)

    for axis in get_axes(poly1) + get_axes(poly2):
        min1, max1 = project(poly1, axis)
        min2, max2 = project(poly2, axis)
        if max1 < min2 or max2 < min1: return False
    return True

# 메인 루프
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # 1. 입력 및 상태 업데이트
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: player_rect.x -= speed
    if keys[pygame.K_RIGHT]: player_rect.x += speed
    if keys[pygame.K_UP]: player_rect.y -= speed
    if keys[pygame.K_DOWN]: player_rect.y += speed
    
    rot_speed = 5 if keys[pygame.K_z] else 1
    angle += rot_speed

    # 2. 충돌 데이터 준비
    poly_fixed = get_obb_points(fixed_center, fixed_size, angle)
    poly_player = [pygame.Vector2(player_rect.topleft), pygame.Vector2(player_rect.topright),
                   pygame.Vector2(player_rect.bottomright), pygame.Vector2(player_rect.bottomleft)]
    fixed_aabb = pygame.Rect(0, 0, fixed_size.x, fixed_size.y) # AABB 비교용 (회전 미고려)
    fixed_aabb.center = fixed_center

    # 3. 각 방식별 충돌 감지
    # Circle: 거리 제곱 비교 (최적화)
    dist_sq = (player_rect.centerx - fixed_center.x)**2 + (player_rect.centery - fixed_center.y)**2
    circle_hit = dist_sq < (player_radius + fixed_radius)**2

    # AABB: Rect 내장 함수 사용
    aabb_hit = player_rect.colliderect(fixed_aabb)

    # OBB: SAT 알고리즘 사용
    obb_hit = check_obb_collision(poly_fixed, poly_player)

    # 4. 그리기
    screen.fill(WHITE)

    # 오브젝트 본체 (회전하는 고정 오브젝트)
    pygame.draw.polygon(screen, GRAY, poly_fixed)
    
    # 바운딩 박스 표시
    pygame.draw.circle(screen, BLUE, (int(fixed_center.x), int(fixed_center.y)), int(fixed_radius), 1) # Circle
    pygame.draw.rect(screen, RED, fixed_aabb, 1) # AABB
    pygame.draw.polygon(screen, GREEN, poly_fixed, 2) # OBB
    
    # 플레이어 표시
    pygame.draw.rect(screen, GRAY, player_rect)
    pygame.draw.circle(screen, BLUE, player_rect.center, player_radius, 1)
    pygame.draw.rect(screen, RED, player_rect, 1)

    # 5. UI 텍스트 표시 (왼쪽 상단)
    texts = [
        (f"Circle: {'HIT' if circle_hit else 'SAFE'}", BLUE),
        (f"AABB: {'HIT' if aabb_hit else 'SAFE'}", RED),
        (f"OBB: {'HIT' if obb_hit else 'SAFE'}", GREEN)
    ]
    
    for i, (text, color) in enumerate(texts):
        surf = font.render(text, True, color)
        screen.blit(surf, (20, 20 + (i * 30)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()