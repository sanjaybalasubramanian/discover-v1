# REAL TRACKING TEST - Step by Step

## YOU DO THIS:

### Step 1: Start Server (in a separate PowerShell window)
```powershell
cd v:/discover
python -m uvicorn tracking_server_debug:app --host 0.0.0.0 --port 8000
```

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8000`

### Step 2: Test Tracking (in THIS window)
```powershell
# This simulates what happens when someone opens an email
curl http://localhost:8000/track/open/1
```

### Step 3: Check if it tracked
```powershell
python check_tracking_status.py
```

You should see `open_count` increased!

---

## OR USE THIS AUTOMATED TEST:

I'll create a script that does REAL HTTP tracking (not fake database calls)
