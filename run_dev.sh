#!/bin/bash
# ========================================
# Spckit AI 통합 개발 서버 실행 스크립트
# ========================================
#
# 이 스크립트는 백엔드 API 서버와 프론트엔드 개발 서버를 모두 실행합니다.
# 벡터 DB가 없으면 자동으로 초기화됩니다.
#

echo ""
echo "========================================"
echo "  Spckit AI 개발 서버 시작"
echo "========================================"
echo ""

# 프로젝트 루트로 이동 (이미 루트에 있음)
cd "$(dirname "$0")"

# 가상 환경 확인
if [ ! -f "backend/.venv/bin/activate" ]; then
    echo ""
    echo "[오류] 가상 환경이 없습니다."
    echo ""
    echo "먼저 setup_dev.sh를 실행해주세요."
    echo ""
    exit 1
fi

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo ""
    echo "[경고] .env 파일이 없습니다."
    echo ""
    echo "setup_dev.sh를 실행하여 환경 변수를 설정해주세요."
    echo ""
    exit 1
fi

# Node.js 확인
if ! command -v node &> /dev/null; then
    echo ""
    echo "[경고] Node.js가 설치되어 있지 않습니다."
    echo ""
    echo "진단 정보:"
    echo "  - command -v node 결과: $(command -v node)"
    echo "  - node --version 결과: $(node --version 2>&1)"
    echo ""
    echo "프론트엔드 서버를 실행하려면 Node.js가 필요합니다."
    echo "설치: https://nodejs.org/"
    echo ""
    read -p "백엔드만 실행하시겠습니까? (y/n): " backend_only
    if [ "$backend_only" != "y" ]; then
        exit 1
    fi
    FRONTEND_SKIP=1
fi

# 프론트엔드 의존성 확인
if [ -z "$FRONTEND_SKIP" ]; then
    if [ ! -d "node_modules" ]; then
        echo ""
        echo "[정보] 프론트엔드 의존성이 설치되지 않았습니다."
        echo "[정보] npm install을 실행합니다..."
        echo ""
        npm install
        if [ $? -ne 0 ]; then
            echo ""
            echo "[경고] npm install 실패. 프론트엔드 없이 진행합니다."
            FRONTEND_SKIP=1
        fi
    fi
fi

echo ""
echo "========================================"
echo "  서버 시작 중..."
echo "========================================"
echo ""

# 가상 환경 활성화
echo "[1/3] 백엔드 가상 환경 활성화 중..."
source backend/.venv/bin/activate

if [ $? -ne 0 ]; then
    echo ""
    echo "[오류] 가상 환경 활성화 실패"
    exit 1
fi

# 프론트엔드 서버 시작 (백그라운드)
if [ -z "$FRONTEND_SKIP" ]; then
    echo "[2/3] 프론트엔드 개발 서버 시작 중..."
    echo ""
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    sleep 2
    echo "[완료] 프론트엔드 서버가 백그라운드에서 시작되었습니다."
    echo "[정보] 로그 확인: tail -f frontend.log"
    echo ""
fi

# 백엔드 API 서버 실행
echo "[3/3] 백엔드 API 서버 시작 중..."
echo ""
echo "========================================"
echo "  서버 정보"
echo "========================================"
if [ -z "$FRONTEND_SKIP" ]; then
    echo "  🌐 웹 페이지: http://localhost:3000"
    echo ""
fi
echo "  🔧 백엔드 API: http://localhost:8000"
echo "  📚 API 문서: http://localhost:8000/docs"
echo "  💚 헬스 체크: http://localhost:8000/health"
echo "  📊 통계: http://localhost:8000/stats"
echo "========================================"
echo ""
if [ -z "$FRONTEND_SKIP" ]; then
    echo "💡 프론트엔드 서버는 백그라운드에서 실행 중입니다."
    echo ""
fi
echo "⚠️  벡터 DB가 없으면 자동으로 초기화됩니다."
echo "   초기화에는 약 10-15분이 소요될 수 있습니다."
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo ""
echo "========================================"
echo ""

# 백엔드 API 서버 실행
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# 서버 종료 시 프론트엔드도 종료
if [ -z "$FRONTEND_SKIP" ] && [ ! -z "$FRONTEND_PID" ]; then
    echo ""
    echo "[정보] 프론트엔드 서버 종료 중..."
    kill $FRONTEND_PID 2>/dev/null
fi

