@echo off
REM 前端：Vite 开发服（默认 3000，/api 代理见 vite.config.ts）
cd /d "%~dp0frontend"
npm run dev -- --host 0.0.0.0 --port 3000