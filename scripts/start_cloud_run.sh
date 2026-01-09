#!/bin/bash
set -e

# 1. 데이터 다운로드 (GCS -> Local /tmp)
# USE_GCS_DATA=true 일 때만 실행됨
echo "Checking data download configuration..."
python backend/scripts/download_data.py

# 2. Uvicorn 서버 실행
# CHROMA_PERSIST_DIRECTORY는 Dockerfile의 ENV 또는 Cloud Run 환경변수에서 /tmp/chroma_db 로 설정되어야 함
echo "Starting Uvicorn server..."
exec python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
