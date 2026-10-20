@echo off
echo.
echo ========================================
echo    Starting Job Outreach Pipeline
echo ========================================
echo.
echo Server will start on: http://localhost:8000
echo Dashboard URL: http://localhost:8000/dashboard/
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
