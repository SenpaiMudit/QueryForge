<div align="center">

# ⚡ QueryForge

### _The AI-Powered DBMS Workspace for SQL Students_

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Svelte](https://img.shields.io/badge/Svelte-5.x-FF3E00?style=for-the-badge&logo=svelte&logoColor=white)](https://svelte.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-Free_API-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**QueryForge** is a full-stack, AI-powered DBMS workspace that helps students understand SQL through live query execution, automatic data visualizations, and a built-in AI tutor — all in one browser-based application.

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Development Roadmap](#-development-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

Traditional SQL tools respond to mistakes with cryptic error messages. **QueryForge** changes this — it acts as an **interactive DBMS tutor** that:

- **Executes** real SQLite queries against your own uploaded databases
- **Explains** what each clause does in plain English
- **Fixes** broken queries with AI-generated corrections
- **Visualizes** query results as interactive charts automatically
- **Converts** natural language questions into valid SQL

---

## ✨ Features

### 🗄️ File Upload & Database Creation

| Supported Format | Behavior |
|---|---|
| `.csv` | Auto-converted into SQLite table with inferred schema |
| `.sql` | Executed as schema + seed data script |
| `.sqlite` / `.db` | Opened directly as working database |
| Blank Database | Create tables manually from scratch |

### 📝 Professional SQL Editor
- **CodeMirror 6** with full SQL syntax highlighting and autocomplete
- Multi-statement support
- Keyboard shortcuts: Run `Ctrl+Enter`, Format `Ctrl+Shift+F`

### ⚡ Live Query Feedback
- Auto-executes query after 800ms typing pause
- Detects incomplete queries and shows AI hints
- Shows row-count, execution time, success/failure banners
- Live schema refresh after DDL commands

### 🤖 AI SQL Tutor (Google Gemini - Free Tier)
- **English → SQL**: Describe what you want, get valid SQL
- **Error Explainer**: Understand *why* a query failed
- **Logic Explainer**: Plain-English breakdown of any SQL query
- **Optimizer**: Suggests indexes, query rewrites for performance

### 📊 Automatic Data Visualization

| Query Result Pattern | Chart Type |
|---|---|
| 1 category + 1 number column | Bar Chart |
| Date/time + number column | Line Chart |
| ≤ 7 categories summing to whole | Pie Chart |
| 2 numeric columns | Scatter Plot |
| Complex / text-heavy result | Table View |

### 🗂️ Database Schema Explorer
- Live tree view of tables, columns, types, and constraints
- Primary key / foreign key indicators
- Click table → auto-generate preview query

### 📜 Query History & Snapshots
- Stores last 100 queries with status and timestamp
- **Auto-snapshot** before every destructive query
- One-click restore to any previous snapshot

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.11+ | Core logic, file processing |
| **API Framework** | FastAPI | REST API + WebSocket |
| **Database Engine** | SQLite (built-in) | Query execution sandbox |
| **AI** | Google Gemini 1.5 Flash (free) | Tutor, NL→SQL |
| **Frontend** | Svelte 5 + Vite | Reactive UI |
| **SQL Editor** | CodeMirror 6 | Syntax highlighting |
| **Charts** | Plotly.js | Interactive visualizations |
| **Styling** | Vanilla CSS | Design system |
| **CSV Parsing** | Pandas | CSV → SQLite |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     BROWSER (Svelte)                    │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ SQL      │  │ Schema   │  │ AI Tutor │  │ Chart  │  │
│  │ Editor   │  │ Explorer │  │ Panel    │  │ View   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │
│       └─────────────┴──────────────┴────────────┘       │
│                          │ REST / WebSocket               │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  FastAPI Backend (Python)                │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────┐  │
│  │  /api/db   │  │  /api/ai   │  │  /api/history     │  │
│  │  execute   │  │  explain   │  │  /api/snapshot    │  │
│  │  schema    │  │  nl2sql    │  │  /api/upload      │  │
│  └─────┬──────┘  └─────┬──────┘  └─────────┬─────────┘  │
│        │               │                   │             │
│  ┌─────▼──────┐  ┌─────▼──────┐  ┌─────────▼─────────┐  │
│  │  SQLite    │  │  Gemini    │  │  Query History     │  │
│  │  Engine    │  │  API       │  │  Snapshot Manager  │  │
│  └────────────┘  └────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User types query
      ↓
800ms debounce (typing pause)
      ↓
Frontend sends query to /api/db/validate
      ↓
Backend checks completeness
      ├── Incomplete → AI tutor explains missing part
      └── Valid      → Execute against SQLite
                           ↓
                     Return rows + columns + exec time
                           ↓
                     Detect chart type automatically
                           ↓
                     Update: Table | Chart | Schema | History
```

---

## 📁 Project Structure

```
QueryForge/
├── 📄 README.md
├── 📄 LICENSE
├── 📄 .gitignore
├── 📄 docker-compose.yml
│
├── 🐍 backend/
│   ├── 📄 main.py                    # FastAPI app entry point
│   ├── 📄 requirements.txt
│   ├── 📄 .env.example
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── database.py           # DB execute, upload, schema routes
│   │   │   ├── ai_tutor.py           # Gemini AI routes
│   │   │   ├── history.py            # Query history routes
│   │   │   └── snapshot.py           # DB snapshot routes
│   │   │
│   │   ├── core/
│   │   │   └── config.py             # App settings (pydantic-settings)
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic request/response models
│   │   │
│   │   ├── services/
│   │   │   ├── db_manager.py         # SQLite session manager
│   │   │   ├── query_executor.py     # Query runner + result formatter
│   │   │   ├── csv_importer.py       # CSV → SQLite conversion
│   │   │   ├── sql_importer.py       # .sql file runner
│   │   │   ├── schema_reader.py      # Schema introspection
│   │   │   ├── ai_service.py         # Gemini API wrapper
│   │   │   ├── query_validator.py    # Completeness checker
│   │   │   ├── chart_advisor.py      # Auto chart-type selection
│   │   │   ├── history_manager.py    # Query history CRUD
│   │   │   └── snapshot_manager.py   # DB snapshot/restore
│   │   │
│   │   └── utils/
│   │       ├── file_helpers.py       # File type detection
│   │       └── sql_parser.py         # SQL statement type detection
│   │
│   ├── databases/                    # User DB files (gitignored)
│   ├── snapshots/                    # Auto-snapshots (gitignored)
│   ├── uploads/                      # Temp upload staging (gitignored)
│   └── tests/
│       ├── test_executor.py
│       ├── test_csv_import.py
│       ├── test_ai_service.py
│       └── test_validator.py
│
├── ⚡ frontend/
│   ├── 📄 package.json
│   ├── 📄 vite.config.js
│   ├── 📄 svelte.config.js
│   │
│   └── src/
│       ├── App.svelte                # Root component + router
│       ├── main.js
│       ├── app.css                   # Global design system
│       │
│       ├── pages/
│       │   ├── Home.svelte           # Landing + DB creation
│       │   ├── Workspace.svelte      # Main DBMS workspace
│       │   ├── History.svelte        # Query history page
│       │   └── DBManager.svelte      # Database manager
│       │
│       ├── components/
│       │   ├── Navbar.svelte
│       │   ├── SQLEditor.svelte      # CodeMirror wrapper
│       │   ├── ResultTable.svelte    # Query result table
│       │   ├── ChartView.svelte      # Plotly chart renderer
│       │   ├── SchemaExplorer.svelte # DB schema tree
│       │   ├── AITutorPanel.svelte   # AI tutor panel
│       │   ├── FileUploader.svelte   # Drag-and-drop upload
│       │   ├── QueryHistoryList.svelte
│       │   ├── SnapshotManager.svelte
│       │   └── StatusBanner.svelte
│       │
│       ├── stores/
│       │   ├── database.js           # Active DB state
│       │   ├── query.js              # Query + results state
│       │   ├── ui.js                 # UI state
│       │   └── history.js            # History state
│       │
│       └── lib/
│           ├── api.js                # API client
│           ├── chartDetector.js      # Chart type logic
│           └── sqlHelpers.js         # SQL constants
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── API_REFERENCE.md
│   └── CONTRIBUTING.md
│
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 🚀 Getting Started

### ⚡ Quick Start: Pure Python Streamlit App (Recommended — Zero JS!)

Run the complete QueryForge interactive workspace in a single command with 100% Python:

```bash
# 1. Clone the repository
git clone https://github.com/SenpaiMudit/QueryForge.git
cd QueryForge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch QueryForge Studio
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser. Pre-loaded sample databases (University and E-Commerce) are included out-of-the-box!

---

### Alternative: FastAPI Backend

If running the headless REST API service:

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
# Edit .env and add your GEMINI_API_KEY

# Start the backend
uvicorn main:app --reload --port 8000
```

Backend API: `http://localhost:8000`  
API Docs (Swagger): `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### 4. Docker (Optional)

```bash
docker-compose up --build
```

---

## 🔑 Environment Variables

Create `backend/.env` from `backend/.env.example`:

```env
# Required
GEMINI_API_KEY=your_google_gemini_api_key_here

# Optional (defaults shown)
APP_NAME=QueryForge
DEBUG=True
ALLOWED_ORIGINS=http://localhost:5173
MAX_UPLOAD_SIZE_MB=50
MAX_QUERY_ROWS=5000
SNAPSHOT_LIMIT=20
HISTORY_LIMIT=100
DATABASE_DIR=./databases
SNAPSHOT_DIR=./snapshots
UPLOAD_DIR=./uploads
```

### Getting a Free Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key into your `.env` file

> ✅ Gemini 1.5 Flash has a **free tier**: 15 req/min, 1,500 req/day — perfect for student usage.

---

## 📡 API Reference

### Database Routes `/api/db`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/db/create` | Create a new blank database |
| `POST` | `/api/db/upload` | Upload .csv/.sql/.sqlite/.db file |
| `POST` | `/api/db/execute` | Execute a SQL query |
| `GET` | `/api/db/schema/{db_id}` | Get full database schema |
| `GET` | `/api/db/list` | List all user databases |
| `DELETE` | `/api/db/{db_id}` | Delete a database |

### AI Tutor Routes `/api/ai`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ai/nl2sql` | Convert English → SQL |
| `POST` | `/api/ai/explain` | Explain a SQL query |
| `POST` | `/api/ai/fix` | Fix a broken SQL query |
| `POST` | `/api/ai/optimize` | Suggest query optimizations |
| `POST` | `/api/ai/validate` | Check query completeness |

### History Routes `/api/history`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/history/{db_id}` | Get query history for a DB |
| `DELETE` | `/api/history/{db_id}` | Clear query history |

### Snapshot Routes `/api/snapshot`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/snapshot/{db_id}` | List snapshots for a DB |
| `POST` | `/api/snapshot/{db_id}/restore/{snap_id}` | Restore a snapshot |
| `DELETE` | `/api/snapshot/{snap_id}` | Delete a snapshot |

---

## 🗺️ Development Roadmap

```
Phase 1 — Core DBMS Workspace             [🚧 In Progress]
  ✅ Project setup and folder structure
  ✅ README and documentation
  🔲 FastAPI backend skeleton
  🔲 Svelte frontend scaffold
  🔲 CodeMirror SQL editor integration
  🔲 SQLite query execution engine
  🔲 CSV / SQL / SQLite file upload
  🔲 Schema explorer

Phase 2 — Live Feedback & Visualizations  [📋 Planned]
  🔲 Debounced live query execution
  🔲 Incomplete query detection
  🔲 Plotly chart auto-generation
  🔲 Schema auto-refresh after DDL
  🔲 Result table with sorting/filtering

Phase 3 — AI Tutor                        [📋 Planned]
  🔲 Gemini API integration
  🔲 English-to-SQL conversion
  🔲 SQL error explanation
  🔲 Query logic breakdown
  🔲 Optimization suggestions

Phase 4 — Reliability & Polish            [📋 Planned]
  🔲 Query history persistence
  🔲 Database snapshots and restore
  🔲 Improved error messages
  🔲 Large file handling
  🔲 Export results as CSV/JSON

Future Ideas                              [💡 Backlog]
  🔲 User accounts and saved workspaces
  🔲 ER diagram generation
  🔲 Shareable workspace links
  🔲 PostgreSQL / MySQL adapter
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit using conventional commits: `git commit -m 'feat: add amazing feature'`
4. Push the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">

Made with ❤️ for SQL students everywhere

**⭐ Star this repo if QueryForge helped you learn SQL!**

</div>
