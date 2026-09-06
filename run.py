import os
import subprocess
import uvicorn
import webbrowser
import threading
import time

HOST = "127.0.0.1"
PORT = 8000

# Manager-portal password used when the app is started via run.py / share.bat.
# An explicitly set MANAGER_PASSWORD environment variable (e.g. on Render) still wins.
os.environ.setdefault("MANAGER_PASSWORD", "smarthire2026")


def free_port(port):
    """Stop any stale process still listening on `port` so a fresh start always runs the
    current code. Without this, a leftover server can keep serving an OLD build and cause
    confusing "my change didn't take effect" behaviour. Windows-focused (netstat/taskkill);
    a no-op elsewhere."""
    if os.name != "nt":
        return
    try:
        out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return
    pids = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[1].endswith(f":{port}") and parts[3].upper() == "LISTENING":
            pid = parts[4]
            if pid and pid != "0":
                pids.add(pid)
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/F", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  Freed port {port}: stopped a stale server (PID {pid}).")
        except Exception:
            pass
    if pids:
        time.sleep(1.0)


def open_browser():
    time.sleep(1.5)
    print(f"\n[SmartHire Finance] Launching browser at http://{HOST}:{PORT} ...")
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print("=" * 70)
    print("  SmartHire Finance — AI Candidate Assessment & Hiring Intelligence")
    print("  Packaging & Manufacturing (Corrugation, Cartons, Flexible, Labels)")
    print("=" * 70)
    free_port(PORT)
    print(f"  Server starting at: http://{HOST}:{PORT}")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 70)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=False)
