import sys
from pathlib import Path

# Make the repository root importable when Vercel executes this function.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

# FastAPI ASGI entry point for Vercel Python functions.