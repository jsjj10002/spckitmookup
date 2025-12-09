@echo off
chcp 65001 > nul
REM ========================================
REM Spckit AI 통합 개발 서버 실행 스크립트
REM ========================================
REM
REM 이 스크립트는 백엔드 API 서버와 프론트엔드 개발 서버를 모두 실행합니다.
REM 벡터 DB가 없으면 자동으로 초기화됩니다.
REM

echo.
echo ========================================
echo   Spckit AI Dev Server
echo ========================================
echo.

REM 프로젝트 루트로 이동
cd /d "%~dp0"

REM 가상 환경 확인
if not exist "backend\.venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] Virtual environment not found.
    echo.
    echo Please run setup_dev.bat first.
    echo.
    pause
    exit /b 1
)

REM .env 파일 확인
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found.
    echo.
    echo Please run setup_dev.bat to set up environment variables.
    echo.
    pause
    exit /b 1
)

REM Node.js 확인
echo [INFO] Checking Node.js installation...

node --version >nul 2>&1
if %errorlevel% equ 0 goto :NODE_FOUND

:NODE_MISSING
echo.
echo [WARNING] Node.js not found or not in PATH.
echo.
echo Node.js is required for the frontend server.
echo Install: https://nodejs.org/
echo.
echo Run backend only? (y/n)
set /p backend_only="> "
if /i not "%backend_only%"=="y" (
    pause
    exit /b 1
)
set FRONTEND_SKIP=1
goto :NODE_CHECK_END

:NODE_FOUND
echo [INFO] Node.js found.
:NODE_CHECK_END

REM 프론트엔드 의존성 확인
if not defined FRONTEND_SKIP (
    if not exist "node_modules" (
        echo.
        echo [정보] 프론트엔드 의존성이 설치되지 않았습니다.
        echo [정보] npm install을 실행합니다...
        echo.
        call npm install
        if errorlevel 1 (
            echo.
            echo [경고] npm install 실패. 프론트엔드 없이 진행합니다.
            set FRONTEND_SKIP=1
        )
    )
)

echo.
echo ========================================
echo   서버 시작 중...
echo ========================================
echo.

REM 가상 환경 활성화
echo [1/3] Activating backend virtual environment...
call backend\.venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM 프론트엔드 서버 시작 (새 창에서)
if not defined FRONTEND_SKIP (
    echo [2/3] Starting frontend development server...
    echo.
    echo [INFO] Starting frontend server in a new window...
    
    REM 프로젝트 루트 경로 저장
    set "PROJECT_ROOT=%CD%"
    
    REM start 명령어 개선: /D 옵션 대신 cd 명령어로 명시적 이동
    start "Spckit AI - Frontend Server" cmd /k "cd /d "%PROJECT_ROOT%" && echo Starting Frontend Server... && npm run dev"
    
    timeout /t 3 /nobreak >nul
    echo [DONE] Frontend server started in a new window.
    echo.
)

REM 백엔드 API 서버 실행
echo [3/3] Starting backend API server...
echo.
echo ========================================
echo   서버 정보
echo ========================================
if not defined FRONTEND_SKIP (
    echo   🌐 웹 페이지: http://localhost:3000
    echo.
)
echo   🔧 백엔드 API: http://localhost:8000
echo   📚 API 문서: http://localhost:8000/docs
echo   💚 헬스 체크: http://localhost:8000/health
echo   📊 통계: http://localhost:8000/stats
echo ========================================
echo.
if not defined FRONTEND_SKIP (
    echo 💡 프론트엔드 서버는 별도 창에서 실행 중입니다.
    echo.
)
echo ⚠️  벡터 DB가 없으면 자동으로 초기화됩니다.
echo    초기화에는 약 10-15분이 소요될 수 있습니다.
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
echo ========================================
echo.

REM 백엔드 API 서버 실행
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

REM 서버 종료 시 프론트엔드도 종료 안내
if not defined FRONTEND_SKIP (
    echo.
    echo [정보] 프론트엔드 서버 창도 닫아주세요.
)

pause
