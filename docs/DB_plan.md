# [영구적 실행 취소 관리 (DB History 저장소) 기획안]

단순 인-메모리(RAM) 캐싱으로 유지되어 서버 프로그램 종료 시 함께 폭파되던 불안정한 Undo/Redo 엔진을, **.env에 선언된 실제 원격 PostgreSQL 데이터베이스 상의 영구적 테이블을 구축하여(Persistence) 연결**하는 전면 개편 아키텍처입니다. 이제 브라우저를 끄거나 서버가 내려가도 10년 전의 작업들로 시트를 롤백할 수 있게 됩니다.

## User Review Required

> [!WARNING]
> - 서버 부하와 네트워크 I/O: 구글 시트를 편집할 때마다 매번 원격 DB로 접속해 JSON 페이로드를 `INSERT` 하고, `Undo`마다 `UPDATE` 하는 등 대규모 트래픽이 발생하게 됩니다.
> - **[패키지 추가 설치]** Database ORM 프레임워크인 `SQLAlchemy` 및 PostgreSQL 드라이버인 `psycopg2-binary` 라이브러리를 사용하기 위해 `requirements.txt`에 신규 모듈을 추가 설치할 예정입니다.
> - **[UI 시각화]** "보고 돌릴 수 있게" 라는 피드백에 맞춰, 프론트엔드에 **[📜 전체 히스토리 내역 보기]** 라는 새 모달 창을 하나 만들어 방금 어떤 타입의 작업을 했는지 목록을 뿌려주는 기능(GET API)까지 추가하겠습니다. 괜찮으신가요?

## Proposed Changes

### 백엔드 (FastAPI) 모델 변경 및 DB 구축

#### [NEW] `backend/core/database.py`
- `.env`에 등록된 18.207.181.91 (PostgreSQL)의 인증서 정보(DB_USER, DB_PASSWORD, DB_PORT 등)를 조합하여 Connection Pool 엔진(`create_engine`) 선언.
- SQLAlchemy Base 모델 상속 및 `get_db()` 트랜잭션 의존성 주입(Dependency) 라우터.

#### [NEW] `backend/models/history_model.py`
- 실제 물리 DB에 새겨질 테이블 `action_history` 구축 구조.
- 칼럼 구조 (ORM Schema): 
  - `id` (Primary Key, 자동 순번 증가)
  - `action_type` (VARCHAR: ADD_ROW, UPDATE_SHEET 등)
  - `payload` (JSON Type: oldData, newData 등의 거대한 객체를 담은 역산용 정보 꾸러미)
  - `is_undone` (Boolean: 기본값 False. 만약 되돌리기로 취소되었다면 True 처리)
  - `created_at` (기록 저장 시각)

#### [MODIFY] `backend/services/history_manager.py` (비즈니스 로직 DB 치환)
- 기존 리스트 변수들(`history_stack`, `redo_stack`)을 완전 폐기합니다.
- `push_action()`: 
  - 1단계: `is_undone=True` 인 상태의 쓰레기 튜플들을 모두 `DELETE`.
  - 2단계: 신규 Action을 `action_history` 스키마에 `INSERT` (is_undone=False).
- `pop_action()` (Undo):
  - DB에서 `is_undone=False` 인 항목 중 가장 `ID`가 큰(마지막) 녀석 하나를 반환하며 그 녀석의 상태를 `is_undone=True` 로 `UPDATE` 시켜 Redo 큐로 전송.
- `pop_redo_action()` (Redo):
  - DB에서 `is_undone=True` 인 항목 중 가장 `ID`가 작은(첫 번째) 녀석 하나를 반환하며 다시 `is_undone=False` 로 `UPDATE`.

#### [NEW] 엔드포인트 `GET /api/action/logs`
- 저장된 `action_history` 목록 스펙들을 가져와 프론트엔드에 "어떤 작업들이 있었는지 목록 시각화" 로 제공하는 단순 조회 API 개설.

---

### 프론트엔드 (React) 시각화 구조 변경

#### [MODIFY] `frontend/src/App.jsx`
- **신규 UI 요소**: 
  - 상단 작업 도구 공간에 `[ 📜 작업 기록 로그 보기 ]` 모달 버튼 장착.
- **모달 화면 구성**:
  - 가장 상단부터 가장 최근 작업(Current)까지 일렬로 목록화. (`ADD_ROW`, `UPDATE_SHEET` 등)
  - 이미 Undo 되어 사라진 상태(`is_undone = true`)의 아이템엔 밑줄 취소선을 긋거나 투명도(Opacity) 효과 부여.
  - 리스트를 보면서 방금 전 버튼으로만 까딱까딱 하던 상태가 아닌, 시각적으로 전체적인 현재 진행 상태를 관망하는 효과 부여.

## Verification Plan

### Manual Verification
1. 데이터 변경/수정 시 즉각 에러 없이 원격지 PostgreSQL DB에 JSON 형태의 `payload`가 잘 삽입되어 트랜잭션 무결성이 유지되는지 로그 관측.
2. 프론트엔드의 `[ 📜 작업 기록 로그 보기 ]` 창을 눌러 이전에 생성했던/삭제했던 로깅 테이블이 시각적으로 제대로 그려지는지 렌더링 확인.
