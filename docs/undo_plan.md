# [백엔드 모듈화 리팩토링 및 되돌리기(Undo) 기능 도입]

현재 `main.py`에 모든 로직(라우팅, 구글 인증, OpenAI 프롬프트 처리)이 혼재되어 크기가 비대해진 현상을 해결하고, 사용자가 실수로 데이터를 삭제하거나 자동 생성 결과가 마음에 들지 않을 때 **'직전 상태로 되돌리기(Undo)'** 버튼 하나로 복구할 수 있는 강력한 히스토리 스택 아키텍처를 새로 제안합니다.

## User Review Required

> [!WARNING]
> - **[구조 개편]** 현존하는 `main.py` 코드는 `routes/`, `services/`, `core/` 등의 디렉토리 구조로 완전히 쪼개져 관리됩니다. 이후 실행방식에는 변함이 없으나 파일 위치가 모두 바뀝니다.
> - **[되돌리기(Undo) 원리]** 구글 시트 API 자체에는 `Ctrl+Z` 버튼이 없기 때문에, 백엔드의 메모리(리스트 변수) 상에 `Command Pattern`으로 '사용자의 마지막 작업 목록'을 역산할 수 있는 스택(Stack)을 구현할 예정입니다.
> - **[되돌리기 범위]** 방금 수행한 '행/열 삭제', '행/열 생성', '새 템플릿(시트) 통합 생성' 등의 API 직후에만 복구가 가능하도록 구현할 계획입니다. (만약 브라우저를 완전히 껐다 켜거나 서버 재구동 시 히스토리는 초기화되며, 방금 변경한 최근 X개 작업에 한해서만 Undo를 지원합니다.) 괜찮으신가요?

## Proposed Changes

### 1. 백엔드 폴더 아키텍처 리팩토링 (Refactoring)
현재 `main.py` 내부의 기능들을 다음과 같이 분할(De-coupling)합니다.
- **[NEW] `backend/core/config.py`**: `.env` 세팅 및 환경 변수 로드
- **[NEW] `backend/services/google_sheets.py`**: 구글 서비스 계정 인증(`service_account.json`), 시트 메타데이터 조회 및 삽입/삭제 핵심 로직
- **[NEW] `backend/services/ai_generator.py`**: OpenAI 키 관리 및 프롬프트 생성/파싱 객체
- **[NEW] `backend/services/history_manager.py`**: **(Undo 엔진)** 발생한 작업(생성/삭제 등)과 삽입/삭제했던 시트의 ID 및 인덱스/데이터를 기록해두고 역추적 복구하는 엔진
- **[NEW] `backend/routers/sheet_router.py`**: FastAPI 통신 엔드포인트(`@app.post...`)들만 깔끔하게 모아둔 라우터
- **[MODIFY] `backend/main.py`**: 이제 앱 구동 및 라우터 등록, CORS 셋업만 담당하는 20줄짜리 진입점(Entry Point)으로 축소됩니다.

### 2. 되돌리기 (Undo) 기능 연동

#### 백엔드 (FastAPI)
- **[NEW] Endpoint**: `POST /api/action/undo`
- **로직**: `history_manager`에 저장된 직전 작업(액션)을 하나 꺼냅니다(Pop).
  - 직전에 `행 추가`를 했다면 ➜ 추가한 해당 줄의 인덱스를 찾아 삭제(Delete)합니다.
  - 직전에 `열 삭제`를 했다면 ➜ 삭제했던 자리에 다시 열 공간을 삽입(InsertDimension)하고 보관해둔 원래의 데이터를 복원(Update)합니다.
  - 직전에 `시트 모달 생성`을 했다면 ➜ 추가된 시트 탭 자체를 삭제(DeleteSheet)합니다.

#### 프론트엔드 (React)
- **[MODIFY] `frontend/src/App.jsx`**:
  - 화면 상단, 시트 이름 옆에 `[ ↩️ 실행 취소(Undo) ]` 전용 버튼을 배치합니다.
  - 누르면 `POST /api/action/undo`를 요청하고 성공 시 즉시 해당 시트 데이터를 재조회(refetch) 합니다.

## Open Questions

- 서버가 재구동되면 기존 작업 히스토리 스택(메모리)이 증발하므로 '이전 되돌리기'가 불가능해지는 단순 메모리 변수 저장 방식을 택하려 합니다. 영구적인 DB 저장이 아닌 임시 메모리 저장을 사용해도 무방한가요?
- '되돌리기' 버튼은 언제나 보이지만, 되돌릴 작업이 없을 땐 비활성화(회색) 되도록 할 계획입니다.

## Verification Plan

### Automated Tests
- 없음

### Manual Verification
- 행/열 추가 아이콘을 클릭한 직후 데이터가 생기면, 즉시 `↩️ 실행 취소` 버튼을 눌러 이전 상태로 원상복귀되는지 Google 시트로 뷰 검증.
- AI 시트 생성 모달로 탭을 만든 직후 `↩️ 실행 취소` 시, 새 탭 전체가 깔끔하게 삭제되는지 확인.
