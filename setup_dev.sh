#!/bin/bash
# ========================================
# Spckit AI 개발 환경 자동 설정 스크립트
# ========================================
#
# 이 스크립트는 다음을 자동으로 수행합니다:
#   1. uv 설치 확인 및 설치
#   2. 가상 환경 생성
#   3. 의존성 설치
#   4. 환경 변수 파일 생성
#   5. 벡터 DB 초기화 (선택사항)
#

echo ""
echo "========================================"
echo "  Spckit AI 개발 환경 자동 설정"
echo "========================================"
echo ""
echo "이 스크립트는 개발 환경을 자동으로 설정합니다."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# Python이 설치되어 있는지 확인
if ! command -v python3 &> /dev/null; then
    echo "[오류] Python이 설치되어 있지 않습니다."
    echo ""
    echo "진단 정보:"
    echo "  - command -v python3 결과: $(command -v python3)"
    echo "  - python3 --version 결과: $(python3 --version 2>&1)"
    echo ""
    echo "Python 3.10 이상을 설치해주세요: https://www.python.org/downloads/"
    exit 1
fi

# setup_dev.py 실행
echo "[정보] Python 스크립트를 실행합니다..."
echo ""
python3 backend/scripts/setup_dev.py

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "  설정 실패"
    echo "========================================"
    echo ""
    echo "설정 중 오류가 발생했습니다."
    echo "위의 오류 메시지를 확인해주세요."
    exit 1
fi

echo ""
echo "========================================"
echo "  설정 완료!"
echo "========================================"
echo ""

