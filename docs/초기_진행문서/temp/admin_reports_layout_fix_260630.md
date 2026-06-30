# admin/reports 화면 깨짐 수정 계획

## 목표
- `admin/reports` 페이지가 라이트/다크 테마에서 깨져 보이지 않도록 관리자 공통 UI 톤에 맞춘다.
- 실제 문의 접수 유형과 관리자 탭 필터 값을 맞춘다.
- 데이터가 없는 경우와 있는 경우 모두 자연스럽게 보이도록 목록/상세 화면을 정리한다.

## 원인 요약
1. 데이터 부족이 주 원인은 아니다.
   - 백엔드 `/reports/` 응답은 `items`, `total`, `totalPages`, `type`, `createdAt` 등 프론트가 기대하는 필드를 제공한다.
   - 데이터가 없으면 빈 상태 문구가 표시되도록 되어 있다.
2. 화면 깨짐의 주요 원인은 프론트 레이아웃/CSS다.
   - `AdminReports.css`에 흰색 반투명 텍스트와 다크 배경 전제 스타일이 많아 라이트 관리자 화면에서 글자가 흐리거나 안 보일 수 있다.
   - `<table>` 내부 `tr`에 `display: grid`를 적용해 테이블 레이아웃이 어색하게 보일 수 있다.
   - `terms-tabs`를 재사용하면서 인라인 다크 스타일을 강제로 사용한다.
3. 탭 값이 실제 문의 접수 값과 일부 맞지 않는다.
   - 실제 접수 값: `general`, `bug_report`, `abuse_report`, `billing`, `other`
   - 현재 관리자 탭: `account`, `illegal` 포함, `abuse_report` 누락

## 수정 범위
- `frontend/src/pages/garim/AdminReports.jsx`
- `frontend/src/css/garim-pages/AdminReports.css`

## 작업 순서
1. `TABS`를 실제 문의 유형에 맞게 정리한다.
   - 전체, 일반 문의, 결제/환불, 버그 및 오탐지 신고, 불법 콘텐츠 및 악용 신고, 기타
2. 목록 UI를 관리자 공통 카드/그리드 행 패턴으로 변경한다.
   - `<table>` 대신 `div` 기반 grid row를 사용한다.
   - 컬럼: ID, 유형, 제목, 작성자, 작성일, 상태, 관리
3. 탭 UI를 `terms-tabs` 인라인 스타일에서 `arp-tabs` 클래스로 분리한다.
4. 라이트/다크 공통으로 보이는 색상 변수 기반 CSS로 정리한다.
   - `rgba(255,255,255,...)` 고정 텍스트를 `var(--fg-2)`, `var(--fg-3)` 등으로 변경한다.
   - 목록/상세 카드 배경은 `#fff`와 다크 보정으로 처리한다.
5. 상세 화면의 주요 인라인 다크 배경을 클래스 기반으로 이동한다.
6. 중복 `className` 속성 등 JSX 품질 이슈를 정리한다.
7. `npm run build`로 검증한다.

## 검증 계획
- `cmd /c "cd frontend && npm run build"`
- 결과가 실패하면 오류 위치를 기준으로 수정한다.
- 실제 브라우저 클릭 확인은 필요 시 별도 수행한다.

## 제외 범위
- 백엔드 API shape 변경
- DB 스키마 변경
- 문의 데이터 seed 추가
- 관리자 상세 첨부파일 다운로드 정책 변경
