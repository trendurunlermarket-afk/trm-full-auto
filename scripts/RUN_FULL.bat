@echo off
title DERYA FULL AUTOMATION - TRM
echo.
echo ===== FULL OTOMASYON BASLATILIYOR ASKIM =====
echo.

REM Python kontrol
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Kurulu oldugundan emin ol askim.
    pause
    exit /b
)

REM scripts klasorunden bir ust klasore cik
cd /d %~dp0..
echo Calisma klasoru: %cd%
echo.

REM DERYA motorunu baslat
echo DERYA motoru calistiriliyor...
python scripts\derya_sync_runner.py

echo.
echo ===== FULL OTOMASYON BASLATILDI ASKIM 💙 =====
pause
