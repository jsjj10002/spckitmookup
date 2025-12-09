@echo off
chcp 65001 > nul
REM ========================================
REM Spckit AI Setup Script
REM ========================================
REM
REM This script automatically sets up the development environment:
REM   1. Check and install uv
REM   2. Create virtual environment
REM   3. Install dependencies
REM   4. Create .env file
REM   5. Initialize Vector DB (optional)
REM

echo.
echo ========================================
echo   Spckit AI Development Setup
echo ========================================
echo.
echo This script will automatically set up your development environment.
echo.

REM 프로젝트 루트로 이동
cd /d "%~dp0"

REM Python 확인
echo [INFO] Checking Python installation...
set PYTHON_CMD=python

where python >nul 2>&1
if %errorlevel% equ 0 goto :PYTHON_FOUND

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :PYTHON_FOUND
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :PYTHON_FOUND
)

:PYTHON_MISSING
echo.
echo [ERROR] Python not found.
echo.
echo Diagnostic Info:
echo   - where python result:
where python
echo   - where py result:
where py
echo   - where python3 result:
where python3
echo.
echo Python 3.10+ is required.
echo Install: https://www.python.org/downloads/
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [INFO] Python found: %PYTHON_CMD%

REM setup_dev.py 실행
echo [INFO] Running setup script...
echo.
%PYTHON_CMD% backend\scripts\setup_dev.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   설정 실패
    echo ========================================
    echo.
    echo 설정 중 오류가 발생했습니다.
    echo 위의 오류 메시지를 확인해주세요.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   설정 완료!
echo ========================================
echo.
pause

