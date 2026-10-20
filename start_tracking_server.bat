@echo off
echo ============================================================
echo Starting Email Tracking Server
echo ============================================================
echo.
echo Server will run on: http://localhost:8000
echo.
echo Endpoints:
echo   GET /track/open/{outreach_id}     - Track email opens
echo   GET /track/click/{outreach_id}    - Track link clicks  
echo   GET /stats/{campaign_id}          - Get campaign stats
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

python tracking_server.py
