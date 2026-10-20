Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  🔥 TRACKING SERVER - STARTING NOW" -ForegroundColor Green  
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Server: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "WATCH THIS WINDOW!" -ForegroundColor Cyan
Write-Host "When you open an email, you'll see:" -ForegroundColor Cyan
Write-Host "  [TRACKING REQUEST] Email ID: X" -ForegroundColor Cyan
Write-Host "  ✅ TRACKED! Open Count: Y" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop server" -ForegroundColor Red
Write-Host ""

python start_server.py
