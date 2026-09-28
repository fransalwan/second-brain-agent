@echo off
title Second Brain Agent - Local Runner
echo =======================================================
echo   Second Brain Agent (Student Edition) - Local Runner
echo =======================================================
echo.
echo [1/2] Menyalakan Backend FastAPI dan Bot Telegram...
cd apps\backend
start "Second Brain Backend & Telegram Bot" cmd /k "uvicorn app.main:app --reload --port 8000"
cd ..\..

echo [2/2] Backend berhasil dijalankan!
echo       - Server API: http://localhost:8000
echo       - Bot Telegram: Aktif & siap menerima pesan
echo       - Web Dashboard: Dapat diakses via Netlify atau localhost
echo.
echo Tekan sembarang tombol untuk menutup launcher ini...
pause >nul
