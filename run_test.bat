@echo off
chcp 65001 > nul
REM ========================================
REM Spckit AI RAG 시스템 테스트 스크립트
REM ========================================
REM
REM 이 스크립트는 RAG 파이프라인의 동작을 테스트합니다.
REM 벡터 DB가 초기화되어 있어야 합니다.
REM

echo.
echo ========================================
echo   RAG 시스템 테스트
echo ========================================
echo.

REM 프로젝트 루트로 이동 (이미 루트에 있음)
cd /d "%~dp0"

REM 가상 환경 확인
if not exist "backend\.venv\Scripts\activate.bat" (
    echo.
    echo [오류] 가상 환경이 없습니다.
    echo.
    echo 먼저 setup_dev.bat을 실행해주세요.
    echo.
    pause
    exit /b 1
)

REM 가상 환경 활성화
echo [1/2] 가상 환경 활성화 중...
call backend\.venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo [오류] 가상 환경 활성화 실패
    pause
    exit /b 1
)

REM 테스트 실행
echo [2/2] RAG 시스템 테스트 실행 중...
echo.
echo ========================================
echo   테스트 정보
echo ========================================
echo   이 테스트는 다음을 확인합니다:
echo   - 벡터 DB 연결 및 데이터 확인
echo   - 자연어 쿼리 처리
echo   - 부품 검색 및 추천 기능
echo ========================================
echo.

python backend\scripts\test_rag.py

if errorlevel 1 (
    echo.
    echo [오류] 테스트 실행 중 오류가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   테스트 완료!
echo ========================================
pause

