# 🎮 [실습 기록] Pygame 게임 제작 및 EXE 실행 파일 빌드 과정 정리

## 1. 실습 개요
- **프로젝트 명**: Midterm (Wizard: Dungeon Defense)
- **주요 목표**: Pygame을 이용한 게임 로직 구현 및 파이썬 미설치 환경에서도 실행 가능한 독립적인 배포 파일(.exe) 생성

---

## 2. 핵심 해결 과제: 리소스 경로 문제 (Path Issue)
일반적인 `.py` 실행 환경과 PyInstaller의 `one-file` 또는 `one-folder` 빌드 환경은 파일 참조 경로가 다릅니다. 이를 해결하기 위해 `sys._MEIPASS`를 활용한 경로 지정 함수를 적용했습니다.

### 🛠 리소스 경로 설정 함수
```python
import os
import sys

def get_path(filename):
    """ PyInstaller 환경과 일반 실행 환경을 모두 지원하는 경로 함수 """
    if hasattr(sys, '_MEIPASS'):
        # exe로 빌드되었을 때 임시 폴더 경로(_MEIPASS) 참조
        base_path = sys._MEIPASS
    else:
        # .py 파일로 실행 중일 때 현재 폴더 경로 참조
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, "assets", filename)
```

---

## 3. PyInstaller 빌드 방식 및 명령어

### ✅ 방식 1: 폴더 방식 (One-folder) - [현재 선택 방식]
실행 파일과 내부 라이브러리(`_internal`), 에셋(`assets`)이 분리된 형태입니다. 실행 속도가 빠르고 안정적입니다.

- **터미널 명령어**:
  ```cmd
  pyinstaller --noconsole --add-data "assets;assets" Midterm.py
  ```
  - `--noconsole`: 실행 시 검은색 터미널(콘솔) 창이 뜨지 않게 설정
  - `--add-data "assets;assets"`: 외부의 assets 폴더를 빌드 결과물에 포함

### ✅ 방식 2: 단일 파일 방식 (One-file)
모든 것을 하나의 `.exe` 파일로 압축하는 방식입니다.
- **터미널 명령어**:
  ```cmd
  pyinstaller --onefile --noconsole --add-data "assets;assets" Midterm.py
  ```

---

## 4. 최종 배포 및 공유 구성 (배포 가이드)

폴더 방식(One-folder)으로 빌드한 경우, 아래의 세 가지 요소를 **하나의 폴더**에 담아 **ZIP으로 압축**하여 공유해야 합니다.

| 구성 요소 | 역할 | 필수 여부 |
| :--- | :--- | :---: |
| **Midterm.exe** | 게임 실행을 위한 메인 아이콘 | 필수 |
| **_internal** | Python 엔진 및 Pygame 라이브러리 모음 | **필수** |
| **assets** | 게임에 사용된 이미지 및 사운드 파일 | **필수** |

### ⚠️ 주의사항
- `Midterm.exe`만 따로 복사해서 실행하면 안 됩니다. 반드시 `_internal`과 `assets` 폴더가 같은 위치에 있어야 합니다.
- 개발 과정에서 생성된 `build` 폴더나 `Midterm.spec` 파일은 배포 시 포함하지 않아도 됩니다.

---

## 5. 실습 결과 및 체크리스트
- [x] **화면 출력**: `pygame.display.set_mode`를 에셋 로드보다 먼저 실행하여 `.convert()` 에러 해결
- [x] **경로 로직**: `get_path` 함수를 통해 빌드 후에도 이미지/사운드가 정상 출력됨
- [x] **배포 형태**: `dist/Midterm` 폴더 전체를 압축하여 제출 준비 완료

## 6. 정리
이번에는 터미널까지 활용해야 했다는 것이 초반에 헷갈리게된 이유였던 것 같다. 터미널에 명령어를 입력하지 않고 다른 곳에서 오류를 찾고있었던 것이 시간을 많이 잡아먹었다.