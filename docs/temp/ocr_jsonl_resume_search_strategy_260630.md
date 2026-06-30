# OCR JSONL 중간 저장, 이어하기, 검색 확장 참고 메모

## 작성 목적

현재 OCR 파이프라인은 영상 분석 중 `ocr_data_f*.json` 같은 프레임별 중간 JSON 파일을 만들고, 이후 `{stem}_index.json`, `{stem}_result.json`으로 통합하는 구조다.

향후 검색 기능과 안정적인 이어하기 기능을 고려할 때, 중간 결과 저장 방식을 어떻게 가져갈지 판단하기 위한 참고 메모다.

## 현재 구조 요약

영상 분석 흐름은 대략 다음과 같다.

```text
OCR 처리 중
-> 프레임별 중간 JSON 생성
-> {stem}_index.json 생성
-> STT 결과와 병합
-> {stem}_result.json 생성
-> detections / analysis_artifacts 등록
```

이미지는 STT 병합이 없으므로 OCR 단계에서 바로 `{stem}_result.json`이 생성된다.

여기서 `{stem}_result.json`은 분석 결과 기준의 최종본이다. 다만 사용자 다운로드용 최종 산출물은 별도의 마스킹 완료 파일이다.

## result.json의 역할

`{stem}_result.json`은 다음 용도로 사용된다.

- OCR + STT 병합 이후 최종 분석 데이터 보존
- 리포트 화면 표시
- 상세보기 오버레이 생성
- 마스킹 대상 선택 재현
- DB 등록 시 원천 데이터 역할

즉, 검색/분석 데이터 기준에서는 최종본으로 볼 수 있다.

## DB 저장 현황

현재 PII 탐지 결과는 `detections` 테이블에 여러 row로 저장된다.

예를 들어 최종 결과에 시각 PII 12개, 음성 PII 3개가 있으면 다음처럼 저장된다.

```text
detections
- visual_pii 12 row
- voice_pii 3 row
```

API 호출은 한 번이어도 내부에서는 `pii_segments` 배열을 순회하면서 항목별로 insert한다.

반면 전체 OCR raw 데이터, 비PII 텍스트, 프레임별 OCR 박스 정보는 주로 JSON 파일 안에 보존된다.

## 모든 데이터를 DB에 바로 저장하는 방식

검색 기능을 고려하면 모든 텍스트 데이터를 DB에 저장하는 방향 자체는 타당하다.

다만 OCR 중간 JSON 원본 전체를 그대로 DB에 넣는 것은 신중해야 한다.

장점:

- 중간 장애 후 재개 판단이 쉬워진다.
- 관리자 화면에서 진행 중 데이터를 조회하기 쉽다.
- 검색 기능과 바로 연결하기 쉽다.
- 프레임 단위 처리 상태를 명확히 관리할 수 있다.

단점:

- 영상 프레임 수가 많으면 DB write가 급증한다.
- OCR 처리 속도가 DB 성능에 영향을 받을 수 있다.
- 트랜잭션, 중복 저장, 재시도 처리가 복잡해진다.
- raw OCR JSON성 데이터가 많아지면 DB가 빠르게 비대해진다.

따라서 DB는 검색과 서비스 기능에 필요한 정제 데이터를 저장하고, 무거운 raw 데이터는 파일로 보관하는 하이브리드 구조가 더 적합하다.

## JSONL 중간 저장을 추천하는 이유

현재처럼 프레임별 JSON 파일을 많이 만들면 다음 문제가 생긴다.

- 파일 개수가 많아진다.
- 파일 open/write/close 비용이 반복된다.
- 디렉터리 탐색과 cleanup 비용이 커진다.
- Windows 또는 Docker volume 환경에서 작은 파일 다량 생성이 느릴 수 있다.

JSONL은 한 줄에 한 프레임 결과를 기록하는 방식이다.

```jsonl
{"frame_no":1,"timestamp":0.033,"status":"done","ocr_data":[]}
{"frame_no":2,"timestamp":0.066,"status":"done","ocr_data":[]}
```

장점:

- 하나의 파일에 append만 하면 된다.
- 프레임별 JSON 파일 폭증을 줄일 수 있다.
- 중간에 끊겨도 마지막 정상 줄까지 복구 가능하다.
- 재시작 시 이미 처리한 `frame_no`를 확인하기 쉽다.
- 최종 `{stem}_index.json` 또는 `{stem}_result.json`으로 변환하기 쉽다.

주의할 점:

