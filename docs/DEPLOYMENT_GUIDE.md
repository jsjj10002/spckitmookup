# Spckit AI - 배포 가이드

> 프로덕션 환경 배포를 위한 완전한 가이드

## 📋 목차

- [배포 전략 개요](#배포-전략-개요)
- [Frontend 배포](#frontend-배포)
- [Backend 배포](#backend-배포)
- [환경 변수 설정](#환경-변수-설정)
- [CI/CD 파이프라인](#cicd-파이프라인)
- [모니터링 및 로깅](#모니터링-및-로깅)
- [트러블슈팅](#트러블슈팅)

## 🎯 배포 전략 개요

### 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 (Browser)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Frontend (Vercel/Netlify)                   │
│  - Static Hosting                                        │
│  - CDN 자동 배포                                         │
│  - HTTPS 자동 설정                                       │
│  - Gemini API 직접 호출 (클라이언트 사이드)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ (선택적)
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Backend API (GCP Cloud Run)                    │
│  - FastAPI REST API                                      │
│  - RAG 시스템                                            │
│  - ChromaDB (3,000 문서)                                 │
│  - Gemini API 호출                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Google Gemini API                              │
│  - Gemini 2.0 Flash                                      │
│  - Embedding API                                         │
└─────────────────────────────────────────────────────────┘
```

### 배포 단계

| Phase | 목표 | 플랫폼 |
|-------|------|--------|
| **Phase 1** | Frontend 단독 배포 | Vercel |
| **Phase 2** | Backend API 추가 | GCP Cloud Run |
| **Phase 3** | CDN + Cache | Cloudflare |
| **Phase 4** | 모니터링 추가 | Sentry + Analytics |

---

## 🌐 Frontend 배포

### Option 1: Vercel (권장)

**장점:**
- ✅ 무료 티어 (개인 프로젝트)
- ✅ GitHub 자동 배포
- ✅ CDN 글로벌 배포
- ✅ HTTPS 자동
- ✅ 환경 변수 관리 UI

#### 1. Vercel 프로젝트 생성

```bash
# Vercel CLI 설치
npm i -g vercel

# 프로젝트 루트에서
vercel login
vercel
```

#### 2. 프로젝트 설정

```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "installCommand": "npm install",
  "devCommand": "npm run dev",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

#### 3. 환경 변수 설정

Vercel Dashboard → Settings → Environment Variables

```env
VITE_GEMINI_API_KEY=your_production_api_key
VITE_BACKEND_API_URL=https://your-backend-url.run.app
```

#### 4. 배포

```bash
# 프로덕션 배포
vercel --prod

# 미리보기 배포
vercel
```

#### 5. 자동 배포 설정

1. GitHub 저장소 연결
2. Vercel이 자동으로 감지
3. `main` 브랜치 푸시 시 자동 배포
4. PR 생성 시 미리보기 URL 생성

---

### Option 2: Netlify

```bash
# Netlify CLI 설치
npm i -g netlify-cli

# 로그인
netlify login

# 배포
netlify deploy --prod
```

**netlify.toml:**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## 🐳 Backend 배포

### Option 1: GCP Cloud Run (권장)

**장점:**
- ✅ 서버리스 (사용량 기반 과금)
- ✅ 자동 스케일링
- ✅ 컨테이너 기반
- ✅ HTTPS 자동
- ✅ 프리 티어 존재

#### 1. Dockerfile 최적화

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir uv && \
    uv pip install --system -e .

# 애플리케이션 코드 복사
COPY backend/ .

# 데이터 초기화 (옵션)
# RUN python scripts/init_database.py

# 포트 설정
ENV PORT=8080
EXPOSE 8080

# 실행
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

#### 2. GCP 프로젝트 설정

```bash
# GCP CLI 설치 및 로그인
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Container Registry 활성화
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

#### 3. Docker 이미지 빌드 및 푸시

```bash
# 프로젝트 루트에서
cd backend

# 이미지 빌드
docker build -t spckit-ai-backend .

# GCP Container Registry에 태그
docker tag spckit-ai-backend gcr.io/YOUR_PROJECT_ID/spckit-ai-backend

# 푸시
docker push gcr.io/YOUR_PROJECT_ID/spckit-ai-backend
```

#### 4. Cloud Run 배포

```bash
gcloud run deploy spckit-ai-backend \
  --image gcr.io/YOUR_PROJECT_ID/spckit-ai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY
```

#### 5. 환경 변수 설정

**GCP Console 방법:**
1. Cloud Run → 서비스 선택
2. Edit & Deploy New Revision
3. Environment Variables 섹션
4. `GEMINI_API_KEY` 추가

**CLI 방법:**
```bash
gcloud run services update spckit-ai-backend \
  --set-env-vars GEMINI_API_KEY=your_api_key \
  --region us-central1
```

#### 6. ChromaDB 데이터 관리

**옵션 A: 컨테이너 내장 (간단)**
```dockerfile
# Dockerfile에 추가
COPY backend/data/pc_data_dump.sql .
RUN python scripts/init_database.py
```

**옵션 B: Cloud Storage (권장)**
```bash
# GCS 버킷 생성
gsutil mb gs://spckit-ai-chromadb

# 로컬 ChromaDB 업로드
gsutil -m cp -r backend/chroma_db/* gs://spckit-ai-chromadb/

# 애플리케이션에서 다운로드
```

---

### Option 2: Docker + VM (직접 관리)

**GCP Compute Engine:**
```bash
# VM 생성
gcloud compute instances create spckit-ai-backend \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --machine-type=e2-medium \
  --zone=us-central1-a

# SSH 접속
gcloud compute ssh spckit-ai-backend --zone=us-central1-a

# Docker 설치 및 실행
sudo apt-get update
sudo apt-get install -y docker.io
sudo docker run -d -p 8080:8080 \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  gcr.io/YOUR_PROJECT_ID/spckit-ai-backend
```

---

## 🔐 환경 변수 설정

### 개발 환경 (.env.local)

```env
# Frontend
VITE_GEMINI_API_KEY=dev_api_key_here
VITE_BACKEND_API_URL=http://localhost:8080

# Backend (backend/.env)
GEMINI_API_KEY=dev_api_key_here
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 프로덕션 환경

**Frontend (Vercel):**
```env
VITE_GEMINI_API_KEY=prod_api_key_here
VITE_BACKEND_API_URL=https://spckit-ai-backend-xxx.run.app
```

**Backend (Cloud Run):**
```env
GEMINI_API_KEY=prod_api_key_here
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend.vercel.app
```

---

## 🔄 CI/CD 파이프라인

### GitHub Actions 설정

#### Frontend 자동 배포

**.github/workflows/deploy-frontend.yml:**
```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - 'package.json'
      - '.github/workflows/deploy-frontend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
        env:
          VITE_GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          VITE_BACKEND_API_URL: ${{ secrets.BACKEND_API_URL }}
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

#### Backend 자동 배포

**.github/workflows/deploy-backend.yml:**
```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-backend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Configure Docker
        run: gcloud auth configure-docker
      
      - name: Build Docker image
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/spckit-ai-backend ./backend
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/spckit-ai-backend
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy spckit-ai-backend \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/spckit-ai-backend \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}
```

#### 필요한 GitHub Secrets

1. **Frontend:**
   - `GEMINI_API_KEY`
   - `BACKEND_API_URL`
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

2. **Backend:**
   - `GCP_SA_KEY` (Service Account JSON)
   - `GCP_PROJECT_ID`
   - `GEMINI_API_KEY`

---

## 📊 모니터링 및 로깅

### Sentry 통합

```bash
npm install @sentry/browser @sentry/tracing
```

**frontend/js/monitoring.js:**
```javascript
import * as Sentry from "@sentry/browser";
import { BrowserTracing } from "@sentry/tracing";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  integrations: [new BrowserTracing()],
  tracesSampleRate: 1.0,
  environment: import.meta.env.MODE
});
```

### Google Analytics

```html
<!-- frontend/index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Backend 로깅 (Cloud Run)

```python
# backend/rag/config.py
import logging
from loguru import logger

if ENVIRONMENT == "production":
    # GCP Cloud Logging 형식
    logger.add(
        sys.stderr,
        format="{message}",
        level="INFO",
        serialize=True  # JSON 출력
    )
```

---

## 🔍 성능 최적화

### Frontend 최적화

1. **번들 크기 최적화:**
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          gemini: ['@google/genai']
        }
      }
    }
  }
});
```

2. **이미지 최적화:**
```bash
npm install vite-plugin-imagemin -D
```

3. **CDN 캐싱:**
- Vercel 자동 CDN
- Cache-Control 헤더 설정

### Backend 최적화

1. **ChromaDB 메모리 최적화:**
```python
# backend/rag/config.py
CHROMA_SETTINGS = Settings(
    anonymized_telemetry=False,
    allow_reset=True,
    is_persistent=True
)
```

2. **API 응답 캐싱:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_recommendation(query: str):
    return pipeline.query(query)
```

3. **병렬 처리:**
```python
import asyncio

async def batch_embed(texts):
    tasks = [embedder.embed(text) for text in texts]
    return await asyncio.gather(*tasks)
```

---

## 🐛 트러블슈팅

### Frontend 문제

**문제: 빌드 실패**
```bash
# 의존성 재설치
rm -rf node_modules package-lock.json
npm install

# 캐시 삭제
npm run build -- --force
```

**문제: API 키 오류**
- Vercel 환경 변수 확인
- `VITE_` 접두사 확인
- 재배포 필요

### Backend 문제

**문제: Cloud Run 메모리 부족**
```bash
# 메모리 증가
gcloud run services update spckit-ai-backend \
  --memory 4Gi \
  --region us-central1
```

**문제: ChromaDB 초기화 실패**
```bash
# 컨테이너 로그 확인
gcloud run logs read spckit-ai-backend --region us-central1 --limit 50

# 수동 초기화
gcloud run services update spckit-ai-backend \
  --set-env-vars FORCE_INIT=true
```

**문제: Cold Start 지연**
- 최소 인스턴스 수 설정:
```bash
gcloud run services update spckit-ai-backend \
  --min-instances 1 \
  --region us-central1
```

---

## 💰 비용 예측

### Vercel (Frontend)
- **무료 티어**: 개인 프로젝트
- **프로 플랜**: $20/월 (팀 협업)

### GCP Cloud Run (Backend)
```
예상 사용량 (월):
- 요청: 10,000건
- CPU: 0.5 vCPU
- 메모리: 2GB
- 실행 시간: 5초/요청

예상 비용: ~$10-15/월
```

### Gemini API
```
무료 티어:
- 15 RPM (분당 요청)
- 1,500 RPD (일당 요청)
- 1,500,000 TPM (분당 토큰)

유료:
- $0.00025 / 1K 입력 토큰
- $0.00125 / 1K 출력 토큰
```

---

## 📚 추가 리소스

- [Vercel 문서](https://vercel.com/docs)
- [GCP Cloud Run 문서](https://cloud.google.com/run/docs)
- [Gemini API 문서](https://ai.google.dev/docs)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)

---

## ✅ 배포 체크리스트

### 배포 전
- [ ] 모든 테스트 통과
- [ ] 환경 변수 설정 확인
- [ ] API 키 유효성 검증
- [ ] 빌드 오류 없음
- [ ] 로컬에서 프로덕션 빌드 테스트

### Frontend 배포
- [ ] Vercel 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] 환경 변수 설정
- [ ] 커스텀 도메인 설정 (옵션)
- [ ] HTTPS 확인

### Backend 배포
- [ ] Docker 이미지 빌드 성공
- [ ] GCP 프로젝트 설정
- [ ] Cloud Run 서비스 생성
- [ ] ChromaDB 초기화
- [ ] API 엔드포인트 테스트
- [ ] CORS 설정 확인

### 모니터링
- [ ] Sentry 연동
- [ ] Google Analytics 연동
- [ ] 로그 수집 설정
- [ ] 알림 설정

---

**배포 완료 후 확인사항:**
1. Frontend URL 접속 테스트
2. Backend API Health Check
3. RAG 시스템 쿼리 테스트
4. 성능 모니터링 확인
5. 오류 알림 테스트

**Made with ❤️ for production deployment**

