"""
QueryForge — AI-Powered SQL & DBMS Studio
A pure Python, web-based DBMS workspace built with Streamlit.
"""
import sys
from pathlib import Path

# Ensure backend directory is in Python path for services
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import os
import time
import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# QueryForge Core Services
from app.services import (
    db_manager,
    query_executor,
    schema_reader,
    snapshot_manager,
    history_manager,
    csv_importer,
    sql_importer,
    ai_service,
)
from app.utils.sql_parser import check_completeness, detect_statement_type
from app.core.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration & Modern Design System (CSS)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QueryForge — AI SQL & DBMS Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Modern typography and dark theme accents */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}

code, pre, .stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Header Banner */
.qf-hero {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.qf-badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.qf-badge-primary {
    background: rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.4);
}

.qf-badge-success {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

.qf-badge-warning {
    background: rgba(245, 158, 11, 0.2);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

.qf-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.8rem;
}

.qf-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
}

.qf-stat-box {
    text-align: center;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

.qf-stat-num {
    font-size: 1.4rem;
    font-weight: 700;
    color: #6366f1;
    font-family: 'Outfit', sans-serif;
}

.qf-stat-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
}

/* Custom button tweaks */
div.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────────────────────────────────────
def init_state():
    if "active_db_id" not in st.session_state:
        # Pick first available or default
        dbs = db_manager.list_databases()
        if dbs:
            st.session_state.active_db_id = dbs[0]["db_id"]
            st.session_state.active_db_name = dbs[0]["db_name"]
        else:
            st.session_state.active_db_id = None
            st.session_state.active_db_name = None

    if "editor_sql" not in st.session_state:
        st.session_state.editor_sql = "SELECT * FROM students LIMIT 10;"
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_error" not in st.session_state:
        st.session_state.last_error = None
    if "ai_api_key" not in st.session_state:
        st.session_state.ai_api_key = os.getenv("GEMINI_API_KEY", "")
    if "ai_model" not in st.session_state:
        st.session_state.ai_model = "gemini-1.5-flash"
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0

init_state()


# Sync API key with backend settings
if st.session_state.ai_api_key:
    settings.GEMINI_API_KEY = st.session_state.ai_api_key
if st.session_state.ai_model:
    settings.GEMINI_MODEL = st.session_state.ai_model


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────
def get_current_schema():
    if not st.session_state.active_db_id:
        return None
    try:
        return schema_reader.get_schema(st.session_state.active_db_id)
    except Exception:
        return None


