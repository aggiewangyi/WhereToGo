@echo off
REM WhereToGo Service - starting development server
REM 用于在 Windows 环境下快速启动 FastAPI 开发服务器

echo ========================================
echo WhereToGo Service - starting development server
echo ========================================
echo.

REM 激活 conda 环境
echo activating conda environment: wheretogo
call conda activate wheretogo
if errorlevel 1 (
    echo warning: conda environment activation failed, please ensure that the wheretogo environment has been created
    echo continuing to use the current environment...
)

poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause