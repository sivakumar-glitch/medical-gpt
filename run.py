"""
run.py  –  Build & start backend (FastAPI/Uvicorn) + frontend (Next.js) in
           PRODUCTION mode with a single command.

Usage:
    python run.py

Press Ctrl+C to stop both servers.
"""
import os
import sys
import shutil
import signal
import subprocess
import threading

# ── paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "frontend")
BACKEND_DIR = os.path.join(ROOT, "backend")
NEXT_CACHE   = os.path.join(FRONTEND_DIR, ".next")

# npm executable (npm.cmd on Windows)
NPM = "npm.cmd" if sys.platform == "win32" else "npm"

# ── helpers ──────────────────────────────────────────────────────────────────
def stream_output(proc: subprocess.Popen, label: str) -> None:
    for line in iter(proc.stdout.readline, b""):
        print(f"[{label}] {line.decode('utf-8', errors='replace').rstrip()}", flush=True)


def run_step(label: str, cmd: list, cwd: str) -> tuple[int, str]:
    """Run a blocking subprocess and stream its output."""
    print(f"\n[run.py] {label} …")
    proc = subprocess.Popen(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output_lines: list[str] = []
    for line in iter(proc.stdout.readline, b""):
        decoded = line.decode('utf-8', errors='replace').rstrip()
        output_lines.append(decoded)
        print(f"[{label.lower()}] {decoded}", flush=True)
    proc.wait()
    return proc.returncode, "\n".join(output_lines)


def clean_next_cache() -> None:
    """Delete stale .next folder to avoid EINVAL / readlink errors on Windows."""
    if os.path.exists(NEXT_CACHE):
        print(f"[run.py] Removing stale .next cache …")
        shutil.rmtree(NEXT_CACHE, ignore_errors=True)


def start_backend() -> subprocess.Popen:
    print("[run.py] Starting backend (production) …")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = BACKEND_DIR + (os.pathsep + existing if existing else "")
    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "1",
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def start_frontend() -> subprocess.Popen:
    print("[run.py] Starting frontend (production) …")
    env = os.environ.copy()
    env.setdefault("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1")
    return subprocess.Popen(
        [NPM, "run", "start"],
        cwd=FRONTEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )


def main() -> None:
    # ── 1. Clean stale Next.js cache (fixes EINVAL on Windows/OneDrive) ──────
    clean_next_cache()

    # ── 2. Build Next.js for production ──────────────────────────────────────
    code, build_output = run_step("Building frontend", [NPM, "run", "build"], FRONTEND_DIR)
    if code != 0:
        lower = build_output.lower()
        transient_next_errors = (
            "pages-manifest.json" in lower or
            "readlink" in lower or
            "einval" in lower or
            "enoent" in lower
        )
        if transient_next_errors:
            print("[run.py] Detected transient Next.js build artifact error; retrying once …")
            clean_next_cache()
            code, _ = run_step("Rebuilding frontend", [NPM, "run", "build"], FRONTEND_DIR)
        if code != 0:
            print(f"[run.py] ERROR: '{NPM} run build' failed after retry.")
            sys.exit(code)

    # ── 3. Launch both servers concurrently ──────────────────────────────────
    backend  = start_backend()
    frontend = start_frontend()

    t_back  = threading.Thread(target=stream_output, args=(backend,  "backend"),  daemon=True)
    t_front = threading.Thread(target=stream_output, args=(frontend, "frontend"), daemon=True)
    t_back.start()
    t_front.start()

    print("\n[run.py] Both servers running.")
    print("[run.py]   Backend  → http://localhost:8000  (docs: /docs)")
    print("[run.py]   Frontend → http://localhost:3000")
    print("[run.py] Press Ctrl+C to stop.\n")

    def shutdown(sig=None, frame=None) -> None:
        print("\n[run.py] Shutting down …")
        for proc in (frontend, backend):
            try:
                proc.terminate()
            except Exception:
                pass
        for proc in (frontend, backend):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("[run.py] Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    backend.wait()
    frontend.wait()


if __name__ == "__main__":
    main()

