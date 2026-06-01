# Garim 시각 개인정보 OCR 실행 가이드

이 문서는 영상의 장면을 분할하고, 필요한 프레임만 OCR에 전달해 화면 속 개인정보 후보를
찾는 기능을 팀원이 재현하는 방법을 설명한다.

현재 시각 OCR 파이프라인은 탐지 결과 JSON, CSV와 검토용 블러 이미지를 생성한다. 탐지한
영역을 영상 전체에 지속적으로 모자이크 처리하는 렌더러는 별도 개발 대상이다.

## 처리 흐름

```text
영상 입력
-> PySceneDetect 장면 탐지
-> 장면 경계, 기본 주기, 모션 후보 기반 프레임 샘플링
-> dHash 기반 유사 프레임 제거
-> PaddleOCR 문자 탐지 및 인식
-> 개인정보 패턴 분류
-> 인접 탐지 구간 병합 및 시간 여유 적용
-> JSON, CSV, 검토용 블러 이미지 저장
```

현재 기본 샘플링 값:

| 구분 | 기본값 |
|---|---:|
| 일반 구간 | `0.5 fps` |
| 장면 경계 앞뒤 `0.5초` | `2 fps` |
| 모션 또는 텍스트 집중 구간 | `4 fps` |
| 모션 후보 검사 | `1 fps` |
| OCR 인식 배치 크기 | `16` |

처음 테스트할 때는 이 값을 유지한다. 빠르게 지나가는 텍스트를 놓치는 경우에만 FPS를
단계적으로 높인다.

## 1. 처음 Pull 받은 팀원의 준비

저장소를 처음 받는 경우:

```bash
git clone <프로젝트 GitHub URL>
cd Human_Final_PJ
```

이미 저장소가 있다면 최신 코드를 받는다.

```bash
cd Human_Final_PJ
git pull
```

시각 OCR 독립 테스트에 필요한 파일:

```text
docs/colab/garim_visual_pii_ocr_pipeline.ipynb
docs/colab/garim_visual_pii_ocr_pipeline.py
```

통합 worker 테스트까지 진행할 때 필요한 파일:

```text
docs/colab/garim_pipeline.py
docs/colab/garim_colab_worker.ipynb
docs/colab/garim_colab_worker.py
docs/colab/COLAB_WORKER_RUNBOOK.md
```

## 2. OCR 기능만 독립적으로 테스트

백엔드 실행이나 로그인이 없어도 OCR 담당자는 이 방법으로 장면 분할과 OCR 전달을 먼저
확인할 수 있다.

1. Google Colab에서 `docs/colab/garim_visual_pii_ocr_pipeline.ipynb`를 연다.
2. `런타임 -> 런타임 유형 변경 -> GPU`를 선택한다.
3. 백엔드와 프론트엔드를 실행하고 로그인하고 분석파일을 업로드 한다.
4. 첫 번째 설치 셀을 실행한다.
5. `# 2. Upload the reusable module` 셀을 실행한다.
6. 구글드라이브 내 드라이브에 garim_colab 폴더를 만들고 그 안에 `garim_pipeline.py` 와 `garim_visual_pii_ocr_pipeline.py`를 업로드한다.
7. `# 3. Configure sampling and output` 셀을 실행한다.
8. `# 4. Upload a video` 셀을 실행한다.
9. 이후 셀을 순서대로 실행해 결과를 확인한다.

첫 검증 영상은 `10~30초` 길이를 권장한다. 화면에 전화번호, 이메일 또는 주소처럼 사람이
직접 확인할 수 있는 텍스트가 크게 표시된 영상을 사용한다.

정상 실행 중에는 다음 로그가 출력된다.

```text
INFO:pyscenedetect:Detecting scenes...
[OCR] 장면 탐지 완료: ...개
[OCR] 모션 후보 탐지 완료: ...개
[OCR] OCR 전달 프레임: ...개
[OCR] PaddleOCR 초기화 (device=cpu 또는 gpu, detector=mobile)
Creating model: ('PP-OCRv5_mobile_det', ...)
[OCR] 1차 OCR 완료: ...건
```

## 3. 독립 테스트 결과 확인

노트북의 `OUTPUT_DIR` 기본값은 다음과 같다.

