# Deploying SmartHire Finance to Render

One web service hosts **both portals at the same URL**:

- **Candidate portal** — the main page (`/`). Open to anyone with the link.
- **Manager portal** — the *Manager Intelligence Portal* tab. **Password-protected**; the
  password is set with the `MANAGER_PASSWORD` environment variable and the manager API
  endpoints reject any request without it.

---

## 1. One-time prep (local)

1. Make sure secrets/data are **not** committed. A `.gitignore` is already included that
   excludes the SQLite database, uploaded resumes, backups, and the virtualenv. Verify:
   ```
   git status --short        # smarthire.db, backend/uploads/, .venv/ must NOT appear
   ```
   If `backend/smarthire.db` was ever committed before, untrack it (keeps your local copy):
   ```
   git rm --cached backend/smarthire.db
   ```
2. Commit and push to a GitHub (or GitLab) repository:
   ```
   git add .
   git commit -m "Prepare SmartHire Finance for Render deploy"
   git push origin main
   ```

The question bank (`backend/app/data/bank_*.json`) **is** committed — the app needs it.

---

## 2. Deploy on Render (Blueprint — easiest)

1. Push includes `render.yaml`. In Render, click **New + → Blueprint**.
2. Connect the repository. Render reads `render.yaml` and proposes a **web service**
   `smarthire-finance` with a **1 GB persistent disk** mounted at `/var/data`.
3. When prompted, set the one secret value:
   - **`MANAGER_PASSWORD`** → choose a strong password. This is what managers type to open
     the Manager portal.
4. Click **Apply / Create**. Render runs:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. First boot creates the database and `uploads/` folder on the disk automatically.
6. Open the service URL (e.g. `https://smarthire-finance.onrender.com`):
   - Candidates use it directly.
   - Managers click **Manager Intelligence Portal → enter the password**.

### Manual alternative (no Blueprint)
New + → **Web Service** → connect repo → Runtime **Python 3** →
Build `pip install -r requirements.txt` → Start
`uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.
Then add a **Disk** (mount `/var/data`, 1 GB) and the env vars:
`MANAGER_PASSWORD`, `DATABASE_URL=sqlite:////var/data/smarthire.db`,
`UPLOAD_DIR=/var/data/uploads`, `PYTHON_VERSION=3.12.10`.

---

## 3. Free plan (no persistent disk)

Render disks require a paid instance. To try it on the **free** plan, in `render.yaml`:
- delete the `disk:` block, and
- delete the `DATABASE_URL` and `UPLOAD_DIR` env vars (the app falls back to paths inside
  the container).

⚠️ On free, the container filesystem is **ephemeral**: the database and uploaded resumes
are **wiped whenever the service restarts, redeploys, or wakes from sleep**. Fine for a demo;
use the paid disk (or a Postgres migration) for anything you need to keep.

---

## 4. Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `MANAGER_PASSWORD` | Password for the Manager portal (**set this!**) | `a-strong-secret` |
| `DATABASE_URL` | SQLite location (point at the disk) | `sqlite:////var/data/smarthire.db` |
| `UPLOAD_DIR` | Where resumes are stored | `/var/data/uploads` |
| `PYTHON_VERSION` | Python runtime | `3.12.10` |

If `MANAGER_PASSWORD` is not set, it defaults to `admin123` (local dev only — **always**
set a real one in production).

---

## 5. Run locally

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
.venv/Scripts/python.exe run.py                               # opens http://127.0.0.1:8000
```
`run.py` frees port 8000 first so a stale server can't serve old code. The local manager
password is `admin123` unless you set `MANAGER_PASSWORD`.
