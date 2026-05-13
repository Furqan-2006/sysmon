# ⚡ SysMon API

> A high-performance system monitoring REST API built with **Flask** and a custom **C extension**.  
> Real-time CPU, memory, disk, and process metrics — powered by a C backend reading the Linux `/proc` filesystem, exposed through a secure JWT-authenticated REST API with SQLite history storage.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│               Flask REST API                │
│  Auth │ Metrics │ Upload │ History          │
└──────────────────┬──────────────────────────┘
                   │  ctypes
┌──────────────────▼──────────────────────────┐
│           C Extension (sysmon.so)           │
│   /proc/stat  │ /proc/meminfo │  statvfs    │
└─────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           SQLite (via SQLAlchemy)           │
│   Users │ MetricSnapshots │ UploadedConfigs │
└─────────────────────────────────────────────┘
```

**Why C + Python?**  
The metrics engine is written in C for zero-overhead access to kernel interfaces. Python calls it at runtime via `ctypes` — no subprocess, no FFI overhead, no parsing shell output. This is how production monitoring tools actually work.

---

## 🚀 Quick Start

### 1. Build the C extension
```bash
cd c_extension
make
cd ..
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY and JWT_SECRET_KEY
```

### 4. Run the server
```bash
python run.py
```

Server starts at `http://127.0.0.1:5000`

---

## 📡 API Reference

### Auth Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register` | Register a new user | ❌ |
| `POST` | `/api/auth/login` | Login → get JWT token | ❌ |
| `DELETE` | `/api/auth/logout` | Invalidate token | ✅ |
| `GET` | `/api/auth/me` | Current user profile | ✅ |

### Metrics Endpoints (all require JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/metrics/cpu` | Live CPU usage (100ms C sample) |
| `GET` | `/api/metrics/memory` | Live memory stats |
| `GET` | `/api/metrics/disk` | Root filesystem disk usage |
| `GET` | `/api/metrics/processes` | Process count by state |
| `GET` | `/api/metrics/uptime` | System uptime |
| `GET` | `/api/metrics/snapshot` | All metrics + save to DB |
| `GET` | `/api/metrics/history` | Historical snapshots from SQLite |
| `DELETE` | `/api/metrics/history` | Clear all snapshots |

**History query params:**
```
GET /api/metrics/history?limit=50&since=2024-01-01T00:00:00
```

### Upload Endpoints (all require JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/config` | Upload a config file (.json/.yaml/.ini/.toml) |
| `GET` | `/api/upload/configs` | List your uploaded configs |
| `GET` | `/api/upload/configs/<id>` | Download a config file |
| `DELETE` | `/api/upload/configs/<id>` | Delete a config file |

---

## 🔐 Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "email": "ali@example.com", "password": "secret123"}'

# 2. Login → copy the token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "password": "secret123"}'

# 3. Use token in requests
curl http://localhost:5000/api/metrics/snapshot \
  -H "Authorization: Bearer <your_token>"
```

---

## 🔬 C Extension Details

The C engine (`c_extension/sysmon.c`) reads metrics directly from the Linux kernel:

| Metric | Source |
|--------|--------|
| CPU usage | `/proc/stat` — two samples 100ms apart |
| Memory | `/proc/meminfo` — MemTotal, MemAvailable |
| Disk | `statvfs("/")` syscall |
| Processes | `/proc/[pid]/stat` — counts by state |
| Uptime | `/proc/uptime` |

Compiled as a shared library (`.so`) and loaded at runtime via Python's `ctypes`. Struct layouts in `sysmon.h` are mirrored exactly in `sysmon_bridge.py`.

```bash
# Rebuild after any changes
cd c_extension && make clean && make
```

---

## 📁 Project Structure

```
sysmon/
├── c_extension/
│   ├── sysmon.c          # C metrics engine
│   ├── sysmon.h          # Struct definitions
│   ├── sysmon.so         # Compiled shared library
│   └── Makefile
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── extensions.py     # SQLAlchemy, JWT, Bcrypt
│   ├── models.py         # User, MetricSnapshot, UploadedConfig
│   ├── auth.py           # Auth blueprint (register/login/logout)
│   ├── metrics.py        # Metrics blueprint (live + history)
│   ├── upload.py         # Upload blueprint
│   └── sysmon_bridge.py  # Python ↔ C ctypes bridge
├── uploads/              # Uploaded config files
├── instance/
│   └── sysmon.db         # SQLite database (auto-created)
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Flask 3.x |
| Database ORM | Flask-SQLAlchemy + SQLite |
| Authentication | Flask-JWT-Extended (JWT tokens) |
| Password Hashing | Flask-Bcrypt |
| Metrics Engine | Custom C (gcc, shared library) |
| C ↔ Python Bridge | `ctypes` |
| Config Upload | Flask file handling |

---

## 💡 CV Talking Points

- **"Wrote a C shared library that reads Linux kernel interfaces (`/proc`, `statvfs`) and integrated it with Flask at runtime using `ctypes` — no subprocess overhead."**
- **"Designed a JWT-authenticated REST API with token blocklisting and bcrypt password hashing."**
- **"Used SQLAlchemy to persist time-series metric snapshots to SQLite with filterable history queries."**
- **"Implemented secure file upload with UUID-based storage, MIME validation, and per-user access control."**
