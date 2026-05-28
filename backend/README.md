## Python 가상환경 세팅

### 가상환경 세팅이 완전 처음이라면!

- anaconda / miniconda 설치
- anaconda / miniconda 실행 후, conda init
- environment.yml 이 있는 위치까지 폴더 이동
- conda env create -f environment.yml -n 가상환경명 입력
  -> environment.yml 을 기준으로 가상환경 설치(이미 만들어진 가상환경을 복제하는 개념)
  -> -n 가상환경명 누락시, environment.yml 에 있는 name 값으로 가상환경명 생성

### 이미 가상환경 세팅이 되어있다면!

- (초기 가상환경이 존재하지 않는다면) conda create -n 가상환경명 python=3.10
- conda activate 가상환경명
- requirements.txt 이 있는 위치까지 폴더 이동
- pip install -r requirements.txt

## backend 서버 실행 방법

1. backend 폴더로 이동
2. uvicorn main:app --host 0.0.0.0 --port 8000 --reload 로 서버 실행
3. ** nodemon main.py 로 실행 안 하는 이유 ** : 1. logging이 두번씩 찍힘 2. 파일 경로 일원화

## cloudflare 서버 실행 방법

1. backend 폴더로 이동
2. python cloudflare_tunnel.py 로 서버 실행

### Colab 과 연결

3. prompt 에 아래 주소 나오는 주소 저장
   ex) Colab BACKEND_URL 에 아래 주소를 넣으세요:
   https://href-dui-marketplace-facilities.trycloudflare.com
4. BACKEND_URL 부분에 복사한 주소 붙여넣기

## 깃 사용법

    - 1. git pull(최신 소스 받아오기)
    - (소스 출동시 backend 담당자와 확인)
    - 2. 방법1: git add .(전체) /방법2: git add 업로드할 파일1, 업로드할 파일2(부분)
        **주의 사항** 작업한 내용중 필요한 파일만 업로드(충돌 방지), git add .(전체) 로 할 경우, 전체 확인 후 업로드
    - 3. git commit -m "커밋할 내용"
    - 4. git push -u origin main(최소 commit 시에만) / git push(2번째부터)

## 폴더 구조도

backend/
├── controllers/ # 요청 처리 로직 (Controller 계층)
│
├── core/ # 핵심 설정 및 공통 기능
│ └── logging.py # 로깅 설정
│
├── data/ # 데이터 파일 / 초기 데이터 / 저장소
│
├── models/ # DB 모델(SQLAlchemy 등)
│
├── routes/ # API 라우터 정의
│
├── schemas/ # Pydantic 요청/응답 스키마
│
├── services/ # 비즈니스 로직 계층
│
├── utils/ # 유틸 함수 모음
│
├── .env # 실제 환경변수
│
├── main.py # FastAPI 엔트리포인트
│
├── README.md # Backend 가이드
│
└── requirement.txt # Python 패키지 목록