def execute_current_query(sql: str):
    if not st.session_state.active_db_id:
        st.error("Please select or create a database first.")
        return

    db_id = st.session_state.active_db_id
    result = query_executor.execute_query(db_id, sql)
    st.session_state.last_result = result

    # Log to history
    try:
        history_manager.add_history(
            db_id=db_id,
            query=sql,
            statement_type=result.statement_type.value,
            status=result.status.value,
            execution_time_ms=result.execution_time_ms,
            row_count=result.row_count,
            error=result.error,
        )
    except Exception:
        pass

    if result.status.value == "error":
        st.session_state.last_error = {
            "query": sql,
            "error": result.error or result.message,
        }
    else:
        st.session_state.last_error = None


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR: Database Management, File Uploads, Snapshots, Settings
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ **QueryForge**")
    st.caption("AI-Powered DBMS & SQL Studio")

    st.markdown("---")

    # 1. Database Selector
    dbs = db_manager.list_databases()
    db_options = {d["db_id"]: f"{d['db_name']} ({d['db_id']})" for d in dbs}

    if dbs:
        current_index = 0
        ids_list = list(db_options.keys())
        if st.session_state.active_db_id in ids_list:
            current_index = ids_list.index(st.session_state.active_db_id)

        selected_db_id = st.selectbox(
            "📁 Active Database",
            options=ids_list,
            index=current_index,
            format_func=lambda x: db_options.get(x, x),
            key="db_selector",
        )
        if selected_db_id != st.session_state.active_db_id:
            st.session_state.active_db_id = selected_db_id
            for d in dbs:
                if d["db_id"] == selected_db_id:
                    st.session_state.active_db_name = d["db_name"]
            st.rerun()
    else:
        st.warning("No databases found. Create one or load sample data below.")

    # 2. Database Quick Actions Expander
    with st.expander("➕ Create or Load Database", expanded=not bool(dbs)):
        tab_new, tab_sample, tab_upload = st.tabs(["New DB", "Sample Datasets", "Upload File"])

        with tab_new:
            new_db_name = st.text_input("Database Name", placeholder="e.g. library_db", key="new_db_input")
            if st.button("Create Blank DB", type="primary", use_container_width=True):
                if new_db_name.strip():
                    created = db_manager.create_database(new_db_name.strip())
                    st.session_state.active_db_id = created["db_id"]
                    st.session_state.active_db_name = created["db_name"]
                    st.success(f"Created database '{new_db_name}'!")
                    st.rerun()
                else:
                    st.error("Please enter a database name.")

        with tab_sample:
            st.markdown("<small>Pre-configured datasets with relational tables & sample rows:</small>", unsafe_allow_html=True)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("🎓 University DB", use_container_width=True):
                    db_id = "sample_university"
                    sql_path = Path("samples/university.sql")
                    if sql_path.exists():
                        conn = sqlite3.connect(f"databases/{db_id}.db")
                        with open(sql_path, "r", encoding="utf-8") as f:
                            conn.executescript(f.read())
                        conn.close()
                        st.session_state.active_db_id = db_id
                        st.session_state.active_db_name = "University DB"
                        st.session_state.editor_sql = "SELECT s.first_name, s.last_name, s.gpa, d.dept_name\nFROM students s\nJOIN departments d ON s.dept_id = d.dept_id\nORDER BY s.gpa DESC;"
                        st.success("Loaded University DB!")
                        st.rerun()
            with col_s2:
                if st.button("🛒 E-Commerce DB", use_container_width=True):
                    db_id = "sample_ecommerce"
                    sql_path = Path("samples/ecommerce.sql")
                    if sql_path.exists():
                        conn = sqlite3.connect(f"databases/{db_id}.db")
                        with open(sql_path, "r", encoding="utf-8") as f:
                            conn.executescript(f.read())
                        conn.close()
                        st.session_state.active_db_id = db_id
                        st.session_state.active_db_name = "E-Commerce DB"
                        st.session_state.editor_sql = "SELECT c.name, COUNT(o.order_id) as orders_count, SUM(o.total_amount) as total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nGROUP BY c.customer_id;"
                        st.success("Loaded E-Commerce DB!")
                        st.rerun()

        with tab_upload:
            uploaded_file = st.file_uploader("Upload CSV, SQL, or SQLite .db", type=["csv", "sql", "db"])
            if uploaded_file is not None:
                upload_name = uploaded_file.name
                ext = upload_name.split(".")[-1].lower()

                if ext == "csv":
                    table_name_input = st.text_input("Table Name for CSV", value=Path(upload_name).stem.lower())
                    if st.button("Import CSV into Active DB", use_container_width=True):
                        if not st.session_state.active_db_id:
                            st.error("Select an active database first!")
                        else:
                            temp_csv = Path(f"uploads/{upload_name}")
                            temp_csv.parent.mkdir(exist_ok=True)
                            with open(temp_csv, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            try:
                                imported = csv_importer.import_csv(st.session_state.active_db_id, str(temp_csv), table_name_input)
                                st.success(f"Imported {imported['rows_imported']} rows into '{table_name_input}'!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Import failed: {e}")

                elif ext == "sql":
                    if st.button("Execute SQL Script in Active DB", use_container_width=True):
                        if not st.session_state.active_db_id:
                            st.error("Select an active database first!")
                        else:
                            temp_sql = Path(f"uploads/{upload_name}")
                            temp_sql.parent.mkdir(exist_ok=True)
                            with open(temp_sql, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            try:
                                sql_importer.import_sql(st.session_state.active_db_id, str(temp_sql))
                                st.success("SQL Script executed successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"SQL execution failed: {e}")

                elif ext == "db":
                    if st.button("Load SQLite Database File", use_container_width=True):
                        new_id = Path(upload_name).stem
                        dest_db = Path(f"databases/{new_id}.db")
                        dest_db.parent.mkdir(exist_ok=True)
                        with open(dest_db, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.session_state.active_db_id = new_id
                        st.session_state.active_db_name = upload_name
                        st.success(f"Database '{upload_name}' loaded!")
                        st.rerun()

    # 3. Snapshots & Rollback
    if st.session_state.active_db_id:
        with st.expander("🔄 Snapshots & Rollback", expanded=False):
            if st.button("📸 Take Snapshot Now", use_container_width=True):
                try:
                    snapshot_manager.create_snapshot(st.session_state.active_db_id, trigger_query="Manual Snapshot")
                    st.success("Snapshot created successfully!")
                except Exception as e:
                    st.error(f"Snapshot failed: {e}")

            snaps = snapshot_manager.list_snapshots(st.session_state.active_db_id)
            if snaps:
                st.markdown(f"<small>Recent snapshots ({len(snaps)}):</small>", unsafe_allow_html=True)
                for s in snaps[:5]:
                    col_snap, col_btn = st.columns([3, 1])
                    with col_snap:
                        time_str = s['created_at'][:19].replace('T', ' ')
                        st.caption(f"🕒 {time_str}\n`{s.get('trigger_query', 'Manual')[:30]}`")
                    with col_btn:
                        if st.button("Restore", key=f"restore_{s['snapshot_id']}"):
                            try:
                                snapshot_manager.restore_snapshot(st.session_state.active_db_id, s['snapshot_id'])
                                st.success("Restored database from snapshot!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Restore failed: {e}")
            else:
                st.caption("No snapshots yet. QueryForge automatically takes snapshots before destructive queries (DROP, DELETE, UPDATE).")

    # 4. Settings: Gemini AI Key
    with st.expander("⚙️ AI Tutor Settings", expanded=not bool(st.session_state.ai_api_key)):
        st.markdown("<small>QueryForge uses Google Gemini for NL→SQL, query explanations, and error fixing.</small>", unsafe_allow_html=True)
        key_input = st.text_input("Gemini API Key", value=st.session_state.ai_api_key, type="password", placeholder="AIzaSy...")
        if key_input != st.session_state.ai_api_key:
            st.session_state.ai_api_key = key_input
            settings.GEMINI_API_KEY = key_input

        model_choice = st.selectbox(
            "Gemini Model",
            options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
            index=0,
        )
        if model_choice != st.session_state.ai_model:
            st.session_state.ai_model = model_choice
            settings.GEMINI_MODEL = model_choice

        st.markdown("[Get a free Gemini API Key](https://aistudio.google.com/app/apikey)", unsafe_allow_html=True)

    # 5. Active DB Deletion
    if st.session_state.active_db_id:
        st.markdown("---")
        if st.button("🗑️ Delete Active Database", type="secondary", use_container_width=True):
            db_manager.delete_database(st.session_state.active_db_id)
            st.session_state.active_db_id = None
            st.session_state.active_db_name = None
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN HEADER & STATS BAR
# ──────────────────────────────────────────────────────────────────────────────
schema = get_current_schema()
table_names = [t.name for t in schema.tables] if schema else []
total_tables = len(table_names)
total_rows = sum(t.row_count for t in schema.tables) if schema else 0

st.markdown(f"""
<div class="qf-hero">
    <div>
        <h2 style="margin: 0; font-size: 1.6rem; color: #f8fafc;">⚡ QueryForge Studio</h2>
        <div style="margin-top: 0.25rem;">
            <span class="qf-badge qf-badge-primary">Active DB: {st.session_state.active_db_name or 'None Selected'}</span>
            <span class="qf-badge qf-badge-success">{total_tables} Table(s)</span>
            <span class="qf-badge qf-badge-warning">{total_rows} Total Records</span>
        </div>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 0.85rem; color: #94a3b8;">AI Tutor: {'🟢 Ready' if st.session_state.ai_api_key else '🟡 Offline (No Key)'}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# WORKSPACE TABS
# ──────────────────────────────────────────────────────────────────────────────
main_tabs = st.tabs([
    "⚡ SQL Studio & Results",
    "🤖 AI Tutor & Assistant",
    "🗄️ Database & Schema Explorer",
    "📜 Query History & Snapshots",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: SQL STUDIO & LIVE RESULTS
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[0]:
    # Quick Table Pills / Schema Hints
    if table_names:
        cols_pills = st.columns([1] + [1] * min(len(table_names), 5) + [2])
        cols_pills[0].markdown("<small style='color:#94a3b8;'><b>Tables:</b></small>", unsafe_allow_html=True)
        for i, tbl in enumerate(table_names[:5]):
            if cols_pills[i+1].button(tbl, key=f"pill_{tbl}", use_container_width=True):
                st.session_state.editor_sql = f"SELECT * FROM {tbl} LIMIT 10;"
                st.rerun()

    # Query Snippet Shortcuts
    col_snip, col_fmt = st.columns([5, 1])
    with col_snip:
        snip_cols = st.columns(6)
        if snip_cols[0].button("SELECT *", use_container_width=True):
            target = table_names[0] if table_names else "my_table"
            st.session_state.editor_sql = f"SELECT * FROM {target} LIMIT 10;"
            st.rerun()
        if snip_cols[1].button("COUNT(*)", use_container_width=True):
            target = table_names[0] if table_names else "my_table"
            st.session_state.editor_sql = f"SELECT COUNT(*) as total_rows FROM {target};"
            st.rerun()
        if snip_cols[2].button("JOIN", use_container_width=True):
            if len(table_names) >= 2:
                st.session_state.editor_sql = f"SELECT *\nFROM {table_names[0]} a\nJOIN {table_names[1]} b ON a.id = b.id\nLIMIT 10;"
            else:
                st.session_state.editor_sql = "SELECT *\nFROM table_a a\nJOIN table_b b ON a.id = b.id\nLIMIT 10;"
            st.rerun()
        if snip_cols[3].button("GROUP BY", use_container_width=True):
            target = table_names[0] if table_names else "my_table"
            st.session_state.editor_sql = f"SELECT category, COUNT(*) as count, AVG(price) as avg_val\nFROM {target}\nGROUP BY category;"
            st.rerun()
        if snip_cols[4].button("WHERE", use_container_width=True):
            target = table_names[0] if table_names else "my_table"
            st.session_state.editor_sql = f"SELECT * FROM {target}\nWHERE condition = 'value'\nORDER BY 1 DESC;"
            st.rerun()
        if snip_cols[5].button("INSERT", use_container_width=True):
            target = table_names[0] if table_names else "my_table"
            st.session_state.editor_sql = f"INSERT INTO {target} (col1, col2) VALUES ('val1', 100);"
            st.rerun()

    with col_fmt:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.editor_sql = ""
            st.session_state.last_result = None
            st.rerun()

    # SQL Editor Text Area
    query_input = st.text_area(
        "SQL Query Editor",
        value=st.session_state.editor_sql,
        height=140,
        placeholder="Enter your SQL query here... e.g. SELECT * FROM students WHERE gpa > 3.5;",
        key="sql_editor_box",
    )
    st.session_state.editor_sql = query_input

    # Real-time Syntax / Completeness Checker
    if query_input.strip():
        completeness = check_completeness(query_input)
        if not completeness["is_complete"]:
            st.info(f"💡 **Incomplete Query Hint:** Missing {completeness['missing']}. {completeness['hint']}\n\n*Example:* `{completeness['example']}`")

    # Execution Buttons
    col_run, col_exp, col_opt = st.columns([2, 1, 1])
    with col_run:
        run_clicked = st.button("▶ Run Query", type="primary", use_container_width=True)
    with col_exp:
        explain_clicked = st.button("✨ Explain Query", use_container_width=True)
    with col_opt:
        optimize_clicked = st.button("⚡ Optimize Query", use_container_width=True)

    if run_clicked and query_input.strip():
        execute_current_query(query_input.strip())
        st.rerun()

    if explain_clicked and query_input.strip():
        st.session_state.explain_target_query = query_input.strip()
        st.info("Switched to AI Tutor tab for detailed explanation!")

    if optimize_clicked and query_input.strip():
        st.session_state.optimize_target_query = query_input.strip()
        st.info("Switched to AI Tutor tab for optimization insights!")

    # ── Query Results Display ─────────────────────────────────────────────────
    result = st.session_state.last_result
    if result:
        st.markdown("---")
        status_color = "#10b981" if result.status.value == "success" else "#ef4444"

        # Results Metric Bar
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Status", result.status.value.upper())
        with col_m2:
            st.metric("Execution Time", f"{result.execution_time_ms} ms")
        with col_m3:
            if result.statement_type.value == "select":
                st.metric("Rows Returned", result.row_count)
            else:
                st.metric("Rows Affected", result.rows_affected)
        with col_m4:
            st.metric("Statement Type", result.statement_type.value.upper())

        # Error State
        if result.status.value == "error":
            st.error(f"❌ **Database Error:** {result.error or result.message}")
            col_err_fix, _ = st.columns([2, 3])
            with col_err_fix:
                if st.button("🤖 Fix this Error with AI Tutor", type="primary", use_container_width=True):
                    st.session_state.fix_target_query = query_input
                    st.session_state.fix_target_error = result.error or result.message
                    st.info("Ready! Switch to 'AI Tutor & Assistant' tab to see the diagnosis & fix.")

        # Success State - SELECT Query
        elif result.statement_type.value == "select" and result.columns:
            col_names = [c.name for c in result.columns]
            df = pd.DataFrame(result.rows, columns=col_names)

            tab_data, tab_charts, tab_export = st.tabs(["📊 Results Table", "📈 Visualizations", "📥 Export"])

            with tab_data:
                st.dataframe(df, use_container_width=True, hide_index=True)

            with tab_charts:
                # 1. Automatic Chart Advisor Recommendation
                if result.chart and df.shape[0] > 0:
                    st.markdown(f"##### 🎯 Auto Recommended Chart: `{result.chart.type.value.upper()}`")
                    c_type = result.chart.type.value
                    x_col = result.chart.x_column
                    y_col = result.chart.y_column

                    try:
                        if c_type == "bar" and x_col and y_col:
                            fig = px.bar(df, x=x_col, y=y_col, title=result.chart.title, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                        elif c_type == "line" and x_col and y_col:
                            fig = px.line(df, x=x_col, y=y_col, title=result.chart.title, markers=True, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                        elif c_type == "pie" and x_col and y_col:
                            fig = px.pie(df, names=x_col, values=y_col, title=result.chart.title, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                        elif c_type == "scatter" and x_col and y_col:
                            fig = px.scatter(df, x=x_col, y=y_col, title=result.chart.title, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.caption(f"Could not render auto-chart: {e}")

                # 2. Interactive Custom Chart Builder
                st.markdown("##### 🛠️ Interactive Chart Builder")
                c_builder_1, c_builder_2, c_builder_3 = st.columns(3)
                with c_builder_1:
                    chart_kind = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie", "Area"], key="custom_chart_kind")
                with c_builder_2:
                    x_axis = st.selectbox("X-Axis (Category / Dimension)", options=col_names, key="custom_chart_x")
                with c_builder_3:
                    num_cols = [c.name for c in result.columns if c.type == "number"] or col_names
                    y_axis = st.selectbox("Y-Axis (Numeric Measure)", options=num_cols, key="custom_chart_y")

                if st.button("Generate Custom Chart", use_container_width=True):
                    try:
                        if chart_kind == "Bar":
                            fig = px.bar(df, x=x_axis, y=y_axis, template="plotly_dark")
                        elif chart_kind == "Line":
                            fig = px.line(df, x=x_axis, y=y_axis, markers=True, template="plotly_dark")
                        elif chart_kind == "Scatter":
                            fig = px.scatter(df, x=x_axis, y=y_axis, template="plotly_dark")
                        elif chart_kind == "Pie":
                            fig = px.pie(df, names=x_axis, values=y_axis, template="plotly_dark")
                        elif chart_kind == "Area":
                            fig = px.area(df, x=x_axis, y=y_axis, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Failed to generate chart: {e}")

            with tab_export:
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                json_bytes = df.to_json(orient="records", indent=2).encode('utf-8')
                c_dl1, c_dl2 = st.columns(2)
                with c_dl1:
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv_bytes,
                        file_name=f"query_result_{int(time.time())}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with c_dl2:
                    st.download_button(
                        label="📥 Download Results as JSON",
                        data=json_bytes,
                        file_name=f"query_result_{int(time.time())}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

        # Success State - DML / DDL
        else:
            st.success(f"✅ {result.message}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: AI TUTOR & ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[1]:
    st.markdown("### 🤖 QueryForge AI SQL Tutor")
    st.caption("Convert natural language to SQL, understand complex queries, fix syntax errors, and learn database best practices.")

    if not st.session_state.ai_api_key:
        st.warning("⚠️ **Gemini API Key Required for AI Features:** Please enter your free Gemini API key in the sidebar under 'AI Tutor Settings'.")

    ai_subtabs = st.tabs([
        "💬 Natural Language → SQL",
        "🔍 Explain Query",
        "🛠️ Error Debugger & Fixer",
        "⚡ Query Optimizer",
    ])

    # 1. Natural Language to SQL
    with ai_subtabs[0]:
        st.markdown("##### 💬 Convert English into SQL Query")
        nl_input = st.text_area(
            "What would you like to query?",
            placeholder="e.g. Find students enrolled in Computer Science with a GPA above 3.5, ordered by highest GPA",
            height=80,
            key="nl_sql_prompt",
        )
        if st.button("Generate SQL Query", type="primary", key="btn_nl_sql"):
            if not st.session_state.ai_api_key:
                st.error("Please configure your Gemini API Key in the sidebar.")
            elif not nl_input.strip():
                st.error("Please enter a question or query description.")
            else:
                with st.spinner("AI Tutor is analyzing database schema and generating SQL..."):
                    try:
                        res = ai_service.nl_to_sql(nl_input.strip(), schema)
                        st.session_state.generated_sql = res["sql"]
                        st.session_state.generated_explanation = res["explanation"]
                    except Exception as e:
                        st.error(f"AI Generation Error: {e}")

        if "generated_sql" in st.session_state:
            st.markdown("##### 📝 Generated SQL:")
            st.code(st.session_state.generated_sql, language="sql")
            st.markdown(f"**Explanation:** {st.session_state.get('generated_explanation', '')}")

            col_copy, col_exec = st.columns(2)
            with col_copy:
                if st.button("📋 Load into SQL Studio Editor", use_container_width=True):
                    st.session_state.editor_sql = st.session_state.generated_sql
                    st.success("Loaded into editor! Go to 'SQL Studio' tab to view.")
            with col_exec:
                if st.button("▶ Run Immediately", type="primary", use_container_width=True):
                    st.session_state.editor_sql = st.session_state.generated_sql
                    execute_current_query(st.session_state.generated_sql)
                    st.success("Executed! Check 'SQL Studio' tab for live results.")

    # 2. Explain Query
    with ai_subtabs[1]:
        st.markdown("##### 🔍 Learn How a Query Works (Clause by Clause)")
        default_explain_sql = getattr(st.session_state, "explain_target_query", st.session_state.editor_sql)
        explain_sql_input = st.text_area(
            "SQL Query to Explain",
            value=default_explain_sql,
            height=100,
            key="explain_sql_input",
        )
        if st.button("Explain Query Logic", type="primary", key="btn_explain_sql"):
            if not st.session_state.ai_api_key:
                st.error("Please configure your Gemini API Key in the sidebar.")
            elif not explain_sql_input.strip():
                st.error("Please enter a SQL query to explain.")
            else:
                with st.spinner("AI Tutor is analyzing query structure..."):
                    try:
                        res = ai_service.explain_query(explain_sql_input.strip(), schema)
                        st.session_state.explain_result = res
                    except Exception as e:
                        st.error(f"Explanation Error: {e}")

        if "explain_result" in st.session_state:
            exp = st.session_state.explain_result
            st.markdown("#### 📖 Plain English Summary")
            st.info(exp.get("explanation", ""))

            clauses = exp.get("clause_breakdown", {})
            if clauses:
                st.markdown("#### 🧱 Clause-by-Clause Breakdown")
                for clause, details in clauses.items():
                    st.markdown(f"- **`{clause}`**: {details}")

            tips = exp.get("suggestions", [])
            if tips:
                st.markdown("#### 💡 Student Tips & Best Practices")
                for tip in tips:
                    st.markdown(f"- {tip}")

    # 3. Error Debugger & Fixer
    with ai_subtabs[2]:
        st.markdown("##### 🛠️ Fix Broken Queries and Understand Errors")
        broken_query = getattr(st.session_state, "fix_target_query", "")
        broken_error = getattr(st.session_state, "fix_target_error", "")

        err_q_input = st.text_area("Broken SQL Query", value=broken_query, height=80, key="broken_q_box")
        err_msg_input = st.text_input("Error Message", value=broken_error, placeholder="e.g. no such column: gpa_avg", key="broken_err_box")

        if st.button("Debug & Fix Query", type="primary", key="btn_fix_sql"):
            if not st.session_state.ai_api_key:
                st.error("Please configure your Gemini API Key in the sidebar.")
            elif not err_q_input.strip():
                st.error("Please provide the broken query.")
            else:
                with st.spinner("AI Tutor is diagnosing the issue..."):
                    try:
                        res = ai_service.fix_query(err_q_input.strip(), err_msg_input.strip(), schema)
                        st.session_state.fixed_result = res
                    except Exception as e:
                        st.error(f"Debugger Error: {e}")

        if "fixed_result" in st.session_state:
            fres = st.session_state.fixed_result
            st.markdown("#### ✅ Corrected Query:")
            st.code(fres.get("fixed_query", ""), language="sql")
            st.markdown(f"**Explanation:** {fres.get('explanation', '')}")

            changes = fres.get("changes_made", [])
            if changes:
                st.markdown("**Changes Made:**")
                for ch in changes:
                    st.markdown(f"- {ch}")

            if st.button("Load Corrected Query into Editor", key="btn_load_fixed"):
                st.session_state.editor_sql = fres.get("fixed_query", "")
                st.success("Loaded corrected query into SQL Studio!")

    # 4. Query Optimizer
    with ai_subtabs[3]:
        st.markdown("##### ⚡ Optimize Query Performance & Indexing")
        default_opt_sql = getattr(st.session_state, "optimize_target_query", st.session_state.editor_sql)
        opt_sql_input = st.text_area(
            "Query to Analyze",
            value=default_opt_sql,
            height=100,
            key="opt_sql_box",
        )
        if st.button("Analyze & Optimize", type="primary", key="btn_opt_sql"):
            if not st.session_state.ai_api_key:
                st.error("Please configure your Gemini API Key in the sidebar.")
            elif not opt_sql_input.strip():
                st.error("Please provide a SQL query to optimize.")
            else:
                with st.spinner("Analyzing execution strategy and indexes..."):
                    try:
                        res = ai_service.optimize_query(opt_sql_input.strip(), schema)
                        st.session_state.opt_result = res
                    except Exception as e:
                        st.error(f"Optimizer Error: {e}")

        if "opt_result" in st.session_state:
            ores = st.session_state.opt_result
            if ores.get("optimized_query"):
                st.markdown("#### 🚀 Optimized SQL:")
                st.code(ores["optimized_query"], language="sql")

            st.markdown(f"**Analysis:** {ores.get('explanation', '')}")
            suggs = ores.get("suggestions", [])
            if suggs:
                st.markdown("**Recommendations:**")
                for s in suggs:
                    st.markdown(f"- {s}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: DATABASE & SCHEMA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[2]:
    st.markdown("### 🗄️ Database & Schema Explorer")

    if not schema or not schema.tables:
        st.info("No tables in the active database. Create a table in SQL Studio or load sample data from the sidebar.")
    else:
        # Table Selector
        selected_tbl_name = st.selectbox(
            "Select Table to Inspect",
            options=table_names,
            key="schema_table_selector",
        )

        selected_table = next((t for t in schema.tables if t.name == selected_tbl_name), None)

        if selected_table:
            c_meta1, c_meta2, c_meta3 = st.columns(3)
            with c_meta1:
                st.metric("Total Records", selected_table.row_count)
            with c_meta2:
                st.metric("Total Columns", len(selected_table.columns))
            with c_meta3:
                pk_cols = [c.name for c in selected_table.columns if c.is_primary_key]
                st.metric("Primary Key", ", ".join(pk_cols) if pk_cols else "None")

            # Column Structure Table
            st.markdown("##### 📋 Columns & Constraints")
            cols_data = []
            for c in selected_table.columns:
                cols_data.append({
                    "Column Name": c.name,
                    "Data Type": c.type,
                    "Primary Key": "🔑 Yes" if c.is_primary_key else "No",
                    "Not Null": "Yes" if not c.nullable else "No",
                    "Default Value": str(c.default) if c.default is not None else "-",
                })
            st.dataframe(pd.DataFrame(cols_data), use_container_width=True, hide_index=True)

            # Foreign Keys
            if selected_table.foreign_keys:
                st.markdown("##### 🔗 Relationships (Foreign Keys)")
                fk_data = []
                for fk in selected_table.foreign_keys:
                    fk_data.append({
                        "From Column": fk.from_column,
                        "References Table": fk.to_table,
                        "To Column": fk.to_column,
                    })
                st.dataframe(pd.DataFrame(fk_data), use_container_width=True, hide_index=True)

            # Sample Data Preview
            st.markdown(f"##### 👁️ Live Data Preview (First 15 Rows of `{selected_tbl_name}`)")
            if st.session_state.active_db_id:
                try:
                    conn = db_manager.get_connection(st.session_state.active_db_id)
                    sample_df = pd.read_sql_query(f"SELECT * FROM {selected_tbl_name} LIMIT 15", conn)
                    conn.close()
                    st.dataframe(sample_df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Could not load preview: {e}")

            # DDL Viewer
            with st.expander("📜 View Table DDL (`CREATE TABLE` Definition)"):
                try:
                    conn = db_manager.get_connection(st.session_state.active_db_id)
                    cur = conn.cursor()
                    cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{selected_tbl_name}'")
                    ddl_row = cur.fetchone()
                    conn.close()
                    if ddl_row and ddl_row[0]:
                        st.code(ddl_row[0], language="sql")
                except Exception as e:
                    st.caption(f"Could not fetch DDL: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: QUERY HISTORY & SNAPSHOT TIMELINE
# ══════════════════════════════════════════════════════════════════════════════
with main_tabs[3]:
    st.markdown("### 📜 Query Execution History & Rollback Timeline")

    if st.session_state.active_db_id:
        h_tab, s_tab = st.tabs(["Query History", "Database Snapshots"])

        with h_tab:
            history = history_manager.get_history(st.session_state.active_db_id)
            if not history:
                st.info("No queries executed yet in this session.")
            else:
                col_h_clear, _ = st.columns([1, 5])
                with col_h_clear:
                    if st.button("Clear History", use_container_width=True):
                        history_manager.clear_history(st.session_state.active_db_id)
                        st.success("History cleared.")
                        st.rerun()

                for item in history[:20]:
                    status_badge = "🟢 SUCCESS" if item.get("status") == "success" else "🔴 ERROR"
                    with st.expander(f"{status_badge} | {item.get('statement_type', 'SQL').upper()} | {item.get('executed_at', '')[:19].replace('T', ' ')} ({item.get('execution_time_ms', 0)} ms)"):
                        st.code(item.get("query", ""), language="sql")
                        if item.get("error"):
                            st.error(f"Error: {item['error']}")
                        col_re, _ = st.columns([2, 4])
                        with col_re:
                            if st.button("Load this Query into Studio", key=f"hist_load_{item['history_id']}"):
                                st.session_state.editor_sql = item["query"]
                                st.success("Loaded! Go to SQL Studio tab to run.")

        with s_tab:
            snaps = snapshot_manager.list_snapshots(st.session_state.active_db_id)
            if not snaps:
                st.info("No snapshots recorded yet.")
            else:
                for s in snaps:
                    time_str = s['created_at'][:19].replace('T', ' ')
                    st.markdown(f"""
                    <div class="qf-card">
                        <b>Snapshot ID:</b> <code>{s['snapshot_id']}</code><br>
                        <b>Trigger:</b> <code>{s.get('trigger_query', 'Manual Snapshot')[:80]}</code><br>
                        <small style="color:#94a3b8;">Created: {time_str} | Size: {s.get('size_bytes', 0)} bytes</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Restore to this state ({s['snapshot_id'][:8]})", key=f"restore_tab_{s['snapshot_id']}"):
                        snapshot_manager.restore_snapshot(st.session_state.active_db_id, s['snapshot_id'])
                        st.success(f"Database restored to snapshot {s['snapshot_id'][:8]}!")
                        st.rerun()
