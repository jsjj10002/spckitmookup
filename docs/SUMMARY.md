# Spckit AI - 프로젝트 요약

> 프로젝트 핵심 내용을 빠르게 파악하기 위한 요약 문서

---

## 프로젝트 개요

**Spckit AI**는 Google Gemini 2.0 Flash와 RAG(Retrieval-Augmented Generation) 기술을 활용한 AI 기반 PC 부품 추천 시스템이다. 사용자의 자연어 쿼리를 이해하고 135,000개 이상의 실제 부품 데이터베이스에서 최적의 조합을 추천한다.

---

## 핵심 성과

### 1. RAG 시스템 구현 완료

| 항목 | 수치 |
|------|------|
| 부품 데이터 | 135,660개 레코드 |
| 벡터 문서 | 3,000개 |
| 검색 정확도 | 50-62% 유사도 |
| 응답 시간 | 5-10초 |

### 2. 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Vite + Vanilla JavaScript |
| Backend | Python + FastAPI |
| AI/ML | Google Gemini 2.0 Flash |
| Database | ChromaDB (벡터 DB) |

### 3. API 엔드포인트

| 엔드포인트 | 상태 | 설명 |
|-----------|------|------|
| `POST /query` | 완성 | 기본 추천 |
| `POST /query-by-specs` | 완성 | 사양 기반 추천 |
| `POST /compare` | 완성 | 부품 비교 |
| `GET /stats` | 완성 | 시스템 통계 |
| `GET /health` | 완성 | 헬스 체크 |

---

## 시스템 아키텍처

```
[사용자] → [Frontend] → [Backend API] → [RAG Pipeline] → [Gemini API]
                              │
                              ▼
                         [ChromaDB]
                       (벡터 검색)
```

### RAG 파이프라인

1. **임베딩 생성**: 쿼리 → 768차원 벡터
2. **벡터 검색**: ChromaDB에서 Top-K 검색
3. **컨텍스트 구성**: 검색 결과 조합
4. **AI 생성**: Gemini로 추천 응답 생성

---

## 프로젝트 구조

```
SpckitAI/
├── frontend/          # 프론트엔드 (HTML/CSS/JS)
├── backend/           # 백엔드
│   ├── api/          # FastAPI REST API
│   ├── rag/          # RAG 시스템 [완성]
│   └── modules/      # AI 모듈 [개발 중]
├── docs/              # 문서
└── Dockerfile         # Docker 설정
```

---

## 개발 현황

### 완료

- [x] RAG 파이프라인 (임베딩, 검색, 생성)
- [x] ChromaDB 벡터 DB
- [x] FastAPI REST API
- [x] Frontend UI
- [x] Docker 배포 구성

### 개발 중

- [ ] 호환성 검사 모듈
- [ ] PC 사양 진단 모듈
- [ ] 가격 예측 모듈
- [ ] GNN 추천 시스템
- [ ] Step-by-Step PC 빌더

### 계획 중

- [ ] 사용자 인증
- [ ] 견적 저장/공유
- [ ] 3D 부품 시각화
- [ ] 모바일 앱

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd SpckitAI

# 2. 자동 설정 (Windows)
setup_dev.bat

# 3. 개발 서버 실행
run_dev.bat

# 접속
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

---

## 주요 문서

| 문서 | 설명 |
|------|------|
| [README.md](../README.md) | 전체 프로젝트 가이드, 플로우차트 |
| [QUICK_START.md](./QUICK_START.md) | 빠른 시작 가이드 |
| [RAG_GUIDE.md](./RAG_GUIDE.md) | RAG 시스템 상세 |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | 배포 가이드 |
| [backend/modules/README.md](../backend/modules/README.md) | 모듈 개발 가이드 |

---

## 기술적 특이사항

### 해결한 문제들

1. **SQL 파싱**: MySQL 덤프 `INSERT INTO table VALUES` 형식 지원
2. **ChromaDB 메타데이터**: None 값 자동 필터링, 타입 검증
3. **한글 인코딩**: Windows 콘솔 UTF-8 설정 (chcp 65001)
4. **uv 빌드**: pyproject.toml 패키지 정의 추가

### 성능 최적화

- 배치 임베딩 처리 (100개 단위)
- ChromaDB 영구 저장
- API 응답 캐싱 가능

---

## 연락처

- **GitHub**: [Repository URL]
- **문서**: [docs/INDEX.md](./INDEX.md)

---

**프로젝트 버전**: 2.1.0  
**마지막 업데이트**: 2026-01-02