```text
/content/garim_visual_pii_output/
```

생성 파일:

```text
visual_pii_detections.json
visual_pii_detections.csv
review_thumbnails/
```

결과 요약에서 아래 값을 확인한다.

| 항목 | 의미 |
|---|---|
| `scene_count` | 탐지된 장면 수 |
| `sampled_frame_count` | OCR에 전달한 프레임 수 |
| `ocr_hit_count` | OCR로 읽은 문자열 수 |
| `detection_count` | 개인정보 패턴으로 분류된 탐지 수 |

판단 기준:

- `sampled_frame_count == 0`: 영상 읽기 또는 프레임 샘플링 실패
- `ocr_hit_count == 0`: OCR이 텍스트를 읽지 못함
- `detection_count == 0`: 텍스트는 읽었지만 개인정보 패턴이 없을 수 있음
- `review_thumbnails/`에 이미지가 있음: 개인정보 bbox를 찾아 검토용 블러 이미지 생성 완료

결과 JSON 예시:

```json
{
  "upload_id": "uuid",
  "detections": [
    {
      "type": "phone",
      "text_masked": "010-****-1234",
      "start_sec": 73.2,
      "end_sec": 75.1,
      "start_display": "01:13.200",
      "end_display": "01:15.100",
      "bbox": [420, 180, 640, 280],
      "confidence": 0.96,
      "source_frames": [2196, 2202, 2208],
      "replacement": "blur"
    }
  ]
}
```

`bbox`는 원본 영상 기준 `[x1, y1, x2, y2]` 픽셀 좌표다. 원문 개인정보는 결과에 그대로
저장하지 않고 `text_masked` 형태로 저장한다.

## 4. OCR에 넘기기 직전 프레임 확인

OCR 정확도를 보기 전에 프레임 샘플링이 적절한지 확인하려면 Colab 새 셀에서 아래 코드를
실행한다. 이 코드는 OCR 모델을 다시 실행하지 않고 OCR 입력 프레임만 화면에 표시한다.

```python
from pathlib import Path
import cv2
import matplotlib.pyplot as plt

from garim_visual_pii_ocr_pipeline import (
    VisualPIIConfig,
    get_video_meta,
    detect_scenes,
    find_motion_timestamps,
    build_candidate_timestamps,
    read_unique_frames,
)

videos = [p for p in Path("/content").glob("*") if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi", ".webm"}]
assert videos, "업로드된 영상이 없습니다."

video_path = str(max(videos, key=lambda p: p.stat().st_mtime))
config = VisualPIIConfig()
meta = get_video_meta(video_path)
scenes = detect_scenes(video_path, meta, config.scene_threshold)
motion = find_motion_timestamps(video_path, meta, config)
timestamps = build_candidate_timestamps(meta, scenes, config, motion)
frames = read_unique_frames(video_path, meta, timestamps, config)

print(f"영상: {video_path}")
print(f"장면 수: {len(scenes)}")
print(f"OCR 전달 프레임 수: {len(frames)}")

limit = min(40, len(frames))
cols = 4
rows = (limit + cols - 1) // cols
plt.figure(figsize=(16, rows * 3))

for i, frame in enumerate(frames[:limit]):
    image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
    plt.subplot(rows, cols, i + 1)
    plt.imshow(image)
    plt.title(f"Frame {frame.frame_no}\n{frame.timestamp_sec:.2f}s")
    plt.axis("off")

plt.tight_layout()
plt.show()
```

개인정보가 표시되는 시점의 이미지가 목록에 없다면 OCR 문제가 아니라 샘플링 문제다. 이
경우 `VisualPIIConfig`의 FPS 값을 높여야 한다.

## 5. 로그인 설정 완료 상태에서 통합 테스트

이 절차는 팀원이 OAuth 로그인과 프론트엔드 실행 환경을 정상적으로 설정했다고 가정한다.
백엔드, Docker, Cloudflare Tunnel, Colab worker를 함께 연결해 실제 업로드 흐름을 테스트한다.

### 5.1 Docker 실행

```powershell
cd Human_Final_PJ\docker
docker compose up -d
docker ps
```

`final_db`, `final_redis`가 `healthy`인지 확인한다.

### 5.2 백엔드 실행

