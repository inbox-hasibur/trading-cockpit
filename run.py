"""Unified supervisor and launcher for Humming Bird Trading Cockpit and Hermes Agent.

Starts:
1. Hermes Gateway on 127.0.0.1:8642 with profile 'hummingbird' and API server enabled.
2. FastAPI Cockpit server via Uvicorn on 127.0.0.1:8000.

Features:
- Sets HERMES_HOME explicitly to resolve the Windows default bug.
- Verifies Gateway /health before starting Uvicorn.
- Supervises Gateway: restarts up to 3 times on unexpected crash.
- Clean shutdown on Ctrl+C (SIGINT/SIGTERM) killing both child processes.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent


def load_env_file(filepath: Path) -> None:
    """Loads key-value pairs from a .env file into os.environ if not already set."""
    if not filepath.exists():
        return
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception as exc:
        print(f"[Warning] Failed reading {filepath}: {exc}", file=sys.stderr)


def get_hermes_bin() -> str:
    """Locates the official hermes CLI binary."""
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        hermes_exe = Path(local_app) / "hermes" / "bin" / ("hermes.exe" if os.name == "nt" else "hermes")
        if hermes_exe.exists():
            return str(hermes_exe)
    return "hermes"


def check_gateway_health(url: str = "http://127.0.0.1:8642/health", timeout: float = 1.0) -> bool:
    """Checks if Hermes Gateway returns HTTP 200 on /health."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def wait_for_gateway(proc: subprocess.Popen, timeout_sec: int = 30) -> bool:
    """Polls gateway health until ready or timeout."""
    sys.stdout.write("Waiting for Hermes Gateway on 127.0.0.1:8642...")
    sys.stdout.flush()
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        if proc.poll() is not None:
            sys.stdout.write(f" FAILED (Gateway process exited with code {proc.returncode})\n")
            return False
        if check_gateway_health():
            sys.stdout.write(" HEALTHY\n")
            return True
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write(" TIMEOUT\n")
    return False


def main() -> int:
    # 1. Resolve HERMES_HOME explicitly (known Windows default bug)
    local_app = os.environ.get("LOCALAPPDATA")
    if "HERMES_HOME" not in os.environ and local_app:
        os.environ["HERMES_HOME"] = str(Path(local_app) / "hermes")

    # 2. Load environment variables
    load_env_file(WORKSPACE_ROOT / ".env")
    load_env_file(WORKSPACE_ROOT / "backend" / ".env")

    # Defaults for API server and Kernel
    os.environ.setdefault("API_SERVER_ENABLED", "true")
    os.environ.setdefault("API_SERVER_KEY", "hb-hermes-local-key-2026")
    os.environ.setdefault("API_SERVER_PORT", "8642")
    os.environ.setdefault("API_SERVER_HOST", "127.0.0.1")
    os.environ.setdefault("KERNEL_TOKEN", "hb-kernel-local-token-2026")
    os.environ.setdefault("HERMES_GATEWAY_URL", "http://127.0.0.1:8642")

    hermes_bin = get_hermes_bin()
    python_bin = sys.executable

    print("==========================================================")
    print("   Humming Bird Cockpit & Hermes Gateway Unified Runner   ")
    print("==========================================================")
    print(f"HERMES_HOME : {os.environ.get('HERMES_HOME')}")
    print(f"Hermes Bin  : {hermes_bin}")
    print("Profile     : hummingbird")
    print("Gateway URL : http://127.0.0.1:8642")
    print("Cockpit URL : http://127.0.0.1:8000")
    print("==========================================================")

    gateway_proc: Optional[subprocess.Popen] = None
    backend_proc: Optional[subprocess.Popen] = None
    shutdown_requested = False

    def shutdown(*args):
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        print("\n[Shutdown] Stopping Humming Bird Cockpit and Hermes Gateway...")
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend_proc.kill()
            print(f"[Shutdown] Stopped backend server (PID {backend_proc.pid})")
        if gateway_proc and gateway_proc.poll() is None:
            gateway_proc.terminate()
            try:
                gateway_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                gateway_proc.kill()
            print(f"[Shutdown] Stopped Hermes Gateway (PID {gateway_proc.pid})")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    def spawn_gateway() -> subprocess.Popen:
        cmd = [hermes_bin, "-p", "hummingbird", "gateway", "run", "--force"]
        return subprocess.Popen(cmd, env=os.environ.copy())

    def spawn_backend() -> subprocess.Popen:
        cmd = [python_bin, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
        return subprocess.Popen(cmd, env=os.environ.copy())

    max_restarts = 3
    restart_count = 0

    try:
        # Start gateway
        print("Starting Hermes Gateway (profile: hummingbird)...")
        gateway_proc = spawn_gateway()
        if not wait_for_gateway(gateway_proc, timeout_sec=30):
            print("[Error] Hermes Gateway failed to start.", file=sys.stderr)
            shutdown()
            return 1

        # Start backend
        print("Starting Cockpit backend on 127.0.0.1:8000...")
        backend_proc = spawn_backend()

        print("\nAll services active!")
        print("Cockpit UI: http://127.0.0.1:8000")
        print("Press Ctrl+C to terminate all services.\n")

        # Supervisor loop
        while not shutdown_requested:
            time.sleep(1.0)
            if backend_proc.poll() is not None:
                print(f"[Alert] Backend server exited with code {backend_proc.returncode}.")
                break

            if gateway_proc.poll() is not None and not shutdown_requested:
                restart_count += 1
                print(f"\n[ALERT] Hermes Gateway process exited unexpectedly (code {gateway_proc.returncode}).")
                if restart_count <= max_restarts:
                    print(f"[SUPERVISOR] Restarting Hermes Gateway (Attempt {restart_count} of {max_restarts})...")
                    gateway_proc = spawn_gateway()
                    if wait_for_gateway(gateway_proc, timeout_sec=20):
                        print("[SUPERVISOR] Gateway successfully recovered and healthy!")
                    else:
                        print("[SUPERVISOR] Gateway recovery failed.")
                else:
                    print(f"[ERROR] Hermes Gateway has crashed repeatedly (exceeded {max_restarts} restarts).", file=sys.stderr)
                    break
    finally:
        shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