- 마지막 줄을 쓰는 중 끊기면 해당 줄이 깨질 수 있다.
- 재시작 시 JSON 파싱이 실패하는 마지막 줄은 버리는 처리가 필요하다.
- 같은 `frame_no`가 중복 기록될 수 있으므로 dedupe 기준이 필요하다.
- JSONL만으로 자동 이어하기가 되는 것은 아니며 resume 로직이 필요하다.

## 이어하기를 위한 필수 조건

JSONL을 쓰더라도 다음 로직이 있어야 안정적인 이어하기가 가능하다.

```text
1. 기존 JSONL 파일 존재 여부 확인
2. JSONL에서 status=done인 frame_no 수집
3. 영상 전체 프레임 목록과 비교
4. 이미 끝난 프레임은 skip
5. 남은 프레임만 OCR 처리
6. OCR 완료 후 index/result.json 생성
7. DB 등록 단계까지 완료 여부 확인
```

이어하기 단계는 다음 수준으로 나눌 수 있다.

```text
JSONL만 존재
-> 수동 복구 힌트 수준

JSONL + frame skip 로직
-> OCR 이어하기 가능

JSONL + stage checkpoint
-> 병합, DB 등록까지 이어하기 가능
```

## 추천 저장 구조

향후 검색과 이어하기를 모두 고려하면 다음 구조가 가장 균형이 좋다.

```text
OCR 처리 중
-> {stem}_ocr_frames.jsonl에 frame 단위 결과 append

OCR 완료
-> {stem}_index.json 생성

STT 병합 완료
-> {stem}_result.json 생성

최종 등록
-> detections 저장
-> search_segments 저장
-> analysis_artifacts 등록

재시작 시
-> JSONL / index.json / result.json / DB 등록 상태를 보고 이어서 처리
```

역할 분리는 다음과 같다.

```text
JSONL
-> OCR 중간 결과, 이어하기용

result.json
-> 최종 분석 원본 보존

detections
-> 개인정보 탐지 결과

search_segments
-> 검색용 정제 텍스트 인덱스

analysis_artifacts
-> result.json, 상세보기 파일 등 산출물 경로와 메타데이터
```

## 검색 기능을 위한 DB 저장 방향

검색 기능을 붙일 예정이라면 OCR/STT에서 나온 모든 텍스트를 검색 가능한 row 형태로 저장하는 것이 좋다.

예상 테이블 예시는 다음과 같다.

```text
analysis_text_segments 또는 search_segments

- segment_id
- job_id
- upload_id
- source_type: ocr / stt
- frame_no
- timestamp_sec
- start_time_sec
- end_time_sec
- text
- bbox_x
- bbox_y
- bbox_w
- bbox_h
- polygon_json
- is_pii
- pii_id
- confidence
- created_at
```

이렇게 저장하면 다음 기능을 만들기 쉽다.

- 특정 단어가 나온 영상 검색
- 검색 결과 클릭 시 해당 시간으로 이동
- OCR/STT 통합 검색
- 개인정보 탐지 결과와 연결
- 검색 결과에서 박스 또는 프레임 미리보기 표시
- 추후 pgvector 기반 의미 검색 확장

## 속도 영향

JSONL로 바꾼다고 OCR 모델 추론 자체가 빨라지는 것은 아니다.

다만 다음 구간은 개선될 가능성이 있다.

- 중간 파일 저장
- 파일 open/close 반복
- 수백/수천 개 파일 glob 탐색
- 최종 통합 시 파일 읽기
- cleanup

따라서 전체 분석 시간은 OCR 추론 병목에 따라 개선폭이 제한될 수 있지만, 파일 I/O와 관리성은 확실히 좋아질 가능성이 높다.

## 권장 결론

단기적으로는 프레임별 `ocr_data_f*.json` 구조를 바로 DB 저장으로 바꾸기보다, 단일 JSONL 중간 저장으로 전환하는 것을 우선 검토한다.

장기적으로는 최종 단계에서 검색용 `search_segments` 테이블을 추가해 OCR/STT 텍스트를 정제된 row 형태로 저장한다.

최종 추천 구조:

```text
프레임 단위 JSONL 중간 저장
-> 이어하기와 파일 개수 감소

result.json 최종 생성
-> 분석 원본 보존

detections 저장
-> 개인정보 탐지 결과

search_segments 저장
-> 영상 검색 기능

stage checkpoint 저장
-> 장애 후 안정적인 재개
```

이 구조가 현재 파이프라인을 크게 갈아엎지 않으면서도 검색, 복구, 유지보수 측면에서 확장성이 가장 좋다.
