# 1. Build Stage (Frontend)
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# 프론트엔드 빌드 관련 파일 복사
COPY package*.json ./
COPY scripts/ ./scripts/
COPY frontend/ ./frontend/

# 의존성 설치 및 빌드
RUN npm install
RUN npm run build

# 2. Runtime Stage (Backend + Frontend)
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 및 데이터 복사
COPY backend/ ./backend/
# 로컬에 생성된 ChromaDB 데이터도 함께 복사 (데이터 유지)
COPY backend/chroma_db/ ./backend/chroma_db/
COPY .env .

# 빌드된 프론트엔드 파일 복사
COPY --from=frontend-builder /app/dist ./dist

# 포트 설정
ENV PORT=8000
EXPOSE 8000

# 서버 실행
CMD ["sh", "-c", "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT"]
