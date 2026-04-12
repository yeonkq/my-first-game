import pygame
import os

pygame.init()

# 화면 설정
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Animation Basics")
clock = pygame.time.Clock()

# ── 폴더 경로 및 이미지 로드 (이전 방식 유지) ─────
current_path = os.path.dirname(__file__)
sheet_path = os.path.join(current_path, 'Idle.png') # 스프라이트 시트 파일

try:
    sprite_sheet = pygame.image.load(sheet_path).convert_alpha()
except pygame.error:
    print(f"이미지를 찾을 수 없습니다: {sheet_path}")
    pygame.quit()
    exit()

# ── ✂️ [핵심] 이미지 자르기 설정 ✂️ ──────────────
# 1. 원본 이미지의 크기를 가져옵니다.
sheet_width, sheet_height = sprite_sheet.get_size()

# 2. 프레임 개수 설정 (보내주신 이미지는 가로로 6개입니다)
# *만약 4개만 쓰고 싶다면 이 값을 4로 바꾸고 3번을 수정하면 됩니다.*
frame_count = 6 

# 3. 한 프레임의 가로 크기 계산
frame_width = sheet_width // frame_count
frame_height = sheet_height  # 세로는 전체를 다 씁니다.

# 4. 자른 프레임들을 담을 리스트 생성
frames = []

# 5. [반복문] 원본 이미지에서 한 칸씩 이동하며 자릅니다.
for i in range(frame_count):
    # 자를 영역 정의: Rect(시작X, 시작Y, 가로길이, 세로길이)
    crop_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
    
    # ✂️ 실제 자르기 작업 (subsurface)
    frame_image = sprite_sheet.subsurface(crop_rect)
    
    # 자른 이미지를 리스트에 추가
    frames.append(frame_image)

# ── 🎞️ 애니메이션 상태 변수 🎞️ ────────────────────
current_frame_index = 0  # 현재 보여줄 프레임 번호 (0~5)
animation_timer = 0      # 다음 프레임으로 넘어갈 시간을 재는 타이머
# *애니메이션 속도 조절: 숫자가 클수록 느려집니다. (단위: 밀리초)*
animation_speed = 100    # 100ms (0.1초) 마다 프레임 변경

# 캐릭터 위치 (화면 중앙)
rect = frames[0].get_rect()
rect.center = (200, 150)

running = True
while running:
    # 델타 타임(dt) 계산: 이전 프레임에서 경과된 시간 (밀리초)
    dt = clock.tick(60) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ── [핵심] 애니메이션 업데이트 로직 ──────────────
    animation_timer += dt  # 경과 시간을 타이머에 더합니다.

    # 타이머가 설정한 속도(100ms)를 넘어서면
    if animation_timer >= animation_speed:
        # 1. 타이머 초기화
        animation_timer = 0
        
        # 2. 다음 프레임 번호로 넘어갑니다 (마지막이면 다시 0으로)
        current_frame_index = (current_frame_index + 1) % frame_count

    # ── 그리기 ────────────────────────────────────
    screen.fill((30, 30, 40))
    
    # [핵심] 현재 번호에 해당하는 자른 이미지를 화면에 그립니다.
    current_image = frames[current_frame_index]
    screen.blit(current_image, rect)
    
    pygame.display.flip()

pygame.quit()