```powershell
cd Human_Final_PJ\backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

팀원 PC의 `.env` 설정을 사용한다. `.env`와 실제 secret은 Git에 올리지 않는다.

### 5.3 Colab worker 준비

백엔드 터미널은 그대로 둔 채 새 PowerShell 터미널을 열고 Cloudflare Tunnel을 실행한다.

```powershell
cd Human_Final_PJ\backend
python cloudflare_tunnel.py
```

정상 실행되면 다음과 같은 주소가 출력된다.

```text
Cloudflare Tunnel URL: https://xxxx.trycloudflare.com
Colab BACKEND_URL 에 아래 주소를 넣으세요:
https://xxxx.trycloudflare.com
```

Cloudflare Tunnel 터미널도 종료하지 않고 유지한다. 이 터미널을 닫으면 Colab worker가
백엔드에 접근할 수 없다.

Google Drive의 `garim_colab` 폴더에 최신 파일을 업로드한다.

```text
garim_pipeline.py
garim_visual_pii_ocr_pipeline.py
garim_colab_worker.py
```

Colab worker의 설정 셀에서 다음 값을 확인한다.

```python
BACKEND_URL = "https://현재주소.trycloudflare.com"
WORKER_SECRET = "백엔드 .env의 WORKER_SECRET과 동일한 값"
```

Cloudflare Tunnel 주소는 터널을 다시 실행하면 바뀔 수 있다. 항상 `python
cloudflare_tunnel.py` 터미널에 새로 출력된 주소를 사용한다.

OCR만 통합 테스트하려면 `garim_pipeline` 또는 worker를 import하기 전에 실행한다.

```python
import os
os.environ["GARIM_VISUAL_OCR_ONLY"] = "true"
```

이후 worker notebook의 셀을 위에서 아래로 실행한다. 이전 파일을 이미 import했다면:

```text
런타임 -> 세션 다시 시작 -> 모두 실행
```

### 5.4 프론트엔드에서 테스트

1. 정상 로그인한다.
2. 업로드 화면에서 `10~30초` 테스트 MP4를 선택한다.
3. 업로드 완료 후 분석 요청 버튼을 누른다.
4. 분석 진행 화면에서 `queued -> processing -> completed` 상태 변화를 확인한다.
5. Colab 로그에서 OCR 단계가 완료되는지 확인한다.

OCR 전용 모드에서는 STT, 음성 개인정보 탐지, beep 렌더링을 실행하지 않는다.

## 6. 자주 발생하는 문제

### 정상 경고

아래 메시지는 라이브러리 내부 경고이며 실행 실패가 아니다.

```text
SyntaxWarning: invalid escape sequence
```

### 이전 파일 실행

아래 로그가 보이면 Google Drive에 이전 OCR 파일이 남아 있는 것이다.

```text
Creating model: ('PP-OCRv5_server_det', ...)
```

최신 파일은 다음 mobile 탐지 모델을 사용한다.

```text
Creating model: ('PP-OCRv5_mobile_det', ...)
```

Drive 파일을 교체하고 Colab 세션을 다시 시작한다.

### Paddle OneDNN 오류

```text
ConvertPirAttribute2RuntimeAttribute not support ...
```

수정된 최신 `garim_visual_pii_ocr_pipeline.py`를 업로드하고 Colab 세션을 다시 시작한다.
최신 코드는 OneDNN을 비활성화하며, Paddle이 CUDA 빌드일 때만 GPU를 선택한다.

### 작업이 진행 화면에서 계속 멈춤

Colab 로그의 마지막 줄을 확인한다. 작업이 실패했는데 프론트 상태가 갱신되지 않으면
백엔드 DB의 job 상태와 Colab worker 로그를 함께 확인한다. 처음에는 반드시 작은 영상으로
테스트한다.

## 7. 저장소 보안

아래 파일은 Git에 올리지 않는다.

```text
.env
실제 사용자 영상
OCR 결과 JSON 및 CSV
review_thumbnails/
모델 가중치
생성 ZIP 파일
Google OAuth secret
WORKER_SECRET
node_modules/
__pycache__/
```

검토용 이미지도 개인정보의 일부를 포함할 수 있으므로 로컬 또는 Colab 임시 결과로만
사용한다.
