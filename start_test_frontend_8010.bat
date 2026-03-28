@echo off
setlocal
cd /d "%~dp0frontend"
set CRM_API_TARGET=http://127.0.0.1:8010
npm run dev
