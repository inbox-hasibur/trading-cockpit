"""Unified supervisor and launcher for Humming Bird Trading Cockpit and Hermes Agent.

Starts:
1. Hermes Gateway on 127.0.0.1:8642 with profile 'hummingbird' and API server enabled.
2. FastAPI Cockpit server via Uvicorn on 127.0.0.1:8000.

Features:
- Auto-detects workspace virtualenv (.venv) and re-execs when called by system Python (e.g. 'npm run dev').
- Sets HERMES_HOME explicitly to resolve the Windows default bug.
- Verifies Gateway /health before starting Uvicorn.
- Cleans stale zombie processes holding ports 8642 or 8000.
- Supervises Gateway: restarts up to 3 times on unexpected crash.
- Clean shutdown on Ctrl+C (SIGINT/SIGTERM) killing process trees.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent


def get_venv_python() -> Optional[Path]:
    """Finds the virtual environment Python executable if it exists."""
    candidates = [
        WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe",
        WORKSPACE_ROOT / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    return None


def ensure_venv() -> None:
    """Ensures this script executes inside the workspace virtual environment.

    When invoked from global Python (e.g. via 'npm run dev' without active venv),
    this transparently re-executes using the workspace .venv interpreter.
    """
    venv_py = get_venv_python()
    if not venv_py:
        return

    try:
        if Path(sys.executable).resolve() == venv_py:
            return
    except Exception:
        pass

    env = os.environ.copy()
    venv_dir = str(venv_py.parent.parent)
    scripts_dir = str(venv_py.parent)
    env["VIRTUAL_ENV"] = venv_dir

    current_path = env.get("PATH", "")
    env["PATH"] = f"{scripts_dir}{os.pathsep}{current_path}"

    current_pythonpath = env.get("PYTHONPATH", "")
    paths = [str(WORKSPACE_ROOT)]
    if current_pythonpath:
        paths.append(current_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [str(venv_py), str(WORKSPACE_ROOT / "run.py")] + sys.argv[1:]
    try:
        ret = subprocess.call(cmd, env=env)
        sys.exit(ret)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"[Error] Failed to switch to virtual environment: {exc}", file=sys.stderr)
        sys.exit(1)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Fast check whether a TCP port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0


def free_port(port: int) -> None:
    """Frees a port if occupied by a stale zombie process on Windows."""
    if os.name != "nt" or not is_port_in_use(port):
        return
    try:
        cmd = f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
        pids = {p.strip() for p in res.stdout.splitlines() if p.strip().isdigit() and int(p.strip()) > 0}
        for pid in pids:
            if int(pid) != os.getpid():
                print(f"[Info] Port {port} is occupied by PID {pid}. Cleaning up stale process...")
                subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True)
    except Exception:
        pass


def kill_proc_tree(pid: int) -> None:
    """Kills a process and all its children."""
    if not pid:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        else:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        pass


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
    """Locates the hermes CLI binary, preferring the vendor/hermes-agent editable in .venv."""
    venv_exe = WORKSPACE_ROOT / ".venv" / "Scripts" / ("hermes.exe" if os.name == "nt" else "hermes")
    if venv_exe.exists():
        return str(venv_exe)
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
    # 1. Transparently ensure running under .venv
    ensure_venv()

    # Handle 'test' argument
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        venv_py = get_venv_python()
        py_bin = str(venv_py) if venv_py else sys.executable
        return subprocess.call([py_bin, "-m", "pytest", "-q"] + sys.argv[2:])

    # Handle 'live' argument
    if len(sys.argv) > 1 and sys.argv[1].lower() == "live":
        os.environ["TRADING_MODE"] = "LIVE_HOURS"

    # 2. Resolve HERMES_HOME explicitly (known Windows default bug)
    local_app = os.environ.get("LOCALAPPDATA")
    if "HERMES_HOME" not in os.environ and local_app:
        os.environ["HERMES_HOME"] = str(Path(local_app) / "hermes")

    # 3. Load environment variables
    load_env_file(WORKSPACE_ROOT / ".env")
    load_env_file(WORKSPACE_ROOT / "backend" / ".env")

    # Critical defaults for API server and Kernel
    os.environ.setdefault("API_SERVER_ENABLED", "true")
    os.environ.setdefault("API_SERVER_KEY", "hb-hermes-local-key-2026")
    os.environ.setdefault("API_SERVER_PORT", "8642")
    os.environ.setdefault("API_SERVER_HOST", "127.0.0.1")
    os.environ.setdefault("KERNEL_TOKEN", "hb-kernel-local-token-2026")
    os.environ.setdefault("HERMES_GATEWAY_URL", "http://127.0.0.1:8642")

    venv_py = get_venv_python()
    python_bin = str(venv_py) if venv_py else sys.executable
    hermes_bin = get_hermes_bin()

    def get_hermes_exec_cmd() -> list[str]:
        """Returns command args for Hermes CLI, preferring python -m to bypass Windows AppControl (WinError 4551)."""
        try:
            res = subprocess.run([python_bin, "-c", "import hermes_cli.main"], capture_output=True)
            if res.returncode == 0:
                return [python_bin, "-m", "hermes_cli.main"]
        except Exception:
            pass
        return [hermes_bin]

    hermes_exec_cmd = get_hermes_exec_cmd()

    # Build child process environment with venv and PYTHONPATH
    child_env = os.environ.copy()
    if venv_py:
        child_env["VIRTUAL_ENV"] = str(venv_py.parent.parent)
        scripts_dir = str(venv_py.parent)
        current_path = child_env.get("PATH", "")
        if not current_path.startswith(scripts_dir):
            child_env["PATH"] = f"{scripts_dir}{os.pathsep}{current_path}"
        current_pythonpath = child_env.get("PYTHONPATH", "")
        paths = [str(WORKSPACE_ROOT)]
        if current_pythonpath:
            paths.append(current_pythonpath)
        child_env["PYTHONPATH"] = os.pathsep.join(paths)
    child_env["PYTHONUNBUFFERED"] = "1"

    # 4. Clean up any stale zombie processes on ports 8642 or 8000
    free_port(8642)
    free_port(8000)

    print("==========================================================")
    print("   Humming Bird Cockpit & Hermes Gateway Unified Runner   ")
    print("==========================================================")
    print(f"HERMES_HOME : {os.environ.get('HERMES_HOME')}")
    print(f"Hermes Bin  : {' '.join(hermes_exec_cmd) if hermes_exec_cmd != [hermes_bin] else hermes_bin}")
    print(f"Python Bin  : {python_bin}")
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
            kill_proc_tree(backend_proc.pid)
            try:
                backend_proc.wait(timeout=2)
            except Exception:
                pass
            print(f"[Shutdown] Stopped backend server (PID {backend_proc.pid})")
        if gateway_proc and gateway_proc.poll() is None:
            kill_proc_tree(gateway_proc.pid)
            try:
                gateway_proc.wait(timeout=2)
            except Exception:
                pass
            print(f"[Shutdown] Stopped Hermes Gateway (PID {gateway_proc.pid})")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    def spawn_gateway() -> subprocess.Popen:
        cmd = [*hermes_exec_cmd, "-p", "hummingbird", "gateway", "run", "--force"]
        return subprocess.Popen(cmd, env=child_env)

    def spawn_backend() -> subprocess.Popen:
        cmd = [python_bin, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
        return subprocess.Popen(cmd, env=child_env)

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
