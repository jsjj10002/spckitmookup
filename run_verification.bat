@echo off
echo Starting verification...
cd /d %~dp0backend
C:\Users\nrtak\.local\bin\uv.exe run python tests/verify_rag_scenario.py
if %ERRORLEVEL% NEQ 0 (
    echo Command failed.
)
echo Done.

