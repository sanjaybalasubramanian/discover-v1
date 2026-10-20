@echo off
cls
echo ============================================================
echo    EMAIL TRACKING SERVER
echo ============================================================
echo.
echo Server starting on: http://localhost:8000
echo.
echo What you'll see when emails are opened:
echo   [Tracking] Email 999 opened (count: 1, detection: likely_bot)
echo   [Tracking] Email 999 opened (count: 2, detection: human_confirmed)
echo.
echo ============================================================
echo Ready! Now open your email in sanjaybalasubramanian171102@gmail.com
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

python tracking_server.py
