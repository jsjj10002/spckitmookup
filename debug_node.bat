@echo off
chcp 65001 > nul
echo ========================================
echo   Node.js 진단 스크립트
echo ========================================
echo.
echo [1] node --version 실행 시도:
node --version
echo ErrorLevel: %errorlevel%
echo.
echo [2] where node 실행 시도:
where node
echo ErrorLevel: %errorlevel%
echo.
echo [3] 환경 변수 PATH 확인:
echo %PATH%
echo.
pause
