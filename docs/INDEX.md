# Spckit AI 문서 목차

프로젝트의 모든 문서가 이 디렉토리에 정리되어 있다.

---

## 목차

- [빠른 시작](#빠른-시작)
- [시스템 가이드](#시스템-가이드)
- [배포](#배포)
- [참고 자료](#참고-자료)

---

## 빠른 시작

새로운 팀원이나 처음 프로젝트를 접하는 경우 아래 순서로 진행한다.

| 순서 | 문서 | 설명 |
|------|------|------|
| 1 | [README.md](../README.md) | 프로젝트 전체 개요, 플로우차트, 아키텍처 |
| 2 | [QUICK_START.md](./QUICK_START.md) | 5분 안에 로컬 환경 설정 |
| 3 | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | 문제 발생 시 해결 방법 |

---

## 시스템 가이드

### RAG 시스템

| 문서 | 설명 |
|------|------|
| [RAG_GUIDE.md](./RAG_GUIDE.md) | RAG 시스템 완전 가이드 - 아키텍처, 사용법, API |

### 백엔드 모듈

| 문서 | 설명 |
|------|------|
| [backend/README.md](../backend/README.md) | 백엔드 전체 구조 및 실행 방법 |
| [backend/ONBOARDING.md](../backend/ONBOARDING.md) | 백엔드 개발 환경 온보딩 |
| [backend/modules/README.md](../backend/modules/README.md) | AI 모듈 개발 가이드 |
| [backend/modules/SERVICE_ARCHITECTURE.md](../backend/modules/SERVICE_ARCHITECTURE.md) | 서비스 아키텍처 및 모듈 현황 |

### 프론트엔드

| 문서 | 설명 |
|------|------|
| [frontend/README.md](../frontend/README.md) | 프론트엔드 구조 및 실행 방법 |

---

## 배포

| 문서 | 설명 |
|------|------|
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | 완전한 프로덕션 배포 가이드 |

배포 가이드 내용:
- Frontend 배포 (Vercel, Netlify)
- Backend 배포 (GCP Cloud Run, Docker)
- CI/CD 파이프라인 설정
- 모니터링 및 로깅

---

## 참고 자료

### 변경 이력

| 문서 | 설명 |
|------|------|
| [CHANGELOG.md](./CHANGELOG.md) | 버전별 변경사항 |

### 프로젝트 개요

| 문서 | 설명 |
|------|------|
| [SUMMARY.md](./SUMMARY.md) | 프로젝트 핵심 요약 |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | 프로젝트 디렉토리 구조 상세 |

### 기타

| 문서 | 설명 |
|------|------|
| [.gitignore.md](./.gitignore.md) | Git 무시 파일 가이드 |
| [device-insights-research.md](./device-insights-research.md) | 연구 자료 |

---

## 문서 구조

```
docs/
├── INDEX.md                 # 이 파일 (문서 목차)
│
├── 시작하기
│   ├── QUICK_START.md       # 빠른 시작 가이드
│   └── TROUBLESHOOTING.md   # 문제 해결
│
├── 시스템 가이드
│   ├── RAG_GUIDE.md         # RAG 시스템 완전 가이드
│   └── PROJECT_STRUCTURE.md # 프로젝트 구조 상세
│
├── 배포
│   └── DEPLOYMENT_GUIDE.md  # 프로덕션 배포 가이드
│
└── 참고
    ├── CHANGELOG.md         # 변경 이력
    ├── SUMMARY.md           # 프로젝트 요약
    └── .gitignore.md        # Git 가이드
```

---

## 역할별 추천 문서

### 개발자

1. [README.md](../README.md) - 프로젝트 개요, 플로우차트
2. [QUICK_START.md](./QUICK_START.md) - 환경 설정
3. [RAG_GUIDE.md](./RAG_GUIDE.md) - RAG 시스템 이해
4. [backend/modules/README.md](../backend/modules/README.md) - 모듈 개발

### DevOps / 배포 담당

1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 배포 가이드
2. [README.md](../README.md) - Docker 섹션

### 기획자 / PM

1. [README.md](../README.md) - 서비스 플로우, 기능 정의
2. [SUMMARY.md](./SUMMARY.md) - 프로젝트 요약
3. [backend/modules/SERVICE_ARCHITECTURE.md](../backend/modules/SERVICE_ARCHITECTURE.md) - 개발 현황

---

## 상황별 문서

| 상황 | 추천 문서 |
|------|----------|
| 처음 프로젝트 시작 | [README.md](../README.md) → [QUICK_START.md](./QUICK_START.md) |
| 오류 발생 | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |
| RAG 시스템 이해 | [RAG_GUIDE.md](./RAG_GUIDE.md) |
| 새 모듈 개발 | [backend/modules/README.md](../backend/modules/README.md) |
| 배포하기 | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |
| 변경사항 확인 | [CHANGELOG.md](./CHANGELOG.md) |
| 프로젝트 구조 파악 | [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) |

---

## 도움말

문서에서 답을 찾지 못한 경우:

1. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 확인
2. GitHub Issues 검색
3. 새 Issue 생성

---

**문서 최종 업데이트**: 2026-01-02  
**문서 버전**: 2.1.0
