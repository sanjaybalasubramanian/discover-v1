#!/usr/bin/env python
"""
Smart runner - runs preflight checks before executing pipeline
"""
import sys
import subprocess

def main():
    """Run preflight checks, then pipeline if checks pass"""
    print("Running pre-flight checks...")
    print()
    
    # Run checks
    result = subprocess.run([sys.executable, "preflight.py"])
    
    if result.returncode == 0:
        print()
        print("🚀 Starting pipeline...")
        print()
        # Run pipeline
        subprocess.run([sys.executable, "-m", "app.cli", "run"])
    else:
        print()
        print("❌ Fix errors above before running pipeline")
        sys.exit(1)

if __name__ == "__main__":
    main()
