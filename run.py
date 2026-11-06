"""
Humming Bird Trading Cockpit - Universal Live Runner
---------------------------------------------------
Single command launcher mimicking `npm run dev` from Next.js.
Supports:
  - npm run dev / npm run live
  - python run.py [live]
  - ./run.sh
  - run.bat (or just `run` in CMD/PowerShell)

Automatically activates `.venv` if present, validates dependencies,
and starts the FastAPI live reload server with colored terminal feedback.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Ensure the root directory is in sys.path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def ensure_venv() -> None:
    """If running under system Python, re-exec under .venv Python if available."""
    venv_py_win = ROOT / ".venv" / "Scripts" / "python.exe"
    venv_py_nix = ROOT / ".venv" / "bin" / "python"
    venv_py = venv_py_win if sys.platform == "win32" else venv_py_nix

    if venv_py.exists():
        try:
            curr = Path(sys.executable).resolve()
            target = venv_py.resolve()
            if curr != target:
                args = [str(target), str(Path(__file__).resolve())] + sys.argv[1:]
                sys.exit(subprocess.call(args))
        except Exception:
            pass


def print_banner(host: str, port: int, reload: bool) -> None:
    mode_str = "Live Reload (Hot Reload)" if reload else "Production Mode"
    print("\n\033[1;36m  ▲ Humming Bird Trading Cockpit\033[0m")
    print(f"\033[90m  - Local Terminal:  \033[0m\033[1;32mhttp://{host}:{port}\033[0m")
    print(f"\033[90m  - API Documentation:\033[0m\033[1;34m http://{host}:{port}/docs\033[0m")
    print(f"\033[90m  - Telemetry Stream: \033[0m\033[1;35m http://{host}:{port}/api/stream\033[0m")
    print(f"\033[90m  - Engine Status:    \033[0m\033[1;33m{mode_str}\033[0m")
    print("\033[90m  Press Ctrl+C to stop.\033[0m\n")


def check_port_in_use(host: str, port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, OSError):
            return False


def main() -> None:
    ensure_venv()

    parser = argparse.ArgumentParser(
        description="Humming Bird Trading Cockpit Universal Runner",
        add_help=True,
    )
    # Allow positional subcommand like "live", "dev", "test" (e.g. `python run.py live`)
    parser.add_argument(
        "subcommand",
        nargs="?",
        default="live",
        help="Command to run: 'live', 'dev', 'start', or 'test'",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--open", "-o", action="store_true", help="Open cockpit in default browser")
    parser.add_argument("--test", action="store_true", help="Run pytest suite instead of server")

    args, unknown = parser.parse_known_args()

    # Handle test mode
    if args.test or args.subcommand in ("test", "tests"):
        print("\033[1;34mRunning Humming Bird test suite...\033[0m\n")
        cmd = [sys.executable, "-m", "pytest", "-q"] + unknown
        sys.exit(subprocess.call(cmd))

    # Check dependencies
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401
    except ImportError:
        print("\033[1;31mError: Required dependencies (uvicorn, fastapi) are missing.\033[0m")
        print("\nPlease run:")
        print("  py -3.12 -m venv .venv")
        print("  .venv\\Scripts\\pip install -r backend/requirements.txt\n")
        sys.exit(1)

    host = args.host
    port = args.port
    reload = not args.no_reload and args.subcommand != "start"

    if check_port_in_use(host, port):
        print(f"\033[1;33mWarning: Port {port} is already in use.\033[0m")
        print(f"If another Humming Bird instance is running, open http://{host}:{port} or use --port {port+1}\n")

    print_banner(host, port, reload)

    if args.open:
        import threading
        import time
        import webbrowser

        def _open():
            time.sleep(1.2)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_open, daemon=True).start()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        # Run uvicorn process directly
        return_code = subprocess.call(cmd)
        sys.exit(return_code)
    except KeyboardInterrupt:
        print("\n\033[90mHumming Bird stopped.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
