import uvicorn
from tracking_server_debug import app

print("\n" + "="*60)
print("🔥 TRACKING SERVER - REAL TIME")
print("="*60)
print("\nServer starting on http://localhost:8000")
print("\nWhen email is opened, you'll see activity HERE!")
print("\n" + "="*60 + "\n")

uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
