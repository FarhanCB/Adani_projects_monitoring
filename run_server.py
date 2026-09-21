import os
import sys

# If we are not inside backend venv, re-exec with venv python if available
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, "backend", ".venv", "Scripts", "python.exe")
if os.path.isfile(venv_python) and sys.executable.lower() != os.path.abspath(venv_python).lower():
    import subprocess
    sys.exit(subprocess.call([venv_python, __file__] + sys.argv[1:]))

# Ensure backend directory is in python path
backend_path = os.path.join(current_dir, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    host = getattr(settings, "HOST", "0.0.0.0") or "0.0.0.0"
    port = int(os.getenv("PORT", getattr(settings, "PORT", 8008) or 8008))
    print(f"Starting {settings.PROJECT_NAME} on http://{host}:{port}...")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)

