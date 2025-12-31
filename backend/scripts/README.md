# Scripts - 유틸리티 스크립트

> 개발, 디버그, 초기화를 위한 스크립트 모음

---

## 파일 목록

| 파일 | 용도 | 실행 시점 |
|------|------|----------|
| `setup_dev.py` | 개발 환경 자동 설정 | 최초 1회 |
| `init_database.py` | 벡터 DB 초기화 | 최초 1회 또는 데이터 갱신 시 |
| `test_rag.py` | RAG 파이프라인 테스트 | 개발 중 수시 |
| `check_sql.py` | SQL 파일 구조 확인 | 디버그 시 |
| `debug_sql_parse.py` | SQL 파싱 디버그 | 디버그 시 |

---

## 주요 스크립트

### 1. setup_dev.py - 개발 환경 설정

새 팀원 온보딩 시 실행:

```bash
# 프로젝트 루트에서
python backend/scripts/setup_dev.py
```

기능:
- uv 설치 확인
- 가상 환경 생성
- 의존성 설치
- 환경 변수 파일 생성
- 벡터 DB 초기화 (선택)

### 2. init_database.py - 벡터 DB 초기화

SQL 덤프 파일을 파싱하여 ChromaDB에 임베딩:

```bash
python backend/scripts/init_database.py
```

소요 시간: 약 10-15분 (135,660개 문서)

### 3. test_rag.py - RAG 테스트

RAG 파이프라인 동작 확인:

```bash
python backend/scripts/test_rag.py
```

테스트 항목:
- 벡터 DB 연결
- 쿼리 임베딩
- 검색 결과
- AI 응답 생성

---

## 디버그 스크립트

### check_sql.py

SQL 덤프 파일의 구조를 확인:

```bash
python backend/scripts/check_sql.py
```

출력:
- 파일 크기
- 테이블 목록
- INSERT 문 개수

### debug_sql_parse.py

SQL 파싱 문제 디버그:

```bash
python backend/scripts/debug_sql_parse.py
```

출력:
- 파싱된 statement 수
- 첫 번째 INSERT 문 상세 분석
- 컬럼/레코드 정보

---

## 참고

- 모든 스크립트는 **프로젝트 루트**에서 실행
- 가상 환경 활성화 필요: `source backend/.venv/bin/activate`
