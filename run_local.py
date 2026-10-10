"""Run the private, single-user LoopingCV preview on this computer."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    data = root / "data"
    data.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment["AUTOJOB_LOCAL_DEV"] = "1"
    # Always use local storage, even if the shell has a hosted database configured.
    environment["AUTOJOB_DATABASE_URL"] = "sqlite:///" + (data / "development.db").as_posix()
    print("Starting LoopingCV on http://localhost:8502", flush=True)
    print("Local preview: one workspace, email sending disabled. Press Ctrl+C to stop.", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(root / "streamlit_app.py"),
             "--server.address=127.0.0.1", "--server.port=8502",
             "--server.headless=false", "--server.showEmailPrompt=false",
             "--browser.gatherUsageStats=false"],
            cwd=root, env=environment, check=False,
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
