# BSI Internal Document Search Engine

A filename-based search engine for BSI internal documents, with role-based access control.

**Stack:** FastAPI + Meilisearch + React + Tailwind CSS v4

> This README is written for **Windows 10 / 11** users.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Python](#2-install-python)
3. [Install Node.js](#3-install-nodejs)
4. [Install Meilisearch](#4-install-meilisearch)
5. [Clone the project](#5-clone-the-project)
6. [Backend setup](#6-backend-setup)
7. [Frontend setup](#7-frontend-setup)
8. [Create admin user](#8-create-admin-user-first-time-only)
9. [Run the project](#9-run-the-project)
10. [Run tests](#10-run-tests)
11. [Configuration](#11-configuration)
12. [Troubleshooting](#12-troubleshooting)
13. [Features](#13-features)
14. [Project structure](#14-project-structure)

---

## 1. Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Git | latest | <https://git-scm.com/download/win> |
| Python | 3.9+ | <https://www.python.org/downloads/windows/> |
| Node.js | 18+ LTS | <https://nodejs.org/> |
| Meilisearch | 1.x | <https://github.com/meilisearch/meilisearch/releases> |

All commands below use **PowerShell** (built into Windows). Open it via
**Start → "Windows PowerShell"**.

---

## 2. Install Python

1. Download the **Windows installer (64-bit)** from <https://www.python.org/downloads/windows/>.
2. Run the installer.
3. **Check** the box **"Add python.exe to PATH"** before clicking *Install Now*.
4. Verify in a **new** PowerShell window:
   ```powershell
   python --version
   ```

---

## 3. Install Node.js

1. Download the **LTS** version from <https://nodejs.org/>.
2. Run the installer (keep default settings).
3. Verify in a new PowerShell window:
   ```powershell
   node --version
   npm --version
   ```

---

## 4. Install Meilisearch

1. Go to <https://github.com/meilisearch/meilisearch/releases>.
2. Download `meilisearch-windows-amd64.exe` from the latest release.
3. Create a folder, e.g. `C:\meilisearch`, and move the file there.
4. Rename it to `meilisearch.exe`.
5. **Add the folder to PATH:**
   - Press *Start* → search **"Environment variables"** → open
     *"Edit the system environment variables"*.
   - Click **Environment Variables…**
   - Under *System variables*, select **Path** → **Edit** → **New** →
     add `C:\meilisearch` → OK on all dialogs.
6. Verify in a new PowerShell window:
   ```powershell
   meilisearch --version
   ```

> If Windows Defender / SmartScreen blocks the `.exe`, right-click it →
> *Properties* → check **"Unblock"** → OK.

---

## 5. Clone the project

```powershell
cd C:\Users\$env:USERNAME
git clone https://github.com/<your-username>/<your-repo>.git bsi_project
cd bsi_project
```

> Replace `<your-username>/<your-repo>` with your actual GitHub repository.

---

## 6. Backend setup

### Allow venv activation in PowerShell (one time per session)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Create the virtual environment and install dependencies

```powershell
cd C:\Users\$env:USERNAME\bsi_project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

You should now see `(venv)` at the start of the PowerShell prompt.

---

## 7. Frontend setup

In a **new** PowerShell window:

```powershell
cd C:\Users\$env:USERNAME\bsi_project\frontend
npm install
```

---

## 8. Create admin user (first time only)

With the venv active:

```powershell
cd C:\Users\$env:USERNAME\bsi_project\backend
python setup.py
```

This creates the SQLite database and a default admin user:

| Field | Value |
|------|-------|
| Username | `admin` |
| Password | `admin123` |

> **Change the password after first login.**

---

## 9. Run the project

You need **three PowerShell windows** running at the same time.

### Terminal 1 — Meilisearch

```powershell
meilisearch --master-key=bsiSecretKey123
```

### Terminal 2 — Backend (FastAPI)

```powershell
cd C:\Users\$env:USERNAME\bsi_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Terminal 3 — Frontend (Vite)

```powershell
cd C:\Users\$env:USERNAME\bsi_project\frontend
npm run dev
```

### Open the app

Go to **<http://localhost:5173>** in your browser.

---

### Alternative startup (no PATH / no venv activation)

If `meilisearch` is not on PATH, or PowerShell blocks `Activate.ps1`, or
`npm` is not recognized in your shell, use these commands instead.
Replace `<PROJECT_PATH>` with the absolute path to your project
(e.g. `C:\Users\YourName\bsi_project`) and `<MEILI_PATH>` with the folder
where `meilisearch.exe` lives (e.g. `C:\meilisearch`).

**Terminal 1 — Meilisearch (no PATH needed):**
```powershell
<MEILI_PATH>\meilisearch.exe --master-key=bsiSecretKey123
```

**Terminal 2 — Backend (run uvicorn directly from venv, no activation):**
```powershell
Set-Location "<PROJECT_PATH>\backend"
& "<PROJECT_PATH>\venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000
```

**Terminal 3 — Frontend (reload system PATH if `npm` is not recognized):**
```powershell
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
Set-Location "<PROJECT_PATH>\frontend"
npm run dev
```

---

## 10. Run tests

```powershell
cd C:\Users\$env:USERNAME\bsi_project
.\venv\Scripts\Activate.ps1
pytest backend\tests\ -v
```

---

## 11. Configuration

Edit `backend\.env`:

```env
DATA_FOLDER=..\tilgang\tilgang
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_KEY=bsiSecretKey123
JWT_SECRET=change-this-secret-in-production
```

| Variable | Description |
|---------|-------------|
| `DATA_FOLDER` | Path to the BSI document root (relative to `backend/`). |
| `MEILISEARCH_URL` | Where Meilisearch is running. |
| `MEILISEARCH_KEY` | Must match the `--master-key` you start Meilisearch with. |
| `JWT_SECRET` | **Must be changed** before production. Use a long random string. |

### Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI) | 8000 |
| Meilisearch | 7700 |

---

## 12. Troubleshooting

**`python` is not recognized**
You forgot to check *"Add Python to PATH"* during install. Re-run the
installer → *Modify* → enable the PATH option.

**`Activate.ps1 cannot be loaded because running scripts is disabled`**
Run this in the same PowerShell window before activating:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

**`meilisearch` is not recognized**
PATH was updated but the existing PowerShell window doesn't know about it.
**Close and reopen** PowerShell.

**Port 7700 / 8000 / 5173 already in use**
Find and stop the process:
```powershell
Get-NetTCPConnection -LocalPort 7700 | Select-Object OwningProcess
Stop-Process -Id <PID>
```

**Backend cannot find documents**
Check that `DATA_FOLDER` in `backend\.env` points to a folder that exists,
and that paths use `\` (not `/`).

**Antivirus blocks `meilisearch.exe`**
Right-click the file → *Properties* → check **"Unblock"**, or whitelist
`C:\meilisearch\` in Windows Security.

---

## 13. Features

- **Filename search** with typo tolerance (Meilisearch).
- **Role-based access:** Admin sees everything, HR sees HR + Driftsmøter,
  Project Manager sees Prosjekt + Driftsmøter.
- **Filters:** department, file type, date range.
- **File preview** in browser (PDF, images, video) and download.
- **Admin dashboard:** user management, stats, configuration, re-index.
- **File watcher:** auto-indexes new / modified / deleted files in real time.

---

## 14. Project structure

```
bsi_project/
├── backend/              # FastAPI backend
│   ├── main.py           # App entry point
│   ├── setup.py          # First-time DB setup
│   ├── config.py         # Configuration
│   ├── database.py       # DB connection
│   ├── routers/          # API routes (auth, search, docs, admin)
│   ├── services/         # meili_service, ingestion, watcher
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── tests/            # pytest tests
│   ├── .env              # Environment config
│   └── requirements.txt
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── pages/        # Login, Search, Admin Dashboard
│   │   ├── components/   # Header, SearchBar, FilterPanel, ResultsList, ResultCard
│   │   ├── services/     # Axios API layer
│   │   ├── context/      # AuthContext
│   │   └── hooks/        # useAuth, useSearch
│   ├── package.json
│   └── vite.config.js
├── tilgang/              # BSI document folders (Prosjekt, HR, Driftsmøter)
└── venv/                 # Python virtual environment (created locally)
```

---

## License

Internal project for BSI. Not for public redistribution.
