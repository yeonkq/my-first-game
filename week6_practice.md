# 에셋 추가 실습

## 에셋 스프라이트 추가

### 가로로 6개의 프레임이 있는 경우
frame_count = 6
frame_width = sheet.get_width() // frame_count
frames = []

for i in range(frame_count):
    # Rect(x좌표, y좌표, 가로, 세로)
    crop_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet.get_height())
    frames.append(sheet.subsurface(crop_rect))

### 0.1초(100ms)마다 프레임 전환
animation_timer += dt 
if animation_timer >= 100:
    animation_timer = 0
    current_frame = (current_frame + 1) % len(frames)