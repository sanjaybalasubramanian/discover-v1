#!/usr/bin/env python
"""
Install git hooks
"""
import os
import shutil
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    hooks_dir = repo_root / ".git" / "hooks"
    
    if not hooks_dir.exists():
        print("❌ .git/hooks directory not found")
        print("   Make sure you're in a git repository")
        return 1
    
    # Copy pre-commit hook
    source = repo_root / "scripts" / "pre-commit"
    dest = hooks_dir / "pre-commit"
    
    shutil.copy(source, dest)
    
    # Make executable (Unix)
    if os.name != 'nt':
        os.chmod(dest, 0o755)
    
    print("✅ Git hooks installed")
    print("   Pre-commit hook will run linting before each commit")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
