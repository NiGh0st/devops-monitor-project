"""Streamlit dashboard — DevOps Monitoring Dashboard."""

import os
import time
from collections import deque

import httpx
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}
HISTORY_SIZE = 60  # seconds of live history kept in memory

st.set_page_config(
    page_title="DevOps Monitor",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for a dark premium look
st.markdown(
    """
    <style>
    /* Dark background */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    /* Cards */
    div[data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
    }
    /* Tab styling */
    .stTabs [role="tab"] { font-size: 16px; font-weight: 600; }
    /* Dataframe */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #238636, #1a7f37);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    h1 { color: #58a6ff; font-size: 2rem; }
    h2 { color: #79c0ff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────────────────────────────────────
if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = deque(maxlen=HISTORY_SIZE)
if "mem_history" not in st.session_state:
    st.session_state.mem_history = deque(maxlen=HISTORY_SIZE)
if "disk_history" not in st.session_state:
    st.session_state.disk_history = deque(maxlen=HISTORY_SIZE)
if "timestamps" not in st.session_state:
    st.session_state.timestamps = deque(maxlen=HISTORY_SIZE)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=2)
def fetch_metrics() -> dict:
    """Fetch current metrics from the API (cached 2 s)."""
    try:
        r = httpx.get(f"{API_BASE_URL}/metrics", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # noqa: BLE001
        st.error(f"❌ Cannot reach API: {exc}")
        return {}


@st.cache_data(ttl=5)
def fetch_servers() -> list[dict]:
    """Fetch registered servers from the API (cached 5 s)."""
    try:
        r = httpx.get(f"{API_BASE_URL}/servers", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # noqa: BLE001
        st.error(f"❌ Cannot reach API: {exc}")
        return []


def status_color(status: str) -> str:
    """Return a coloured HTML badge for a server status."""
    colors = {"UP": "#2ea043", "DEGRADED": "#d29922", "DOWN": "#da3633", "UNKNOWN": "#6e7681"}
    bg = colors.get(status, "#6e7681")
    style = f"background:{bg};color:white;padding:2px 10px;border-radius:12px;font-weight:600;"
    return f'<span style="{style}">{status}</span>'


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.title("📡 DevOps Monitoring Dashboard")
st.caption(f"API : `{API_BASE_URL}`  •  Auto-refresh every 2 s")

tab_metrics, tab_servers = st.tabs(["📊 Métriques", "🖥️ Serveurs"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — METRICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_metrics:
    data = fetch_metrics()

    if data:
        cpu = data.get("cpu_percent", 0)
        mem = data.get("memory_percent", 0)
        disk = data.get("disk_percent", 0)

        # Append to history
        now = time.strftime("%H:%M:%S")
        st.session_state.cpu_history.append(cpu)
        st.session_state.mem_history.append(mem)
        st.session_state.disk_history.append(disk)
        st.session_state.timestamps.append(now)

        # ── KPI cards ────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        with col1:
            history = list(st.session_state.cpu_history)
            prev_cpu = history[-2] if len(history) > 1 else cpu
            st.metric(
                label="🖥️ CPU",
                value=f"{cpu:.1f} %",
                delta=f"{cpu - prev_cpu:.1f} pp",
            )
        with col2:
            st.metric(
                label="🧠 Mémoire",
                value=f"{mem:.1f} %",
                help=f"{data.get('memory_used_gb', 0):.1f} GB / {data.get('memory_total_gb', 0):.1f} GB",
            )
        with col3:
            st.metric(
                label="💾 Disque",
                value=f"{disk:.1f} %",
                help=f"{data.get('disk_used_gb', 0):.1f} GB / {data.get('disk_total_gb', 0):.1f} GB",
            )

        st.divider()

        # ── Live chart ───────────────────────────────────────────────────────
        st.subheader("📈 Historique (60 dernières secondes)")
        if st.session_state.timestamps:
            chart_df = pd.DataFrame(
                {
                    "CPU (%)": list(st.session_state.cpu_history),
                    "Mémoire (%)": list(st.session_state.mem_history),
                    "Disque (%)": list(st.session_state.disk_history),
                },
                index=list(st.session_state.timestamps),
            )
            st.line_chart(chart_df, use_container_width=True, height=300)
    else:
        st.warning("En attente de données de l'API…")

    # Auto-refresh
    time.sleep(2)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SERVERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_servers:
    st.subheader("🖥️ Serveurs enregistrés")

    servers = fetch_servers()

    if servers:
        # Build HTML table with coloured status badges
        rows_html = ""
        for s in servers:
            badge = status_color(s.get("status", "UNKNOWN"))
            rows_html += (
                f"<tr>"
                f"<td style='padding:8px 12px;'>{s['name']}</td>"
                f"<td style='padding:8px 12px;'>{s['host']}</td>"
                f"<td style='padding:8px 12px;'>{s['port']}</td>"
                f"<td style='padding:8px 12px;'>{badge}</td>"
                f"<td style='padding:8px 12px;font-family:monospace;"
                f"font-size:0.75rem;color:#8b949e;'>{s['id'][:8]}…</td>"
                f"</tr>"
            )
        table_html = f"""
        <table style="width:100%;border-collapse:collapse;background:#161b22;border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:#21262d;color:#8b949e;font-size:0.85rem;text-transform:uppercase;">
              <th style="padding:10px 12px;text-align:left;">Nom</th>
              <th style="padding:10px 12px;text-align:left;">Hôte</th>
              <th style="padding:10px 12px;text-align:left;">Port</th>
              <th style="padding:10px 12px;text-align:left;">Statut</th>
              <th style="padding:10px 12px;text-align:left;">ID</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Aucun serveur enregistré. Ajoutez-en un ci-dessous.")

    st.divider()

    # ── Registration form ────────────────────────────────────────────────────
    st.subheader("➕ Enregistrer un serveur")
    with st.form("register_server", clear_on_submit=True):
        col_a, col_b, col_c = st.columns([3, 3, 1])
        with col_a:
            srv_name = st.text_input("Nom du serveur", placeholder="prod-web-01")
        with col_b:
            srv_host = st.text_input("Hôte / IP", placeholder="192.168.1.10")
        with col_c:
            srv_port = st.number_input("Port", min_value=1, max_value=65535, value=8080)

        submitted = st.form_submit_button("🚀 Enregistrer", use_container_width=True)
        if submitted:
            if not srv_name or not srv_host:
                st.error("Nom et hôte sont obligatoires.")
            else:
                try:
                    resp = httpx.post(
                        f"{API_BASE_URL}/servers",
                        json={"name": srv_name, "host": srv_host, "port": int(srv_port)},
                        headers=HEADERS,
                        timeout=5,
                    )
                    if resp.status_code == 201:
                        st.success(f"✅ Serveur **{srv_name}** enregistré !")
                        fetch_servers.clear()
                    else:
                        st.error(f"Erreur {resp.status_code}: {resp.text}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"❌ Erreur: {exc}")
