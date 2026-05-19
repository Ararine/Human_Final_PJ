## docker-compose 사용법

1. docker desktop 실행
2. docker-compose up -d(백엔드로 도커 실행) - 이미지와 컨테이너 동시에 백엔드로 올림
3. docekr-compose exec -it 컨테이너명 bash - 특정 컨테이너로 진입
4. docker-compose down() - 컨데이너 내리는 동시에 삭제까지 진행

### 추가 명령어

- docker ps - 현재 실행되고 있는 컨테이너 확인
- docker ps -all - docker 에 존재하는 모든 컨테이너 확인
- docker start (container_name) - (컨테이너 존재시) 컨테이너 올림
- docker stop (container_name) - (컨테이너 존재시) 컨테이너 내림
