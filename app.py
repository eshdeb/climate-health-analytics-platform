
from __future__ import annotations

from pathlib import Path
from io import BytesIO
from uuid import uuid4
from datetime import datetime
import json
import textwrap
import zipfile
import os
import re

import folium
import shapefile
from folium.plugins import Draw
from branca.colormap import linear
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
try:
    from PIL import Image
except Exception:
    Image = None
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from streamlit_folium import st_folium

try:
    import requests
except Exception:
    requests = None

try:
    from scipy import stats as scipy_stats
except Exception:
    scipy_stats = None

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except Exception:
    sm = None
    smf = None

try:
    from sklearn.decomposition import PCA
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
except Exception:
    PCA = None
    RandomForestRegressor = RandomForestClassifier = None
    GradientBoostingRegressor = GradientBoostingClassifier = None

BASE_DIR = Path(__file__).resolve().parent
FACTSHEETS_DIR = BASE_DIR / "factsheets"
METADATA_DIR = BASE_DIR / "metadata"
SAMPLE_DIR = BASE_DIR / "sample_data"
STATE_DIR = BASE_DIR / ".platform_state"
EXPORTS_DIR = STATE_DIR / "exports"
JOBS_DIR = STATE_DIR / "jobs"
ADMIN_SETTINGS_PATH = STATE_DIR / ".admin_settings.json"
ADMIN_CREDENTIALS_PATH = STATE_DIR / ".admin_credentials.json"

for p in [STATE_DIR, EXPORTS_DIR, JOBS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Climate–Health and Health Systems Analytics Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

COUNTRIES = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina', 'Armenia',
    'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium',
    'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei', 'Bulgaria',
    'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon', 'Canada', 'Central African Republic', 'Chad',
    'Chile', 'China', 'Colombia', 'Comoros', 'Congo', 'Democratic Republic of the Congo', 'Costa Rica',
    'Côte d’Ivoire', 'Croatia', 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
    'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji',
    'Finland', 'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala',
    'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran',
    'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait',
    'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania',
    'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania',
    'Mauritius', 'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Morocco', 'Mozambique',
    'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria',
    'North Korea', 'North Macedonia', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Panama', 'Papua New Guinea',
    'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Qatar', 'Romania', 'Russia', 'Rwanda',
    'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Samoa', 'San Marino',
    'Sao Tome and Principe', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore',
    'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain',
    'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Syria', 'Tajikistan', 'Tanzania', 'Thailand',
    'Timor-Leste', 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
    'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan', 'Vanuatu',
    'Vatican City', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe', 'Custom / user-defined region'
]

st.markdown(
    """
<style>
:root {
  --text:#0f172a;
  --muted:#475569;
  --border:#d8e1f0;
  --panel:#ffffff;
  --bg-soft:#f8fbff;
}
html, body, [class*="css"]  {color: var(--text);}
.block-container {max-width: 1600px; padding-top: 0.8rem; padding-bottom: 2rem; padding-left: 1.15rem; padding-right: 1.15rem;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #f4f8ff 0%, #eef5ff 50%, #f7f3ff 100%);}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap: 0.25rem;}
.hero {position: relative; overflow: hidden; background: linear-gradient(120deg, #0b132b 0%, #1d4ed8 35%, #6d28d9 70%, #c026d3 100%); border-radius: 22px; padding: 1.35rem 1.25rem; color: white; box-shadow: 0 12px 28px rgba(15,23,42,0.18); margin-bottom: 0.95rem; animation: heroReveal 0.9s ease-out 1;}
.hero h1 {margin: 0 0 0.35rem 0; font-size: 2.15rem; line-height: 1.15;}
.hero-title-wrap {position: relative; width: 100%; overflow: hidden; min-height: 2.85rem;}
.hero-title-slide {position: relative; display:inline-block; white-space: nowrap; background: linear-gradient(90deg, #ffffff 0%, #dbeafe 30%, #ffffff 60%, #f5d0fe 100%); background-size: 240% auto; -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent; animation: titleShimmer 12s linear infinite, titleDriftLoop 16s linear infinite; will-change: transform, opacity;}
.hero p {margin: 0.2rem 0; color: rgba(255,255,255,0.96);}
.beta-badge {display:inline-block; margin-top:0.15rem; margin-bottom:0.25rem; padding:0.28rem 0.65rem; border-radius:999px; border:1px solid rgba(255,255,255,0.35); background:rgba(255,255,255,0.12); color:#fff; font-weight:700; font-size:0.78rem; letter-spacing:0.02em;}
.home-map-card {background: var(--panel); border: 1px solid #e2e8f0; border-radius: 20px; box-shadow: 0 8px 20px rgba(15,23,42,0.06); padding: 0.9rem;}
.legend-chip {display:inline-flex; align-items:center; gap:0.45rem; padding:0.34rem 0.75rem; border-radius:999px; background:#f8fafc; border:1px solid #e2e8f0; margin:0.18rem 0.28rem 0.18rem 0; font-size:0.88rem; color:var(--text);}
.legend-title {font-size: 1.18rem; font-weight: 800; color: #0f172a; margin: 0.15rem 0 0.35rem 0;}
.legend-swatch {display:inline-block; width:16px; height:10px; border-radius:2px;}
@keyframes titleShimmer {0% {background-position: 0% 50%;} 100% {background-position: 220% 50%;}}
@keyframes titleDriftLoop {0% {transform: translateX(-110%); opacity: 0;} 12% {transform: translateX(-55%); opacity: 0.95;} 32% {transform: translateX(-8%); opacity: 1;} 48% {transform: translateX(8%); opacity: 1;} 68% {transform: translateX(60%); opacity: 1;} 82% {transform: translateX(110%); opacity: 0;} 83% {transform: translateX(-110%); opacity: 0;} 100% {transform: translateX(0%); opacity: 1;}}
@keyframes heroReveal {0% {opacity: 0; transform: translateY(10px);} 100% {opacity: 1; transform: translateY(0);} }
.step-strip {display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 0.7rem; margin: 0.75rem 0 1rem 0;}
.step-card, .white-card, .metric-card, .workflow-card, .download-card, .status-card, .preview-card, .health-card {background: var(--panel); border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 5px 16px rgba(15,23,42,0.05);}
.step-card, .white-card, .download-card, .status-card, .preview-card, .health-card {padding: 1rem;}
.metric-card {padding: 0.95rem; text-align: center;}
.workflow-card {padding: 1rem; min-height: 220px;}
.workflow-card h4, .preview-card h4, .white-card h4, .status-card h4, .health-card h4 {margin-top: 0; margin-bottom: 0.35rem; color: var(--text);}
.flood-top {border-top: 7px solid #2563eb;}
.heat-top {border-top: 7px solid #ea580c;}
.multi-top {border-top: 7px solid #7c3aed;}
.custom-top {border-top: 7px solid #0f766e;}
.health-top {border-top: 7px solid #0ea5a4;}
.info-chip {display: inline-flex; align-items: center; padding: 0.5rem 0.85rem; margin: 0.22rem 0.35rem 0.22rem 0; border-radius: 999px; border: 1px solid #d5deef; background: #ffffff; font-size: 0.96rem; color: #0f172a; font-weight: 500;}
.note-box {border: 1px solid #dbe4ff; border-radius: 14px; background: linear-gradient(90deg, #eef2ff 0%, #f5f3ff 100%); padding: 0.9rem 1rem; color: var(--text);}
.upload-box {border: 1px dashed #c8d5ec; border-radius: 16px; background: #fbfdff; padding: 0.95rem 1rem; color: var(--text);}
.ai-box {border-radius: 16px; background: linear-gradient(135deg, #ecfeff 0%, #eef2ff 100%); border: 1px solid #c7d2fe; padding: 1rem; color: var(--text);}
.section-banner {border-radius: 18px; padding: 0.95rem 1rem; color: white; margin-bottom: 0.85rem; box-shadow: 0 8px 22px rgba(15,23,42,0.08);}
.flood-banner {background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%);}
.heat-banner {background: linear-gradient(135deg, #c2410c 0%, #fb923c 100%);}
.multi-banner {background: linear-gradient(135deg, #6d28d9 0%, #a78bfa 100%);}
.custom-banner {background: linear-gradient(135deg, #0f766e 0%, #2dd4bf 100%);}
.health-banner {background: linear-gradient(135deg, #0f766e 0%, #38bdf8 100%);}
.small-muted {color: var(--muted); font-size: 0.93rem;}
.example-title {font-size: 1.04rem; font-weight: 700; color: var(--text);}
.stButton>button {border-radius: 14px; min-height: 2.65rem; font-weight: 600;}
.stButton>button[kind="primary"] {background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important; color: white !important; border: 0 !important; box-shadow: 0 8px 18px rgba(37,99,235,0.18);}
.stButton>button[kind="primary"]:hover {filter: brightness(1.03);}
.nav-wrap button {width: 100%; border-radius: 14px !important; padding: 0.68rem 0.78rem !important; margin-bottom: 0.15rem !important; border: 1px solid rgba(148,163,184,0.35) !important; background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(239,246,255,0.98) 100%) !important; color: #1e293b !important; font-weight: 600 !important;}
.nav-active button {width: 100%; border-radius: 14px !important; padding: 0.68rem 0.78rem !important; margin-bottom: 0.15rem !important; border: 0 !important; background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%) !important; color: white !important; font-weight: 700 !important;}
.status-ok {color:#166534; font-weight:700;}
.status-run {color:#1d4ed8; font-weight:700;}
.status-fail {color:#b91c1c; font-weight:700;}
.status-queue {color:#7c2d12; font-weight:700;}
@media (max-width: 1100px) {
  .block-container {padding-left: 0.8rem; padding-right: 0.8rem;}
  .step-strip {grid-template-columns: 1fr;}
}
@media (max-width: 768px) {
  .hero {padding: 1rem 0.95rem; border-radius: 18px;}
  .hero h1 {font-size: 1.6rem;}
  .info-chip {display: block; width: 100%; margin-right: 0; margin-bottom: 0.45rem; padding: 0.7rem 0.9rem;}
  .workflow-card {min-height: auto;}
  .step-strip {grid-template-columns: 1fr; gap: 0.55rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

HOME_TITLE = "Climate–Health and Health Systems Analytics Platform"
HOME_SUBTITLE = "An interactive multi-hazard research and decision-support platform for climate risk, health, and health systems analysis."
HOME_AUTHOR = "Developed by Sisay Debele"
HOME_AFFILIATION = "REACH Project | London School of Hygiene & Tropical Medicine"
HOME_DESCRIPTION = (
    "This platform brings together climate, hazard, exposure, risk, and health systems analytics in one integrated environment. "
    "It supports the exploration of flood, heat, drought, multi-hazard patterns, and early health-data integration through reproducible workflows, "
    "interactive visualisation, workflow factsheets, and downloadable outputs for research, policy, and operational use."
)
HOME_FEATURES = [
    "Two clear pathways: Explore / Visualise Data and Create a Data Job",
    "Interactive climate, hazard, exposure, health, and health-systems analytics",
    "Built-in statistical analysis and AI-guided analysis support",
    "Workflow factsheets, variable dictionaries, and professional figure export tools",
    "Downloadable filtered data, figures, summary tables, CSV, Excel, and narrative PDF notes",
]

PAGES = [
    "Home",
    "Brazil Flood",
    "Brazil Heat",
    "Zambia Multi-Hazard",
    "Health",
    "Custom Dataset Explorer",
    "Run New Analysis",
    "Guides & Documentation",
    "Results & Downloads",
    "About / Credits",
    "Admin",
]

DISPLAY_PAGE_LABELS = {
    "Home": "Home",
    "Brazil Flood": "Flood",
    "Brazil Heat": "Heatwaves",
    "Zambia Multi-Hazard": "Multi-Hazard",
    "Health": "Health",
    "Custom Dataset Explorer": "Upload & Explore Your Data",
    "Run New Analysis": "Create Data Job",
    "Guides & Documentation": "Guides & Documentation",
    "Results & Downloads": "Results & Downloads",
    "About / Credits": "About / Credits",
    "Admin": "Admin",
}

WORKFLOW_META = {
    "Brazil Flood": {
        "upload_label": "Upload Brazil Flood CSV or ZIP of CSVs",
        "summary": "Flood analytics for exposure, impacts, rainfall context, infrastructure exposure, and health-facility-sensitive indicators.",
        "workflow_file": "brazil_flood.md",
        "metadata_file": "brazil_flood.json",
        "area_candidates": ["municipality", "NM_MUN", "state", "CD_MUN"],
        "date_candidates": ["date", "Date", "timestamp"],
        "year_candidates": ["year", "Year"],
        "month_candidates": ["month", "Month"],
        "banner_class": "flood-banner",
        "card_class": "flood-top",
        "demo_files": ["demo_brazil_flood.csv", "demo_brazil_flood_2.csv"],
    },
    "Brazil Heat": {
        "upload_label": "Upload Brazil Heat CSV or ZIP of CSVs",
        "summary": "Heatwaves analytics for temperature, humidity, seasonality, long-term trends, and climate-health interpretation.",
        "workflow_file": "brazil_heat.md",
        "metadata_file": "brazil_heat.json",
        "area_candidates": ["municipality", "NM_MUN", "CD_MUN"],
        "date_candidates": ["date", "Date", "timestamp"],
        "year_candidates": ["year", "Year"],
        "month_candidates": ["month", "Month"],
        "banner_class": "heat-banner",
        "card_class": "heat-top",
        "demo_files": ["demo_brazil_heat.csv", "demo_brazil_heat_2.csv"],
    },
    "Zambia Multi-Hazard": {
        "upload_label": "Upload Zambia Multi-Hazard CSV or ZIP of CSVs",
        "summary": "Integrated multi-hazard analytics for flood, drought, heatwaves, compound events, risk classes, and susceptibility outputs.",
        "workflow_file": "zambia_multihazard.md",
        "metadata_file": "zambia_multihazard.json",
        "area_candidates": ["DISTRICT", "district", "DIST_CODE", "district_id"],
        "date_candidates": ["date", "Date", "timestamp"],
        "year_candidates": ["year", "Year"],
        "month_candidates": ["month", "Month"],
        "banner_class": "multi-banner",
        "card_class": "multi-top",
        "demo_files": ["demo_zambia_multihazard.csv", "demo_zambia_multihazard_month.csv"],
    },
    "Custom Dataset Explorer": {
        "upload_label": "Upload custom CSV or ZIP of CSVs",
        "summary": "Flexible upload, visualisation, filtering, statistics, and download environment for user datasets and other countries.",
        "workflow_file": "custom_dataset.md",
        "metadata_file": "custom_dataset.json",
        "area_candidates": ["country", "state", "district", "municipality", "location", "site"],
        "date_candidates": ["date", "Date", "timestamp", "datetime"],
        "year_candidates": ["year", "Year"],
        "month_candidates": ["month", "Month"],
        "banner_class": "custom-banner",
        "card_class": "custom-top",
        "demo_files": [],
    },
}

AI_QUICK_GUIDE = {
    "Which plot should I use?": "Use line plots for time series, grouped bar charts for comparing places or months, histograms for distributions, scatter plots for relationships, pie charts for composition, and heatmaps for correlations.",
    "How do I compare Tmax, Tmin, and Tmean together?": "Choose all three variables in the Explore tab, then select Line or Bar plot. The app will place them on one figure with different colours.",
    "When should I use a secondary y-axis?": "Use a secondary y-axis when one variable has a much larger magnitude or different unit than the others, for example exposure counts versus percentages.",
    "What does SPI mean?": "SPI is the Standardized Precipitation Index. Negative values generally indicate drier-than-normal conditions and positive values indicate wetter-than-normal conditions.",
    "How should I think about climate–health links?": "Start with admin-level comparisons, align health and climate periods carefully, and avoid over-precise interpretations when the data were collected under different time windows or spatial rules.",
}

DHS_COUNTRY_HINTS = {
    "Ethiopia": "ET",
    "Zambia": "ZM",
    "Brazil": "BR",
    "Pakistan": "PK",
}


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else "File not found."


def load_metadata(filename: str) -> dict:
    p = METADATA_DIR / filename
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def save_uploaded_aoi_file(uploaded_file, prefix: str) -> str | None:
    if uploaded_file is None:
        return None
    lower_name = uploaded_file.name.lower()
    if lower_name.endswith(".geojson"):
        suffix = ".geojson"
    elif lower_name.endswith(".json"):
        suffix = ".json"
    elif lower_name.endswith(".zip"):
        suffix = ".zip"
    else:
        suffix = Path(uploaded_file.name).suffix or ".dat"
    target = JOBS_DIR / f"{prefix}{suffix}"
    target.write_bytes(uploaded_file.getbuffer())
    return str(target)





def default_admin_settings() -> dict:
    return {
        "demo_badge": "Demo / Pre-backend release",
        "feedback_link": "",
        "feedback_email": "",
        "homepage_map_note": "Static district Flood–Heat–Drought preview for faster homepage loading and cleaner landing-page design.",
        "release_status_text": "Final fixed release: this version keeps the moving homepage title style, the stronger workflow and admin features, restores visible AOI upload controls in Create Data Job, and replaces the heavy interactive homepage district map with a faster static preview. The full interactive map remains inside the relevant workflow pages. Live backend execution and production-grade authentication still need a dedicated backend service.",
    }


def load_admin_settings() -> dict:
    saved = load_json(ADMIN_SETTINGS_PATH, {})
    settings = default_admin_settings()
    settings.update(saved)
    return settings


def save_admin_settings(payload: dict) -> None:
    merged = default_admin_settings()
    merged.update(payload)
    save_json(ADMIN_SETTINGS_PATH, merged)


def default_admin_credentials() -> dict:
    default_password = None
    try:
        default_password = st.secrets.get("admin_password")
    except Exception:
        default_password = None
    return {
        "username": str(os.environ.get("PLATFORM_ADMIN_USERNAME") or "admin"),
        "password": str(default_password or os.environ.get("PLATFORM_ADMIN_PASSWORD") or "demo-admin"),
    }


def load_admin_credentials() -> dict:
    saved = load_json(ADMIN_CREDENTIALS_PATH, {})
    creds = default_admin_credentials()
    creds.update({k: v for k, v in saved.items() if k in {"username", "password"}})
    return creds


def save_admin_credentials(payload: dict) -> None:
    merged = default_admin_credentials()
    merged.update({k: v for k, v in payload.items() if k in {"username", "password"}})
    save_json(ADMIN_CREDENTIALS_PATH, merged)


def reset_admin_credentials() -> dict:
    creds = default_admin_credentials()
    save_json(ADMIN_CREDENTIALS_PATH, creds)
    return creds


def get_admin_password() -> str:
    return load_admin_credentials().get("password", "demo-admin")


def get_admin_username() -> str:
    return load_admin_credentials().get("username", "admin")


def render_feedback_link():
    settings = load_admin_settings()
    feedback_link = settings.get("feedback_link", "").strip()
    feedback_email = settings.get("feedback_email", "").strip()
    if feedback_link:
        st.link_button("Give feedback", feedback_link)
    elif feedback_email:
        st.markdown(f"[Give feedback](mailto:{feedback_email})")


def render_admin_page():
    st.markdown('<div class="section-banner multi-banner"><h2 style="margin:0;">Admin</h2><div>Simple pre-backend admin controls for demo release management. This is local demo administration, not production-grade authentication.</div></div>', unsafe_allow_html=True)
    creds = load_admin_credentials()
    if not st.session_state.get("admin_authenticated", False):
        st.markdown("#### Admin login")
        username = st.text_input("Admin username", value="", key="admin_username_input")
        pw = st.text_input("Admin password", type="password", key="admin_password_input")
        login_cols = st.columns([1, 1, 4])
        with login_cols[0]:
            login_clicked = st.button("Log in", use_container_width=True)
        with login_cols[1]:
            reset_clicked = st.button("Reset local admin", use_container_width=True)
        if login_clicked:
            if username == creds.get("username", "admin") and pw == creds.get("password", "demo-admin"):
                st.session_state["admin_authenticated"] = True
                st.session_state["admin_user"] = username
                st.success("Admin login successful.")
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        if reset_clicked:
            reset_admin_credentials()
            st.success("Local admin credentials reset to defaults.")
            st.info("Default username: admin | Default password: demo-admin")
        st.caption("Demo-only local admin access. Use PLATFORM_ADMIN_USERNAME / PLATFORM_ADMIN_PASSWORD or the Streamlit secret admin_password to change the defaults.")
        return

    settings = load_admin_settings()
    current_creds = load_admin_credentials()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Homepage settings", "Feedback settings", "Admin credentials", "Session / logout", "Exports / jobs"])

    with tab1:
        st.markdown("#### Homepage settings")
        with st.form("admin_homepage_form"):
            demo_badge = st.text_input("Demo badge text", value=settings.get("demo_badge", ""))
            homepage_map_note = st.text_area("Homepage map note", value=settings.get("homepage_map_note", ""), height=100)
            homepage_release = st.text_area("Demo / release status text", value=settings.get("release_status_text", default_admin_settings().get("release_status_text", "")), height=140)
            save_homepage = st.form_submit_button("Save homepage settings")
        if save_homepage:
            save_admin_settings({
                "demo_badge": demo_badge,
                "homepage_map_note": homepage_map_note,
                "release_status_text": homepage_release,
                "feedback_link": settings.get("feedback_link", ""),
                "feedback_email": settings.get("feedback_email", ""),
            })
            st.success("Homepage settings saved.")
            st.rerun()

    with tab2:
        st.markdown("#### Feedback settings")
        with st.form("admin_feedback_form"):
            feedback_link = st.text_input("Feedback URL", value=settings.get("feedback_link", ""))
            feedback_email = st.text_input("Feedback email", value=settings.get("feedback_email", ""))
            save_feedback = st.form_submit_button("Save feedback settings")
        if save_feedback:
            save_admin_settings({
                "demo_badge": settings.get("demo_badge", ""),
                "homepage_map_note": settings.get("homepage_map_note", ""),
                "release_status_text": settings.get("release_status_text", default_admin_settings().get("release_status_text", "")),
                "feedback_link": feedback_link,
                "feedback_email": feedback_email,
            })
            st.success("Feedback settings saved.")
            st.rerun()

    with tab3:
        st.markdown("#### Admin credentials")
        st.info(f"Current username: {current_creds.get('username', 'admin')}")
        with st.form("admin_credentials_form"):
            new_username = st.text_input("New admin username", value=current_creds.get("username", "admin"))
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            creds_submit = st.form_submit_button("Save credentials")
        if creds_submit:
            if current_password != current_creds.get("password", "demo-admin"):
                st.error("Current password is incorrect.")
            elif not new_username.strip():
                st.error("Admin username cannot be empty.")
            elif not new_password:
                st.error("New password cannot be empty.")
            elif new_password != confirm_password:
                st.error("New password and confirmation do not match.")
            else:
                save_admin_credentials({"username": new_username.strip(), "password": new_password})
                st.session_state["admin_user"] = new_username.strip()
                st.success("Admin credentials updated.")
                st.rerun()
        reset_cols = st.columns([1, 3])
        with reset_cols[0]:
            if st.button("Reset local admin password", use_container_width=True):
                reset_admin_credentials()
                st.success("Local admin credentials reset to defaults.")
                st.info("Default username: admin | Default password: demo-admin")
                st.session_state["admin_authenticated"] = False
                st.rerun()

    with tab4:
        st.markdown("#### Session / logout")
        st.write(f"Logged in as: **{st.session_state.get('admin_user', current_creds.get('username', 'admin'))}**")
        st.info(f"Current demo badge: {settings.get('demo_badge', '')}")
        if st.button("Log out", use_container_width=False):
            st.session_state["admin_authenticated"] = False
            st.session_state.pop("admin_user", None)
            st.rerun()

    with tab5:
        st.markdown("#### Exports and job manifests")
        exports = list_manifests("export")
        jobs = list_manifests("job")
        st.write(f"Prepared exports: {len(exports)}")
        if exports:
            st.dataframe(pd.DataFrame(exports), use_container_width=True)
        st.write(f"Data jobs: {len(jobs)}")
        if jobs:
            st.dataframe(pd.DataFrame(jobs), use_container_width=True)

def manifest_path(kind: str, item_id: str) -> Path:
    base = EXPORTS_DIR if kind == "export" else JOBS_DIR
    return base / f"{item_id}.json"


def list_manifests(kind: str) -> list[dict]:
    base = EXPORTS_DIR if kind == "export" else JOBS_DIR
    items = []
    for p in sorted(base.glob("*.json"), reverse=True):
        items.append(load_json(p, {}))
    items = [x for x in items if x]
    items.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
    return items


def register_manifest(kind: str, payload: dict) -> dict:
    payload["updated_at"] = now_iso()
    save_json(manifest_path(kind, payload["id"]), payload)
    return payload


def parse_uploaded_table(uploaded_file):
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".zip"):
        frames = []
        with zipfile.ZipFile(uploaded_file) as zf:
            for member in zf.namelist():
                if member.lower().endswith(".csv"):
                    with zf.open(member) as f:
                        frames.append(pd.read_csv(f))
        return pd.concat(frames, ignore_index=True) if frames else None
    return None


def detect_area_field(df: pd.DataFrame, candidates: list[str]):
    for c in candidates:
        if c in df.columns:
            return c
    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    return obj_cols[0] if obj_cols else None


def detect_date_field(df: pd.DataFrame, candidates: list[str]):
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower():
            return c
    return None


def prep_dataframe(df: pd.DataFrame, meta: dict):
    d = df.copy()
    date_field = detect_date_field(d, meta.get("date_candidates", []))
    if date_field:
        d[date_field] = pd.to_datetime(d[date_field], errors="coerce", dayfirst=True)
    for c in meta.get("year_candidates", []) + meta.get("month_candidates", []):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d, date_field


def numeric_columns(df: pd.DataFrame):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def categorical_columns(df: pd.DataFrame):
    return [c for c in df.columns if df[c].dtype == "object"]


def build_period_column(df: pd.DataFrame, date_field: str | None, aggregation: str):
    d = df.copy()
    if date_field and date_field in d.columns and d[date_field].notna().any():
        if aggregation == "Raw":
            d["_period"] = d[date_field]
        elif aggregation == "Daily":
            d["_period"] = d[date_field].dt.date.astype(str)
        elif aggregation == "Weekly":
            d["_period"] = d[date_field].dt.to_period("W").astype(str)
        elif aggregation == "Monthly":
            d["_period"] = d[date_field].dt.to_period("M").astype(str)
        else:
            d["_period"] = d[date_field].dt.year.astype("Int64").astype(str)
        return d
    year_col = next((c for c in ["year", "Year"] if c in d.columns), None)
    month_col = next((c for c in ["month", "Month"] if c in d.columns), None)
    if year_col:
        if aggregation == "Yearly" or month_col is None:
            d["_period"] = d[year_col].astype("Int64").astype(str)
        else:
            d["_period"] = d[year_col].astype("Int64").astype(str) + "-" + d[month_col].astype("Int64").astype(str).str.zfill(2)
    else:
        d["_period"] = np.arange(len(d)).astype(str)
    return d


def aggregate_multi(df: pd.DataFrame, value_cols: list[str], stat: str):
    fn = {"Mean": "mean", "Sum": "sum", "Max": "max", "Min": "min", "Median": "median"}[stat]
    return df.groupby("_period")[value_cols].agg(fn).reset_index()


def interpret_dataset(d: pd.DataFrame, selected_vars: list[str], aggregation: str, statistic: str, secondary_vars=None):
    msgs = []
    for v in selected_vars[:4]:
        s = pd.to_numeric(d[v], errors="coerce")
        if s.dropna().empty:
            continue
        mean_v = s.mean()
        min_v = s.min()
        max_v = s.max()
        trend = "has limited observations"
        if len(s.dropna()) > 3:
            y = s.dropna().values
            slope = np.polyfit(np.arange(len(y)), y, 1)[0]
            trend = "shows an increasing pattern" if slope > 0 else ("shows a decreasing pattern" if slope < 0 else "is broadly stable")
        msgs.append(f"{v}: mean={mean_v:.3f}, min={min_v:.3f}, max={max_v:.3f}, and {trend} across the selected {aggregation.lower()} period.")
    take_home = "The selected variables help describe climate, hazard, exposure, risk, or health conditions in the filtered dataset."
    if any("SPI" in v for v in selected_vars):
        take_home += " SPI values below zero generally indicate drier-than-normal conditions."
    if any("RX" in v for v in selected_vars):
        take_home += " RX indicators describe heavy rainfall intensity and can point to short-duration precipitation extremes."
    if any(v.lower() == "value" or "health" in v.lower() for v in selected_vars):
        take_home += " Treat survey-based health indicators carefully when comparing them with climate time series."
    if secondary_vars:
        take_home += " A secondary y-axis was used because at least one selected variable has a different magnitude or unit."
    caution = "Interpretation depends on data quality, workflow assumptions, selected aggregation, and the completeness of uploaded fields."
    return msgs, take_home, caution


def make_pdf_bytes(title: str, lines: list[str]):
    bio = BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    _, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, title)
    y -= 24
    c.setFont("Helvetica", 10)
    for line in lines:
        for part in textwrap.wrap(str(line), width=96):
            if y < 52:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(50, y, part)
            y -= 13
    c.save()
    bio.seek(0)
    return bio.read()


def dynamic_ai_suggestion(plot_type, selected_vars, aggregation, use_secondary, secondary_vars):
    notes = []
    if plot_type == "Line":
        notes.append("Line plot is suitable for showing change over time.")
    if plot_type == "Bar" and aggregation in ["Monthly", "Yearly"]:
        notes.append("Grouped bar charts work well for comparing seasonal or annual values across selected variables.")
    if len(selected_vars) > 4:
        notes.append("You selected many variables. Consider reducing the list for clearer interpretation.")
    if not use_secondary and len(selected_vars) >= 2:
        notes.append("If one variable is much larger or has different units, consider enabling the secondary y-axis.")
    if use_secondary and secondary_vars:
        notes.append("Secondary y-axis is active, which is useful for mixed units or very different magnitudes.")
    if any(v.lower().startswith("spi") for v in selected_vars):
        notes.append("SPI is a standardised drought or wetness indicator. Negative values generally indicate drier conditions.")
    if any("RH" in v or "humidity" in v.lower() for v in selected_vars) and any("T" in v for v in selected_vars):
        notes.append("Temperature and humidity together can help interpret heat stress conditions.")
    if any(v.lower() == "value" for v in selected_vars):
        notes.append("Survey-based Value fields may represent percentages or rates. Check metadata and survey year before comparing with hazard outputs.")
    return notes


def unique_non_none(seq):
    seen = set()
    out = []
    for item in seq:
        if item in (None, "None"):
            continue
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def answer_ai_query(user_q, selected_vars=None, aggregation=None, plot_type=None, use_secondary=False, secondary_vars=None):
    q = (user_q or "").strip().lower()
    if not q:
        return None
    selected_vars = selected_vars or []
    secondary_vars = secondary_vars or []
    if any(w in q for w in ["plot", "chart", "graph", "figure"]):
        return "Use line plots for trends over time, bar charts for comparisons, histograms for distributions, scatter plots for relationships, heatmaps for correlations, and priority matrices for screening climate–health patterns."
    if any(w in q for w in ["secondary", "y-axis", "axis"]):
        return "Use a secondary y-axis when variables have very different units or magnitudes, for example exposed population versus intensity index."
    if "spi" in q:
        return "SPI is the Standardized Precipitation Index. Negative values usually indicate drier-than-normal conditions, while positive values indicate wetter-than-normal conditions."
    if any(w in q for w in ["empty", "blank", "no output", "no rows"]):
        return "Empty outputs usually happen when filters return zero rows, when no variable is selected, or when time/geography fields do not align between uploaded tables."
    if any(w in q for w in ["download", "csv", "pdf", "excel", "png", "svg"]):
        return "Use CSV or Excel for further data analysis, PNG/SVG/PDF for publication or slides, and the narrative PDF for a concise written interpretation."
    if any(w in q for w in ["health system", "facility", "readiness", "service", "hospital", "clinic"]):
        return "For health-systems analysis, start with facility, service-use, readiness, or access variables and compare them against flood, heat, or multi-hazard indicators at the same administrative level."
    if any(w in q for w in ["climate", "flood", "heat", "hazard", "multi-hazard"]):
        return "For climate–health analysis, first align geography and time period, then compare one hazard or climate metric with one health or service metric using the correlation, regression, time-series, or AI-guided analysis tabs."
    if "variable" in q:
        if selected_vars:
            return f"You currently selected: {', '.join(selected_vars)}. Check whether these variables match your analysis question and whether they belong on the same axis or model."
        return "Select one or more variables first so the assistant can guide you more specifically."
    return "I can help with variables, plots, statistical models, climate–health comparison, health-systems comparison, downloads, figure design, and why outputs are empty. Ask your question in plain language."


def suggest_analysis_plan(free_text: str, columns: list[str], date_field: str | None = None) -> dict:
    q = (free_text or "").strip().lower()
    if not q:
        return {}
    columns = columns or []

    def find_matches(keywords):
        out = []
        for c in columns:
            lc = c.lower()
            if any(k in lc for k in keywords):
                out.append(c)
        return out

    outcomes, predictors, covariates, models, figures, warnings = [], [], [], [], [], []
    lag_hint = None
    data_type = "cross-sectional"

    if any(w in q for w in ["over time", "time series", "trend", "monthly", "daily", "weekly", "yearly", "lag"]):
        data_type = "time-series" if date_field else "repeated-measures / panel"
    elif any(w in q for w in ["district", "province", "panel", "across years", "across months"]):
        data_type = "panel"

    if any(w in q for w in ["hospital", "visit", "admission", "case", "mortality", "death", "disease", "anc", "delivery", "immun"]):
        outcomes.extend(find_matches(["visit", "admission", "case", "death", "mort", "anc", "delivery", "immun", "value"]))
        predictors.extend(find_matches(["temp", "tmax", "tmean", "heat", "rain", "rx", "spi", "ssi", "flood", "hazard"]))
        covariates.extend(find_matches(["humidity", "rh", "population", "year", "month", "season", "facility", "urban", "region"]))
        models.extend(["Poisson regression", "Negative binomial regression", "GAM-style trend model", "Lag analysis"])
        figures.extend(["Time-series plot", "Exposure-outcome scatter", "Lag-response plot", "Monthly summary plot"])
        lag_hint = "Consider lags of 0–3 periods first, then test a wider lag window if the data are frequent enough."
    if any(w in q for w in ["affect", "association", "relationship", "effect"]):
        models.extend(["Linear regression", "Multiple linear regression", "Pearson/Spearman correlation"])
        figures.extend(["Scatter plot with trend line", "Correlation heatmap"])
    if any(w in q for w in ["binary", "yes/no", "odds", "probability"]):
        models.append("Logistic regression")
    if any(w in q for w in ["cluster", "hotspot", "space", "spatial"]):
        figures.append("Spatial map / hotspot screening")
    if any(w in q for w in ["anomaly", "extreme", "threshold"]):
        models.append("Anomaly analysis")
        figures.append("Anomaly time-series")
    if date_field is None and data_type == "time-series":
        warnings.append("A clear date field was not detected, so time-series models may not work reliably.")
    if not predictors:
        predictors = find_matches(["temp", "rain", "flood", "heat", "spi", "ssi", "rx", "hazard", "exposed", "humidity"])
    if not outcomes:
        outcomes = find_matches(["value", "count", "rate", "visit", "admission", "death"])
    if not covariates:
        covariates = find_matches(["humidity", "population", "month", "year", "facility", "region"])
    if not models:
        models = ["Summary statistics", "Correlation", "Linear regression"]
    if not figures:
        figures = ["Time-series plot" if date_field else "Grouped comparison plot", "Summary table"]
    warnings.append("Suggested models are advisory only. Check whether the data structure, sampling design, and variable definitions support the chosen model.")
    return {
        "outcome": outcomes[:5],
        "predictors": predictors[:8],
        "covariates": covariates[:8],
        "data_type": data_type,
        "models": list(dict.fromkeys(models))[:6],
        "figures": list(dict.fromkeys(figures))[:6],
        "lag_hint": lag_hint,
        "warnings": warnings[:4],
    }


def render_ai_box(workflow_name=None, plot_type=None, selected_vars=None, aggregation=None, use_secondary=False, secondary_vars=None, columns=None, date_field=None):
    st.markdown("#### AI-guided analysis support")
    st.markdown(
        '<div class="ai-box">Use this assistant in two ways: ask a direct workflow question, or describe the full analysis you want to do in your own words. The assistant then suggests likely outcome variables, predictors, covariates, models, figures, lag structure, and limitations.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Describe the analysis you want to do in your own words**")
    free_text = st.text_area(
        "Describe the analysis you want to do in your own words",
        label_visibility="collapsed",
        placeholder="Example: I want to assess whether heat affects hospital visits over time and whether rainfall or seasonality should be controlled for.",
        key=f"analysis_prompt_{workflow_name or 'home'}",
        height=110,
    )
    if free_text:
        plan = suggest_analysis_plan(free_text, columns or selected_vars or [], date_field=date_field)
        if plan:
            st.markdown("**Suggested analysis plan**")
            c1, c2 = st.columns(2)
            with c1:
                st.write("- **Likely outcome:** " + (", ".join(plan.get("outcome", [])) or "Not identified from current columns"))
                st.write("- **Likely predictors:** " + (", ".join(plan.get("predictors", [])) or "Not identified from current columns"))
                st.write("- **Possible covariates:** " + (", ".join(plan.get("covariates", [])) or "Not identified from current columns"))
                st.write("- **Data structure:** " + plan.get("data_type", "Unknown"))
            with c2:
                st.write("- **Suggested models:** " + ", ".join(plan.get("models", [])))
                st.write("- **Suggested figures:** " + ", ".join(plan.get("figures", [])))
                if plan.get("lag_hint"):
                    st.write("- **Lag suggestion:** " + plan["lag_hint"])
            for warn in plan.get("warnings", []):
                st.caption("Warning: " + warn)

    st.markdown("**Ask the assistant directly**")
    user_q = st.text_input(
        "Ask the assistant",
        label_visibility="collapsed",
        placeholder="Example: Which model should I use for count outcomes over time?",
        key=f"user_ai_{workflow_name or 'home'}",
    )
    if user_q:
        st.info(answer_ai_query(user_q, selected_vars, aggregation, plot_type, use_secondary, secondary_vars))

    with st.expander("Quick guidance examples"):
        example = st.selectbox("Choose an example question", ["None"] + list(AI_QUICK_GUIDE.keys()), key=f"ai_examples_{workflow_name or 'home'}")
        if example != "None":
            st.info(AI_QUICK_GUIDE[example])

    if selected_vars:
        st.markdown("**Live suggestions based on selected variables**")
        for note in dynamic_ai_suggestion(plot_type, selected_vars, aggregation, use_secondary, secondary_vars or []):
            st.write("- " + note)


def render_status_box(title: str, status: str, message: str, progress: float | None = None, extra_lines: list[str] | None = None):

    status_class = {"queued": "status-queue", "running": "status-run", "completed": "status-ok", "failed": "status-fail"}.get(status, "status-run")
    st.markdown(f'<div class="status-card"><h4>{title}</h4><div class="{status_class}">{status.upper()}</div><p>{message}</p></div>', unsafe_allow_html=True)
    if progress is not None:
        st.progress(int(progress * 100))
    if extra_lines:
        for line in extra_lines:
            st.write(line)


def load_demo_dataframe(filename: str) -> pd.DataFrame | None:
    p = SAMPLE_DIR / filename
    if p.exists():
        return pd.read_csv(p)
    return None


def open_multi_hazard_interactive_map():
    st.session_state["page"] = "Zambia Multi-Hazard"
    st.session_state["open_multi_map"] = True
    st.rerun()

def open_reach_dataset_module(module_key: str):
    module_lookup = {
        "Flood": "Brazil Flood",
        "Heatwaves": "Brazil Heat",
        "Multi-Hazard": "Zambia Multi-Hazard",
        "Health": "Health",
    }
    st.session_state["page"] = module_lookup.get(module_key, "Brazil Flood")
    st.rerun()


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().lower()).strip("_")


def get_health_outcome_candidates(health_df: pd.DataFrame) -> list[str]:
    priority = []
    secondary = []
    for c in numeric_columns(health_df):
        cl = c.lower()
        if c in {"SurveyYear"}:
            continue
        if cl.endswith("_demo") or any(k in cl for k in ["flood", "heat", "hazard", "population_exposed", "hcf", "tmax", "spi", "ssi", "rx1day"]):
            continue
        if c == "Value" or any(k in cl for k in ["coverage", "visit", "outcome", "response", "rate", "prevalence", "incidence", "mortality", "anc", "pnc", "stunting", "wasting", "anaemia", "anemia"]):
            priority.append(c)
        else:
            secondary.append(c)
    ordered = []
    for c in priority + secondary:
        if c not in ordered:
            ordered.append(c)
    return ordered

def get_health_covariate_candidates(health_df: pd.DataFrame, outcome: str | None = None) -> list[str]:
    return [c for c in get_health_outcome_candidates(health_df) if c != outcome]


def aggregate_panel_series(df: pd.DataFrame, x: str | None, yvars: list[str], freq: str):
    work = df.copy()
    if x is None or x not in work.columns or freq == "Raw":
        return work
    series = work[x]
    if pd.api.types.is_datetime64_any_dtype(series):
        if freq == "Daily":
            work["_panel_x"] = series.dt.strftime("%Y-%m-%d")
        elif freq == "Weekly":
            work["_panel_x"] = series.dt.to_period("W").astype(str)
        elif freq == "Monthly":
            work["_panel_x"] = series.dt.to_period("M").astype(str)
        elif freq == "Yearly":
            work["_panel_x"] = series.dt.to_period("Y").astype(str)
        else:
            work["_panel_x"] = series
    else:
        work["_panel_x"] = series.astype(str)
    nums = [y for y in yvars if y in work.columns]
    if not nums:
        return work
    for y in nums:
        work[y] = pd.to_numeric(work[y], errors="coerce")
    grouped = work.groupby("_panel_x", as_index=False)[nums].mean(numeric_only=True)
    return grouped.rename(columns={"_panel_x": x})

def build_panel_trace_figure(df: pd.DataFrame, panel_specs: list[dict], rows: int, cols: int, title: str = ""):
    subplot_titles = [spec.get('title', f"Panel {i+1}") for i, spec in enumerate(panel_specs)]
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles)
    for idx, spec in enumerate(panel_specs):
        r = idx // cols + 1
        c = idx % cols + 1
        ptype = spec.get('plot_type', 'Line')
        x = spec.get('x')
        yvars = spec.get('yvars', [])
        freq = spec.get('freq', 'Raw')
        if not yvars:
            continue
        plot_df = aggregate_panel_series(df, x, yvars, freq)
        if ptype == 'Heatmap':
            use = [v for v in yvars if v in plot_df.columns]
            if len(use) >= 2:
                corr = plot_df[use].apply(pd.to_numeric, errors='coerce').corr()
                fig.add_trace(go.Heatmap(z=corr.values, x=use, y=use, coloraxis='coloraxis', showscale=False), row=r, col=c)
        elif ptype == 'Histogram':
            y = yvars[0]
            if y in plot_df.columns:
                fig.add_trace(go.Histogram(x=plot_df[y], name=y, showlegend=False), row=r, col=c)
        elif ptype == 'Box':
            for y in yvars:
                if y in plot_df.columns:
                    fig.add_trace(go.Box(y=plot_df[y], name=y, showlegend=False), row=r, col=c)
        elif ptype == 'Scatter':
            if len(yvars) >= 2 and all(y in plot_df.columns for y in yvars[:2]):
                x_series = plot_df[x] if x and x in plot_df.columns else plot_df[yvars[0]]
                fig.add_trace(go.Scatter(x=x_series, y=plot_df[yvars[1]], mode='markers', showlegend=False), row=r, col=c)
        elif ptype == 'Bar':
            y = yvars[0]
            if y in plot_df.columns:
                x_series = plot_df[x] if x and x in plot_df.columns else list(range(len(plot_df)))
                fig.add_trace(go.Bar(x=x_series, y=plot_df[y], showlegend=False), row=r, col=c)
        else:
            for y in yvars:
                if y in plot_df.columns:
                    x_series = plot_df[x] if x and x in plot_df.columns else list(range(len(plot_df)))
                    fig.add_trace(go.Scatter(x=x_series, y=plot_df[y], mode='lines+markers', showlegend=False), row=r, col=c)
    fig.update_layout(title=title, height=max(560, rows * 320), coloraxis=dict(colorscale='Viridis'))
    return fig

def render_funder_logos_small():
    ahrc = BASE_DIR / 'FUNDER_AHRC.png'
    esrc = BASE_DIR / 'FUNDER_ESRC.png'
    if ahrc.exists() or esrc.exists():
        st.markdown('### Our funders')
        c1, c2, c3 = st.columns([0.8, 0.8, 2.2], gap="medium")
        with c1:
            if ahrc.exists():
                st.image(str(ahrc), width=115)
        with c2:
            if esrc.exists():
                st.image(str(esrc), width=115)
        with c3:
            st.markdown('<div class="white-card"><p class="small-muted">Supported by UKRI funders. The platform is presented here for research, policy, and programme-facing climate–health analysis.</p></div>', unsafe_allow_html=True)

def render_how_to_use_section():
    st.markdown('### How to use this platform')
    steps = st.columns(4)
    content = [
        ('1. Choose a pathway', 'Start with Data Analysis and Visualisation or Create a Data Job.'),
        ('2. Load or define data', 'Open a REACH dataset, upload your own file, or define a new AOI.'),
        ('3. Analyse and interpret', 'Use Explore for figures, statistics, climate–health modelling, and AI-guided support.'),
        ('4. Export and share', 'Download figures, tables, CSV, Excel, PDF, TIFF, JPG, or editable HTML outputs.'),
    ]
    for col, (title, desc) in zip(steps, content):
        with col:
            st.markdown(f'<div class="step-card"><h4>{title}</h4><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)


def render_who_for_section():
    st.markdown('### Who this platform is for')
    cols = st.columns(4)
    items = [
        ('Researchers', 'Structured climate, hazard, and climate–health analysis without rebuilding workflows from scratch.'),
        ('Policy makers', 'Clear comparisons, risk preview, summary outputs, and downloadable evidence for planning.'),
        ('Programme teams', 'Practical decision support for climate risk, exposure, health, and health-systems-sensitive outputs.'),
        ('Students and analysts', 'Upload data, explore interactively, and export publication-ready figures and tables without coding.'),
    ]
    for col, (title, desc) in zip(cols, items):
        with col:
            st.markdown(f'<div class="white-card"><h4 style="margin-top:0;">{title}</h4><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)


def render_hero():
    settings = load_admin_settings()
    st.markdown(f'<div class="hero"><h1><span class="hero-title-wrap"><span class="hero-title-slide">{HOME_TITLE}</span></span></h1><div class="beta-badge">{settings.get("demo_badge", "Demo / Pre-backend release")}</div><p>{HOME_SUBTITLE}</p><p><strong>{HOME_AUTHOR}</strong></p><p>{HOME_AFFILIATION}</p></div>', unsafe_allow_html=True)
    l1, l2, txt = st.columns([1.1, 1.1, 4], gap="medium")
    with l1:
        if (BASE_DIR / "LSHTM_LOGO.png").exists():
            st.image(str(BASE_DIR / "LSHTM_LOGO.png"), use_container_width=True)
    with l2:
        if (BASE_DIR / "REACH_PROJECT_LOGO.png").exists():
            st.image(str(BASE_DIR / "REACH_PROJECT_LOGO.png"), use_container_width=True)
    with txt:
        st.markdown(HOME_DESCRIPTION)


def build_brazil_home_preview(df: pd.DataFrame) -> pd.DataFrame:
    annual = (
        df.groupby("year")[["flood_intensity", "population_exposed", "HCFs_exposed", "max_monthly_rainfall_mm"]]
        .mean()
        .reset_index()
        .sort_values("year")
        .copy()
    )
    annual["population_exposed_thousand"] = (annual["population_exposed"] / 1000).round(2)
    rain = annual["max_monthly_rainfall_mm"].astype(float)
    flood = annual["flood_intensity"].astype(float)
    annual["rainfall_context_scaled"] = (((rain - rain.min()) / (rain.max() - rain.min() + 1e-9)) * flood.max()).round(2)
    annual["extreme_year_flag"] = np.where(annual["flood_intensity"] >= annual["flood_intensity"].quantile(0.75), "Higher flood year", "Lower flood year")
    return annual



@st.cache_data(show_spinner=False)
def load_zambia_hfd_geojson():
    shp_path = BASE_DIR / "Zambia_116_District.shp"
    risk_path = BASE_DIR / "risk_table_district_HFD_compound_HFD_quantile_1981_2025.csv"
    if not shp_path.exists() or not risk_path.exists():
        return None, None

    reader = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in reader.fields[1:]]
    risk = pd.read_csv(risk_path).copy()
    risk["DIST_CODE"] = pd.to_numeric(risk["DIST_CODE"], errors="coerce").astype("Int64")
    risk["DISTRICT_KEY"] = risk["DISTRICT"].astype(str).str.strip().str.upper()

    code_lookup = {
        int(row["DIST_CODE"]): row.to_dict()
        for _, row in risk.dropna(subset=["DIST_CODE"]).iterrows()
    }
    name_lookup = {row["DISTRICT_KEY"]: row.to_dict() for _, row in risk.iterrows()}

    features = []
    for shape_record in reader.iterShapeRecords():
        rec = dict(zip(fields, shape_record.record))
        code_val = pd.to_numeric(rec.get("DIST_CODE"), errors="coerce")
        district_key = str(rec.get("DISTRICT", "")).strip().upper()
        match = None
        if pd.notna(code_val):
            match = code_lookup.get(int(code_val))
        if match is None:
            match = name_lookup.get(district_key, {})

        props = {k: rec.get(k) for k in fields}
        props["DISTRICT"] = rec.get("DISTRICT")
        props["DIST_CODE"] = int(code_val) if pd.notna(code_val) else rec.get("DIST_CODE")
        props["compound_HFD"] = float(match.get("compound_HFD")) if match and pd.notna(match.get("compound_HFD")) else None
        props["risk_label"] = str(match.get("risk_label", "Unknown")) if match else "Unknown"
        props["risk_class"] = int(match.get("risk_class")) if match and pd.notna(match.get("risk_class")) else None

        features.append({
            "type": "Feature",
            "geometry": shape_record.shape.__geo_interface__,
            "properties": props,
        })

    minx, miny, maxx, maxy = reader.bbox
    meta = {
        "center": [(miny + maxy) / 2, (minx + maxx) / 2],
        "bbox": [minx, miny, maxx, maxy],
        "feature_count": len(features),
    }
    return {"type": "FeatureCollection", "features": features}, meta


def add_selected_basemap(m, basemap_name: str):
    if basemap_name == "OpenStreetMap":
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    elif basemap_name == "Esri Satellite":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Esri Satellite",
        ).add_to(m)
    elif basemap_name == "CartoDB Positron":
        folium.TileLayer("CartoDB positron", name="CartoDB Positron").add_to(m)
    else:
        folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark Matter").add_to(m)




def home_spatial_preview():
    st.markdown("### Multi-Hazard map preview")
    preview_path = BASE_DIR / "home_static_multirisk_preview.png"
    risk_path = BASE_DIR / "risk_table_district_HFD_compound_HFD_quantile_1981_2025.csv"
    if preview_path.exists():
        c1, c2 = st.columns([1.75, 1.0], gap="large")
        with c1:
            st.image(str(preview_path), use_container_width=True)
        with c2:
            settings = load_admin_settings()
            if risk_path.exists():
                risk = pd.read_csv(risk_path)
                top_row = risk.sort_values("compound_HFD", ascending=False).iloc[0]
                top_msg = f'<p class="small-muted"><strong>Highest mapped district:</strong> {top_row["DISTRICT"]} with compound Flood-Heat-Drought score <strong>{top_row["compound_HFD"]:.3f}</strong> and risk class <strong>{top_row["risk_label"]}</strong>.</p>'
            else:
                top_msg = '<p class="small-muted">Risk summary table is not packaged, so only the static preview image is shown.</p>'
            st.markdown(
                f"""<div class="preview-card"><h4>Static map summary</h4>
                <p class="small-muted">{settings.get("homepage_map_note", "Static district Flood-Heat-Drought preview for faster homepage loading and cleaner landing-page design.")}</p>
                {top_msg}
                <p class="small-muted">The homepage keeps a static preview for speed. The full interactive map stays inside the <strong>Multi-Hazard</strong> workflow.</p></div>""",
                unsafe_allow_html=True,
            )
            if st.button("Open interactive Multi-Hazard map", use_container_width=True, key="home_open_multi_map"):
                open_multi_hazard_interactive_map()
            st.caption("This opens the Multi-Hazard workflow and displays the full interactive Zambia district risk map.")
    else:
        st.info("Static multi-hazard preview image is unavailable.")

def home_example_preview():
    st.markdown("### Climate–health systems preview")
    df = load_demo_dataframe("demo_brazil_flood.csv")
    if df is None:
        st.info("Demo preview is unavailable because the example dataset was not found.")
        return
    preview = build_brazil_home_preview(df)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=preview["year"],
            y=preview["flood_intensity"],
            name="Flood intensity",
            marker_color="#2563eb",
            opacity=0.82,
            hovertemplate="Year %{x}<br>Flood intensity: %{y:.1f}<extra></extra>",
            yaxis="y",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=preview["year"],
            y=preview["rainfall_context_scaled"],
            name="Maximum precipitation (scaled context)",
            mode="lines+markers",
            line=dict(color="#334155", width=5.6, dash="dash"),
            marker=dict(size=9, color="#334155", symbol="x"),
            customdata=np.stack([preview["max_monthly_rainfall_mm"]], axis=-1),
            hovertemplate="Year %{x}<br>Maximum precipitation: %{customdata[0]:.1f} mm<extra></extra>",
            yaxis="y",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=preview["year"],
            y=preview["population_exposed_thousand"],
            name="Population exposed (thousand)",
            mode="lines+markers",
            line=dict(color="#ea580c", width=3),
            marker=dict(size=9, color="#ea580c", symbol="circle"),
            hovertemplate="Year %{x}<br>Population exposed: %{y:.2f}k<extra></extra>",
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=preview["year"],
            y=preview["HCFs_exposed"],
            name="HCFs exposed",
            mode="lines+markers",
            line=dict(color="#dc2626", width=3),
            marker=dict(size=9, color="#dc2626", symbol="diamond"),
            hovertemplate="Year %{x}<br>HCFs exposed: %{y:.1f}<extra></extra>",
            yaxis="y2",
        )
    )

    extreme_years = preview.nlargest(2, "flood_intensity")[["year", "flood_intensity"]]
    for i, (_, r) in enumerate(extreme_years.iterrows()):
        fig.add_annotation(
            x=r["year"], y=r["flood_intensity"], yref="y",
            text="Extreme flood year" if i == 0 else "High flood year", showarrow=True, arrowhead=2, ax=0, ay=-35,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#2563eb"
        )

    fig.update_layout(
        title="Brazil case-study preview: flood intensity, rainfall context, population exposed, and HCF exposure",
        height=520,
        bargap=0.18,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=40, r=70, t=70, b=40),
        yaxis=dict(title="Flood intensity index", showgrid=True, zeroline=False),
        yaxis2=dict(title="Population exposed (thousand) / HCFs exposed", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title="Year"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    c1, c2 = st.columns([1.75, 1.05], gap="large")
    with c1:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Blue bars show flood intensity. The darker dashed grey line gives scaled maximum precipitation as rainfall context so rainfall remains clearly visible. Orange and red lines show exposed population and exposed health facilities (HCFs). This homepage figure is exploratory and not intended for causal inference.")
    with c2:
        worst = preview.loc[preview["flood_intensity"].idxmax()]
        summary_html = f'''<div class="preview-card"><h4>Example summary</h4>
            <p class="small-muted">This landing-page preview focuses on a scientifically safer climate–health systems story: <strong>flood intensity</strong>, <strong>rainfall context</strong>, <strong>population exposed</strong>, and <strong>health-facility exposure</strong>. It shows the type of joined hazard–exposure output the platform can generate without overclaiming health outcome effects on the homepage.</p>
            <p class="small-muted"><strong>Highest-impact year:</strong> {int(worst['year'])}, when mean flood intensity reached <strong>{worst['flood_intensity']:.1f}</strong>, maximum precipitation was around <strong>{worst['max_monthly_rainfall_mm']:.1f} mm</strong>, around <strong>{worst['population_exposed_thousand']:.2f} thousand people</strong> were exposed, and <strong>{worst['HCFs_exposed']:.1f}</strong> health facilities were exposed.</p>
            <p class="small-muted"><strong>Why this matters:</strong> it gives users a quick view of how hazard intensity, validation context, exposed population, and exposed health facilities can be explored together. For DHS and health outcome comparisons, use the <strong>Health</strong> page.</p></div>'''
        st.markdown(summary_html, unsafe_allow_html=True)



def render_analysis_suite_chips():
    chips = ["Summary", "Correlation", "Regression", "Time Series", "Spatial", "Advanced", "AI-Guided Analysis", "Figure & Data Export"]
    st.markdown("".join(f'<span class="info-chip">{c}</span>' for c in chips), unsafe_allow_html=True)


def render_pathway_guidance_box():
    st.markdown(
        '<div class="note-box"><strong>Pathway 1 · Data Analysis and Visualisation</strong> — explore built-in REACH Project datasets or upload your own data to visualise, compare, analyse, run structured statistical workflows, receive AI-guided support, and export publication-ready outputs.<br><br><strong>Pathway 2 · Create a new data job for any region in the world</strong> — define an AOI using country, spatial unit type, uploaded boundary, map drawing, predefined area, or coordinates and buffer; choose variables, time period, temporal resolution, and outputs; then create a processing request.</div>',
        unsafe_allow_html=True,
    )


def render_home():
    render_hero()

    st.markdown("### Start here")
    left, right = st.columns([1.45, 1.0], gap="large")
    with left:
        st.markdown('<div class="workflow-card flood-top"><h3 style="margin-top:0;">Pathway 1 · Data Analysis and Visualisation</h3><p class="small-muted">Open a built-in REACH Project dataset or upload your own file to visualise, compare, analyse, run structured statistical workflows, receive AI-guided support, and export publication-ready outputs.</p></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.1, 1.0, 0.9], gap="medium")
        with c1:
            reach_choice = st.selectbox("Choose REACH Project dataset", ["Flood", "Heatwaves", "Multi-Hazard", "Health"], key="home_reach_choice")
            if st.button("Open REACH Project dataset", use_container_width=True, type="primary", key="home_open_reach_dataset"):
                open_reach_dataset_module(reach_choice)
        with c2:
            if st.button("Open upload-based analysis workspace", use_container_width=True, type="primary", key="home_open_custom_upload"):
                st.session_state["page"] = "Custom Dataset Explorer"
                st.rerun()
        with c3:
            if st.button("Open Guides and Documentation", use_container_width=True, type="primary", key="home_open_docs"):
                st.session_state["page"] = "Guides & Documentation"
                st.rerun()

    with right:
        st.markdown('<div class="workflow-card multi-top"><h3 style="margin-top:0;">Pathway 2 · Create a new data job for any region in the world</h3><p class="small-muted">Define an AOI using country, spatial unit type, uploaded boundary, map drawing, predefined area, or coordinates and buffer; choose variables, dates, temporal resolution, and outputs; then create a processing request.</p></div>', unsafe_allow_html=True)
        if st.button("Open Create Data Job", use_container_width=True, type="primary", key="home_open_create_job"):
            st.session_state["page"] = "Run New Analysis"
            st.rerun()
        st.markdown('<div class="white-card"><h4 style="margin-top:0;">What this pathway supports</h4><p class="small-muted">Country and region selection, uploaded AOI, drawn AOI, coordinates and buffer, temporal resolution, requested outputs, and downstream job submission.</p></div>', unsafe_allow_html=True)

    st.markdown("### Core analytics modules")
    cols = st.columns(5)
    cards = [
        ("Brazil Flood", "Flood", "Explore flood extent, rainfall context, exposure, infrastructure, and health-facility-sensitive indicators."),
        ("Brazil Heat", "Heatwaves", "Explore temperature, humidity, seasonality, long-term trends, and climate-health interpretation."),
        ("Zambia Multi-Hazard", "Multi-Hazard", "Explore flood, drought, heatwave indicators, compound events, and district risk classes."),
        ("Health", "Health", "Load DHS-style health data, inspect patterns, and link health outcomes with climate predictors."),
        ("Custom Dataset Explorer", "Upload & Explore", "Upload a CSV or ZIP from any country or project and move directly into analysis and export."),
    ]
    for col, (page_name, label, desc) in zip(cols, cards):
        card_class = "health-top" if page_name == "Health" else WORKFLOW_META.get(page_name, {}).get("card_class", "custom-top")
        with col:
            st.markdown(f'<div class="workflow-card {card_class}"><h4>{label}</h4><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)
            if st.button(f"Open {label}", use_container_width=True, key=f"home_module_{page_name}"):
                st.session_state["page"] = page_name
                st.rerun()

    st.markdown("### Platform preview")
    st.caption("The static Multi-Hazard preview is shown first for a faster landing page. The full interactive map remains inside the Multi-Hazard workflow.")
    preview_tabs = st.tabs(["Static Multi-Hazard map preview", "Climate–health preview"])
    with preview_tabs[0]:
        home_spatial_preview()
    with preview_tabs[1]:
        home_example_preview()

    render_ai_box("Home", columns=["flood_intensity", "population_exposed", "Tmax_C", "SPI_3", "Value"], date_field="date")
    render_funder_logos_small()
    render_feedback_link()
    settings = load_admin_settings()
    with st.expander("Demo / release status", expanded=False):
        st.markdown(f'<div class="note-box">{settings.get("release_status_text", "")}</div>', unsafe_allow_html=True)

def render_upload_block(page_name: str, meta: dict):
    st.markdown("#### Data input")
    source = st.radio("Choose data source", ["Use REACH Project dataset", "Upload my own CSV or ZIP"], key=f"source_{page_name}")
    if source == "Use REACH Project dataset":
        demos = [x for x in meta.get("demo_files", []) if (SAMPLE_DIR / x).exists()]
        if demos:
            labels = [Path(x).stem.replace("_", " ").title() for x in demos]
            demo_label = st.selectbox("Choose REACH Project data file", labels, key=f"demo_choice_{page_name}")
            demo_name = demos[labels.index(demo_label)]
            demo_df = load_demo_dataframe(demo_name)
            if demo_df is not None:
                st.session_state[f"data_{page_name}"] = demo_df
                st.success(f"Loaded REACH Project dataset: {demo_name} ({len(demo_df):,} rows)")
                st.markdown('<div class="note-box"><strong>REACH Project dataset mode:</strong> this workflow is using a built-in REACH Project dataset from <code>sample_data/</code>. Case studies are included as examples, while the platform is intended for broader use with uploaded data and later backend processing.</div>', unsafe_allow_html=True)
        else:
            st.info("No built-in REACH Project dataset is configured for this page yet. Use upload mode.")
        return st.session_state.get(f"data_{page_name}")

    st.markdown(f'<div class="upload-box"><strong>{meta["upload_label"]}</strong><br><span class="small-muted">Accepted: single CSV or ZIP containing one or more CSV files.</span></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(meta["upload_label"], type=["csv", "zip"], key=f"upload_{page_name}")
    if uploaded is not None:
        parsed = parse_uploaded_table(uploaded)
        if parsed is not None and not parsed.empty:
            st.session_state[f"data_{page_name}"] = parsed
            st.success(f"Loaded {len(parsed):,} rows from {uploaded.name}")
        else:
            st.error("No usable CSV file was found, or the uploaded file was empty.")
    return st.session_state.get(f"data_{page_name}")


def render_variable_dictionary(meta: dict):
    md = load_metadata(meta["metadata_file"])
    rows = [{"variable": x.get("name", ""), "label": x.get("label", ""), "unit": x.get("unit", ""), "description": x.get("description", "")} for x in md.get("variables", [])]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No variable dictionary found.")


def build_secondary_axis_figure(source: pd.DataFrame, xcol: str, selected_vars: list[str], secondary_vars: list[str]):
    fig = go.Figure()
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24
    for i, var in enumerate(selected_vars):
        fig.add_trace(go.Scatter(x=source[xcol], y=source[var], mode="lines+markers", name=var, yaxis="y2" if var in secondary_vars else "y1", line=dict(color=palette[i % len(palette)], width=2)))
    fig.update_layout(yaxis=dict(title="Primary axis"), yaxis2=dict(title="Secondary axis", overlaying="y", side="right"), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), height=560, margin=dict(l=40, r=40, t=40, b=40))
    return fig


def write_export_outputs(page_name: str, df: pd.DataFrame, pdf_lines: list[str], export_title: str, export_id: str) -> tuple[Path, Path]:
    csv_path = EXPORTS_DIR / f"{export_id}_filtered.csv"
    pdf_path = EXPORTS_DIR / f"{export_id}_summary.pdf"
    df.to_csv(csv_path, index=False)
    pdf_bytes = make_pdf_bytes(export_title, pdf_lines)
    pdf_path.write_bytes(pdf_bytes)
    return csv_path, pdf_path


def run_export_pipeline(page_name: str, df: pd.DataFrame, pdf_lines: list[str], title: str) -> dict:
    export_id = f"export_{uuid4().hex[:10]}"
    manifest = {
        "id": export_id,
        "kind": "export",
        "page": page_name,
        "title": title,
        "status": "queued",
        "message": "Preparing export.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "csv_path": None,
        "pdf_path": None,
    }
    register_manifest("export", manifest)
    stages = [
        "Validating selected filters",
        "Preparing filtered dataset",
        "Generating narrative PDF",
        "Registering results",
    ]
    bar = st.progress(0)
    message = st.empty()
    for i, stage in enumerate(stages, start=1):
        manifest["status"] = "running"
        manifest["message"] = stage
        register_manifest("export", manifest)
        message.info(stage)
        if stage == "Validating selected filters":
            if df is None or df.empty:
                manifest["status"] = "failed"
                manifest["message"] = "Export failed because the selected filters returned no rows."
                register_manifest("export", manifest)
                message.error(manifest["message"])
                return manifest
        elif stage == "Generating narrative PDF":
            csv_path, pdf_path = write_export_outputs(page_name, df, pdf_lines, title, export_id)
            manifest["csv_path"] = str(csv_path)
            manifest["pdf_path"] = str(pdf_path)
        bar.progress(int(i / len(stages) * 100))
    manifest["status"] = "completed"
    manifest["message"] = "Export completed successfully. Results are now available in Results & Downloads and below."
    register_manifest("export", manifest)
    message.success(manifest["message"])
    return manifest


def render_export_download_buttons(manifest: dict):
    csv_path = Path(manifest.get("csv_path", "")) if manifest.get("csv_path") else None
    pdf_path = Path(manifest.get("pdf_path", "")) if manifest.get("pdf_path") else None
    c1, c2 = st.columns(2)
    with c1:
        if csv_path and csv_path.exists():
            st.download_button("Download filtered CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv", use_container_width=True, key=f"dlcsv_{manifest['id']}")
    with c2:
        if pdf_path and pdf_path.exists():
            st.download_button("Download narrative PDF", pdf_path.read_bytes(), file_name=pdf_path.name, mime="application/pdf", use_container_width=True, key=f"dlpdf_{manifest['id']}")




def get_figure_presets():
    return {
        "General Medical / Public Health": {"template": "simple_white", "font_size": 16, "bg": "white", "grid": True},
        "Environmental Epidemiology / Environmental Health": {"template": "simple_white", "font_size": 15, "bg": "white", "grid": True},
        "Climate and Planetary Health": {"template": "simple_white", "font_size": 16, "bg": "#fbfdff", "grid": True},
        "Biometeorology / Climate Impacts": {"template": "simple_white", "font_size": 15, "bg": "white", "grid": True},
    }


def available_palettes():
    return {
        "Plotly": px.colors.qualitative.Plotly,
        "Safe": px.colors.qualitative.Safe,
        "Dark24": px.colors.qualitative.Dark24,
        "Set2": px.colors.qualitative.Set2,
        "Pastel": px.colors.qualitative.Pastel,
    }


def apply_figure_customisation(fig, settings: dict, plot_type: str | None = None, source_df: pd.DataFrame | None = None, selected_vars: list[str] | None = None):
    if fig is None:
        return None
    presets = get_figure_presets()
    preset = presets.get(settings.get("preset"), presets["General Medical / Public Health"])
    fig.update_layout(
        template=preset.get("template", "simple_white"),
        title={"text": settings.get("title", ""), "font": {"size": settings.get("font_size", 16) + 2}},
        font={"size": settings.get("font_size", 16)},
        legend_title_text=settings.get("legend_title", ""),
        width=settings.get("fig_width", 1000),
        height=settings.get("fig_height", 560),
        paper_bgcolor=settings.get("background", preset.get("bg", "white")),
        plot_bgcolor=settings.get("background", preset.get("bg", "white")),
        margin=dict(l=40, r=40, t=70, b=50),
    )
    if settings.get("subtitle"):
        fig.add_annotation(text=settings["subtitle"], x=0, y=1.09, xref="paper", yref="paper", showarrow=False, align="left", font={"size": max(10, settings.get("font_size", 16)-2)})
    fig.update_xaxes(title_text=settings.get("x_label"), tickangle=settings.get("label_angle", 0), showgrid=settings.get("show_grid", True))
    fig.update_yaxes(title_text=settings.get("y_label"), showgrid=settings.get("show_grid", True), tickformat=f'.{settings.get("decimals", 1)}f')
    palette = available_palettes().get(settings.get("palette"), px.colors.qualitative.Plotly)
    for i, tr in enumerate(fig.data):
        if hasattr(tr, "line"):
            try:
                tr.line.width = settings.get("line_thickness", 2.5)
                if hasattr(tr.line, "color"):
                    tr.line.color = palette[i % len(palette)]
            except Exception:
                pass
        if hasattr(tr, "marker"):
            try:
                tr.marker.size = settings.get("point_size", 8)
                tr.marker.color = palette[i % len(palette)]
            except Exception:
                pass
    if settings.get("annotate_peak") and source_df is not None and selected_vars:
        first_var = selected_vars[0]
        try:
            s = pd.to_numeric(source_df[first_var], errors="coerce")
            idx = s.idxmax()
            xcol = source_df.columns[0]
            fig.add_annotation(x=source_df.loc[idx, xcol], y=s.loc[idx], text="Peak", showarrow=True, arrowhead=2)
        except Exception:
            pass
    return fig


def figure_to_bytes(fig, fmt: str = "png", width: int = 1400, height: int = 800, scale: int = 2):
    if fig is None:
        return None
    try:
        return fig.to_image(format=fmt, width=width, height=height, scale=scale)
    except Exception:
        return None


def dataframe_to_excel_bytes(sheets: dict[str, pd.DataFrame]):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            (frame if frame is not None else pd.DataFrame()).to_excel(writer, sheet_name=name[:31], index=False)
    bio.seek(0)
    return bio.read()


def build_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns,
        "missing_n": [int(df[c].isna().sum()) for c in df.columns],
        "missing_pct": [round(float(df[c].isna().mean()*100), 2) for c in df.columns],
        "dtype": [str(df[c].dtype) for c in df.columns],
    }).sort_values(["missing_pct", "missing_n"], ascending=False)


def fit_selected_model(df: pd.DataFrame, outcome: str, predictors: list[str], model_name: str, group_var: str | None = None):
    if sm is None:
        return None, None, "statsmodels is not available. Add statsmodels to requirements to enable regression models."
    model_df = df[[outcome] + predictors + ([group_var] if group_var and group_var != "None" else [])].copy()
    model_df = model_df.dropna().copy()
    if model_df.empty:
        return None, None, "No complete rows remain after filtering missing values for the selected model variables."
    X = model_df[predictors].apply(pd.to_numeric, errors="coerce")
    keep = X.notna().all(axis=1) & pd.to_numeric(model_df[outcome], errors="coerce").notna()
    model_df = model_df.loc[keep].copy()
    X = X.loc[keep]
    y = pd.to_numeric(model_df[outcome], errors="coerce")
    if model_df.empty:
        return None, None, "No usable numeric rows remained for model fitting."
    Xc = sm.add_constant(X, has_constant='add')
    result = None
    note = None
    try:
        if model_name == "Linear regression":
            result = sm.OLS(y, Xc).fit()
        elif model_name == "Multiple linear regression":
            result = sm.OLS(y, Xc).fit()
        elif model_name == "Logistic regression":
            y_bin = y.astype(float)
            uniq = sorted(set(y_bin.dropna().unique().tolist()))
            if not set(uniq).issubset({0.0, 1.0}):
                med = float(y_bin.median())
                y_bin = (y_bin > med).astype(int)
                note = f"Outcome was converted to a binary variable using the median ({med:.3f}) because it was not already 0/1."
            result = sm.Logit(y_bin, Xc).fit(disp=False)
        elif model_name == "Poisson regression":
            result = sm.GLM(y, Xc, family=sm.families.Poisson()).fit()
        elif model_name == "Negative binomial regression":
            result = sm.GLM(y, Xc, family=sm.families.NegativeBinomial()).fit()
        elif model_name == "Mixed-effects model":
            if not group_var or group_var == "None":
                return None, None, "Choose a grouping variable for mixed-effects modelling."
            model_df[group_var] = model_df[group_var].astype(str)
            result = sm.MixedLM(endog=y, exog=Xc, groups=model_df[group_var]).fit()
        else:
            return None, None, f"Model {model_name} is not implemented in this release."
        coef = pd.DataFrame({"term": result.params.index if hasattr(result.params, 'index') else range(len(result.params)), "coef": np.asarray(result.params), "p_value": np.asarray(getattr(result, 'pvalues', np.repeat(np.nan, len(result.params))))})
        return result, coef, note
    except Exception as e:
        return None, None, f"Model fitting failed: {e}"


def simple_lag_analysis(df: pd.DataFrame, date_field: str, outcome: str, predictor: str, max_lag: int = 6):
    work = df[[date_field, outcome, predictor]].dropna().copy().sort_values(date_field)
    if work.empty:
        return pd.DataFrame()
    out = []
    y = pd.to_numeric(work[outcome], errors='coerce')
    x = pd.to_numeric(work[predictor], errors='coerce')
    for lag in range(0, max_lag + 1):
        corr = y.corr(x.shift(lag))
        out.append({"lag": lag, "correlation": corr})
    return pd.DataFrame(out)


def anomaly_table(df: pd.DataFrame, date_field: str, variable: str):
    work = df[[date_field, variable]].dropna().copy().sort_values(date_field)
    if work.empty:
        return pd.DataFrame()
    work["month"] = work[date_field].dt.month
    work["baseline"] = work.groupby("month")[variable].transform("mean")
    work["anomaly"] = work[variable] - work["baseline"]
    return work


def render_figure_export_panel(fig, filtered_df: pd.DataFrame, summary_df: pd.DataFrame, page_name: str, plot_type: str, selected_vars: list[str], x_label_default: str = "", y_label_default: str = ""):
    st.markdown("#### Figure styling and export")
    presets = list(get_figure_presets().keys())
    palettes = list(available_palettes().keys())
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        preset = st.selectbox("Journal-style preset", presets, key=f"preset_{page_name}")
        title = st.text_input("Title", value=f"{DISPLAY_PAGE_LABELS.get(page_name, page_name)} analysis", key=f"title_{page_name}")
        subtitle = st.text_input("Subtitle", value="", key=f"subtitle_{page_name}")
        x_label = st.text_input("X-axis label", value=x_label_default or "", key=f"xlabel_{page_name}")
    with c2:
        y_label = st.text_input("Y-axis label", value=y_label_default or "", key=f"ylabel_{page_name}")
        legend_title = st.text_input("Legend title", value="Variables", key=f"legend_{page_name}")
        font_size = st.slider("Font size", 10, 24, 16, key=f"font_{page_name}")
        label_angle = st.slider("Label angle", -90, 90, 0, key=f"angle_{page_name}")
    with c3:
        decimals = st.slider("Decimal places", 0, 4, 1, key=f"dec_{page_name}")
        line_thickness = st.slider("Line thickness", 1.0, 6.0, 2.5, 0.5, key=f"line_{page_name}")
        point_size = st.slider("Point size", 4, 16, 8, key=f"point_{page_name}")
        palette = st.selectbox("Colour palette", palettes, key=f"palette_{page_name}")
    with c4:
        fig_width = st.slider("Figure width", 700, 1800, 1100, 50, key=f"fw_{page_name}")
        fig_height = st.slider("Figure height", 420, 1400, 620, 20, key=f"fh_{page_name}")
        dpi_scale = st.slider("DPI scale", 1, 4, 2, key=f"dpi_{page_name}")
        background = st.selectbox("Background", ["white", "#fbfdff", "#f8fafc"], key=f"bg_{page_name}")
        show_grid = st.checkbox("Show gridlines", value=True, key=f"grid_{page_name}")
        annotate_peak = st.checkbox("Annotate peak", value=False, key=f"peak_{page_name}")

    settings = {"preset": preset, "title": title, "subtitle": subtitle, "x_label": x_label, "y_label": y_label, "legend_title": legend_title, "font_size": font_size, "label_angle": label_angle, "decimals": decimals, "line_thickness": line_thickness, "point_size": point_size, "palette": palette, "fig_width": fig_width, "fig_height": fig_height, "background": background, "show_grid": show_grid, "annotate_peak": annotate_peak}
    styled_fig = apply_figure_customisation(fig, settings, plot_type=plot_type, source_df=filtered_df, selected_vars=selected_vars)

    st.markdown("##### Multi-panel layout")
    panel_mode = st.checkbox("Build a multi-panel export figure", value=False, key=f"mp_toggle_{page_name}")
    export_fig = styled_fig
    if panel_mode:
        layout_choice = st.selectbox("Figure layout", ["1x2", "2x2", "3x2", "3x3", "4x4", "5x5", "Custom rows x columns"], key=f"mp_layout_{page_name}")
        if layout_choice == "Custom rows x columns":
            m1, m2 = st.columns(2)
            with m1:
                rows = st.number_input("Rows", min_value=1, max_value=5, value=2, step=1, key=f"mp_rows_{page_name}")
            with m2:
                cols = st.number_input("Columns", min_value=1, max_value=5, value=2, step=1, key=f"mp_cols_{page_name}")
        else:
            rows, cols = [int(x) for x in layout_choice.split('x')]
        max_panels = int(rows) * int(cols)
        n_panels = st.slider("How many panels to fill", 1, max_panels, min(max_panels, max(1, len(selected_vars))), key=f"mp_n_{page_name}")
        candidate_x = ['None'] + filtered_df.columns.tolist()
        candidate_y = [c for c in numeric_columns(filtered_df) if filtered_df[c].notna().any()]
        panel_specs = []
        st.caption("Add multiple panels below. Each panel can use a different plot type, title, X variable, Y variables, and time aggregation.")
        for i in range(n_panels):
            st.markdown(f"**Panel {i+1}**")
            p1, p2, p3, p4 = st.columns([1.1, 1.0, 1.2, 2.0])
            with p1:
                ptype = st.selectbox("Plot type", ["Line", "Bar", "Scatter", "Box", "Histogram", "Heatmap"], key=f"mp_ptype_{page_name}_{i}")
            with p2:
                freq = st.selectbox("Time aggregation", ["Raw", "Daily", "Weekly", "Monthly", "Yearly"], key=f"mp_freq_{page_name}_{i}")
            with p3:
                xvar = st.selectbox("X variable", candidate_x if candidate_x else ['None'], key=f"mp_x_{page_name}_{i}")
            with p4:
                default_y = candidate_y[i:i+1] if candidate_y else []
                yvars = st.multiselect("Y / variables", candidate_y, default=default_y, key=f"mp_y_{page_name}_{i}")
            ptitle = st.text_input("Panel title", value=f"Panel {i+1}", key=f"mp_title_{page_name}_{i}")
            panel_specs.append({"plot_type": ptype, "x": None if xvar == 'None' else xvar, "yvars": yvars, "title": ptitle, "freq": freq})
        export_fig = build_panel_trace_figure(filtered_df, panel_specs, int(rows), int(cols), title=title)
        export_fig = apply_figure_customisation(export_fig, settings, plot_type='Multi-panel', source_df=filtered_df, selected_vars=selected_vars)

    if export_fig is not None:
        st.plotly_chart(export_fig, use_container_width=True, key=f"styled_plot_{page_name}")
        png_bytes = figure_to_bytes(export_fig, fmt="png", width=fig_width, height=fig_height, scale=dpi_scale)
        svg_bytes = figure_to_bytes(export_fig, fmt="svg", width=fig_width, height=fig_height, scale=dpi_scale)
        pdf_bytes = figure_to_bytes(export_fig, fmt="pdf", width=fig_width, height=fig_height, scale=dpi_scale)
        jpg_bytes = None
        tiff_bytes = None
        html_bytes = export_fig.to_html(include_plotlyjs='cdn').encode('utf-8')
        if png_bytes is not None and Image is not None:
            try:
                img = Image.open(BytesIO(png_bytes)).convert('RGB')
                jpg_buffer = BytesIO()
                img.save(jpg_buffer, format='JPEG', quality=95)
                jpg_buffer.seek(0)
                jpg_bytes = jpg_buffer.read()
                tiff_buffer = BytesIO()
                img.save(tiff_buffer, format='TIFF')
                tiff_buffer.seek(0)
                tiff_bytes = tiff_buffer.read()
            except Exception:
                jpg_bytes = None
                tiff_bytes = None
        excel_bytes = dataframe_to_excel_bytes({"filtered_data": filtered_df, "summary": summary_df.reset_index() if summary_df is not None else pd.DataFrame()})
        st.markdown("##### Download outputs")
        row1 = st.columns(3)
        row2 = st.columns(3)
        row3 = st.columns(2)
        with row1[0]:
            if png_bytes: st.download_button("Download PNG", png_bytes, file_name=f"{slugify(page_name)}_figure.png", mime="image/png", use_container_width=True)
        with row1[1]:
            if jpg_bytes: st.download_button("Download JPG", jpg_bytes, file_name=f"{slugify(page_name)}_figure.jpg", mime="image/jpeg", use_container_width=True)
        with row1[2]:
            if svg_bytes: st.download_button("Download SVG", svg_bytes, file_name=f"{slugify(page_name)}_figure.svg", mime="image/svg+xml", use_container_width=True)
        with row2[0]:
            if pdf_bytes: st.download_button("Download PDF", pdf_bytes, file_name=f"{slugify(page_name)}_figure.pdf", mime="application/pdf", use_container_width=True)
        with row2[1]:
            if tiff_bytes is not None: st.download_button("Download TIFF", tiff_bytes, file_name=f"{slugify(page_name)}_figure.tiff", mime="image/tiff", use_container_width=True)
        with row2[2]:
            st.download_button("Download editable HTML", html_bytes, file_name=f"{slugify(page_name)}_figure.html", mime="text/html", use_container_width=True)
        with row3[0]:
            st.download_button("Download CSV data", filtered_df.to_csv(index=False).encode("utf-8"), file_name=f"{slugify(page_name)}_filtered.csv", mime="text/csv", use_container_width=True)
        with row3[1]:
            st.download_button("Download Excel workbook", excel_bytes, file_name=f"{slugify(page_name)}_analysis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.caption("Figure export supports PNG, JPG, SVG, PDF, CSV, Excel, TIFF where Pillow is available, and editable HTML.")
    else:
        st.info("Figure export preview is unavailable for the current plot type.")


def prepare_health_df_for_analysis(health_df: pd.DataFrame | None) -> pd.DataFrame:
    if health_df is None or health_df.empty:
        return pd.DataFrame()
    work = health_df.loc[:, ~health_df.columns.duplicated()].copy()
    for c in work.columns:
        if c in {"Value", "SurveyYear"} or any(k in c.lower() for k in ["value", "year", "score", "rate", "percent", "coverage"]):
            try:
                work[c] = pd.to_numeric(work[c], errors="ignore")
            except Exception:
                pass
    return work


def normalise_join_key(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def derive_temporal_key(df: pd.DataFrame, field: str | None, mode: str) -> pd.Series | None:
    if field is None or field not in df.columns or mode == "No temporal join":
        return None
    s = df[field]
    if mode == "Year only":
        if pd.api.types.is_datetime64_any_dtype(s):
            return s.dt.year.astype("Int64").astype(str)
        coerced = pd.to_numeric(s, errors="coerce")
        if coerced.notna().any():
            return coerced.astype("Int64").astype(str)
        return s.astype(str).str.extract(r"(\d{4})", expand=False).fillna("")
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.strftime("%Y-%m-%d")
    return s.astype(str).str.strip().str.upper()


def build_climate_health_model_df(
    climate_df: pd.DataFrame,
    health_df: pd.DataFrame,
    climate_key: str,
    health_key: str,
    climate_predictors: list[str],
    health_outcome: str,
    temporal_mode: str = "No temporal join",
    climate_time_field: str | None = None,
    health_time_field: str | None = None,
    health_covariates: list[str] | None = None,
):
    health_covariates = health_covariates or []
    notes = []
    if climate_key not in climate_df.columns or health_key not in health_df.columns:
        return pd.DataFrame(), ["The selected join fields were not found in one of the datasets."]

    climate_keep = [climate_key] + climate_predictors + ([climate_time_field] if climate_time_field else [])
    climate_keep = [c for c in climate_keep if c in climate_df.columns]
    health_keep = [health_key, health_outcome] + health_covariates + ([health_time_field] if health_time_field else [])
    health_keep = [c for c in health_keep if c in health_df.columns]

    cdf = climate_df[climate_keep].copy()
    hdf = health_df[health_keep].copy()

    cdf["join_key"] = normalise_join_key(cdf[climate_key])
    hdf["join_key"] = normalise_join_key(hdf[health_key])

    if temporal_mode != "No temporal join":
        cdf["time_key"] = derive_temporal_key(cdf, climate_time_field, temporal_mode)
        hdf["time_key"] = derive_temporal_key(hdf, health_time_field, temporal_mode)
        cdf = cdf[cdf["time_key"].notna() & (cdf["time_key"] != "")]
        hdf = hdf[hdf["time_key"].notna() & (hdf["time_key"] != "")]
        group_cols = ["join_key", "time_key"]
        notes.append(f"Temporal join mode: {temporal_mode}.")
    else:
        group_cols = ["join_key"]

    climate_numeric = [c for c in climate_predictors if c in cdf.columns]
    health_numeric = [c for c in [health_outcome] + list(health_covariates) if c in hdf.columns]

    for c in climate_numeric:
        cdf[c] = pd.to_numeric(cdf[c], errors="coerce")
    for c in health_numeric:
        hdf[c] = pd.to_numeric(hdf[c], errors="coerce")

    c_grouped = cdf[group_cols + climate_numeric].dropna(subset=climate_numeric, how="all").groupby(group_cols, as_index=False).mean(numeric_only=True)
    h_grouped = hdf[group_cols + health_numeric].dropna(subset=[health_outcome]).groupby(group_cols, as_index=False).mean(numeric_only=True)

    joined = c_grouped.merge(h_grouped, on=group_cols, how="inner")
    if joined.empty:
        return pd.DataFrame(), notes + ["No rows matched between the selected climate and health fields."]

    joined = joined.rename(columns={health_outcome: "__health_outcome__"})
    for cov in health_covariates:
        if cov in joined.columns:
            joined = joined.rename(columns={cov: f"health_{cov}"})
    notes.append(f"Joined {len(joined):,} rows across climate and health fields.")
    return joined, notes


def render_statistical_analysis_tabs(d: pd.DataFrame, aggregated: pd.DataFrame, page_name: str, area_field: str | None, date_field: str | None, selected_vars: list[str], group_col: str, plot_type: str, fig):
    st.markdown("#### Statistical analysis")
    tabs = st.tabs(["Summary", "Correlation", "Regression", "Time Series", "Spatial", "Advanced", "AI-Guided Analysis", "Downloads"])

    health_df_session = prepare_health_df_for_analysis(st.session_state.get("health_df"))

    with tabs[0]:
        st.dataframe(d[selected_vars].describe().T, use_container_width=True)
        st.markdown("##### Grouped summaries")
        if group_col != "None":
            frames = []
            for col in selected_vars:
                g = d.groupby(group_col)[col].agg(["count", "mean", "median", "min", "max", "std"]).reset_index()
                g.insert(1, "variable", col)
                frames.append(g)
            st.dataframe(pd.concat(frames, ignore_index=True), use_container_width=True)
        else:
            st.info("Choose a group / category field in the Explore controls to enable grouped summaries.")
        st.markdown("##### Missing-data summary")
        st.dataframe(build_missing_summary(d), use_container_width=True)

        if not health_df_session.empty:
            st.markdown("##### Climate–Health linkage available")
            st.markdown(
                '<div class="note-box"><strong>Health data are active in this session.</strong> '
                'You can now use the Correlation and Regression tabs to link climate predictors from this workflow '
                'with DHS or other health outcome variables loaded on the Health page.</div>',
                unsafe_allow_html=True,
            )

    with tabs[1]:
        if len(selected_vars) >= 2:
            pearson = d[selected_vars].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
            spearman = d[selected_vars].apply(pd.to_numeric, errors="coerce").corr(method="spearman")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Pearson correlation**")
                st.plotly_chart(px.imshow(pearson, text_auto=True, aspect="auto"), use_container_width=True)
            with c2:
                st.markdown("**Spearman correlation**")
                st.plotly_chart(px.imshow(spearman, text_auto=True, aspect="auto"), use_container_width=True)
        else:
            st.info("Choose at least two numeric variables to run correlation analysis.")

        st.markdown("##### Climate–Health correlation (optional)")
        if health_df_session.empty:
            st.info("Load a health dataset on the Health page to enable cross-domain climate–health correlation here.")
            if (SAMPLE_DIR / "demo_brazil_anc_dhs.csv").exists():
                if st.button("Load built-in DHS-style demo health data", key=f"corr_load_demo_health_{page_name}"):
                    st.session_state["health_df"] = load_demo_dataframe("demo_brazil_anc_dhs.csv")
                    st.rerun()
        else:
            health_numeric = get_health_outcome_candidates(health_df_session)
            climate_numeric = [c for c in numeric_columns(d) if d[c].notna().any()]
            if climate_numeric and health_numeric:
                hc1, hc2, hc3, hc4 = st.columns(4)
                with hc1:
                    climate_key = st.selectbox("Climate join field", [c for c in d.columns], index=d.columns.tolist().index(area_field) if area_field in d.columns else 0, key=f"corr_ck_{page_name}")
                with hc2:
                    default_hk = health_df_session.columns.tolist().index("RegionName") if "RegionName" in health_df_session.columns else (health_df_session.columns.tolist().index("CharacteristicLabel") if "CharacteristicLabel" in health_df_session.columns else 0)
                    health_key = st.selectbox("Health join field", health_df_session.columns.tolist(), index=default_hk, key=f"corr_hk_{page_name}")
                with hc3:
                    climate_vars = st.multiselect("Climate variables", climate_numeric, default=climate_numeric[:min(3, len(climate_numeric))], key=f"corr_cvars_{page_name}")
                with hc4:
                    health_vars = st.multiselect("Health variables", health_numeric, default=health_numeric[:min(2, len(health_numeric))], key=f"corr_hvars_{page_name}")

                tm1, tm2, tm3 = st.columns(3)
                with tm1:
                    temporal_mode = st.selectbox("Temporal join", ["No temporal join", "Year only", "Exact field match"], key=f"corr_tmode_{page_name}")
                with tm2:
                    climate_time = st.selectbox("Climate time field", ["None"] + [c for c in d.columns if c == date_field or "year" in c.lower() or "date" in c.lower()], key=f"corr_ctime_{page_name}")
                with tm3:
                    health_time = st.selectbox("Health time field", ["None"] + [c for c in health_df_session.columns if c == "SurveyYear" or "year" in c.lower() or "date" in c.lower()], key=f"corr_htime_{page_name}")

                if climate_vars and health_vars:
                    joined, notes = build_climate_health_model_df(
                        d, health_df_session, climate_key, health_key, climate_vars, health_vars[0],
                        temporal_mode=temporal_mode,
                        climate_time_field=None if climate_time == "None" else climate_time,
                        health_time_field=None if health_time == "None" else health_time,
                        health_covariates=health_vars[1:],
                    )
                    for note in notes:
                        st.caption(note)
                    if not joined.empty:
                        corr_cols = [c for c in climate_vars + ["__health_outcome__"] + [f"health_{c}" for c in health_vars[1:]] if c in joined.columns]
                        if len(corr_cols) >= 2:
                            pear = joined[corr_cols].corr(method="pearson")
                            spear = joined[corr_cols].corr(method="spearman")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.plotly_chart(px.imshow(pear, text_auto=True, aspect="auto", title="Climate–Health Pearson correlation"), use_container_width=True)
                            with c2:
                                st.plotly_chart(px.imshow(spear, text_auto=True, aspect="auto", title="Climate–Health Spearman correlation"), use_container_width=True)
                            st.dataframe(joined.head(200), use_container_width=True)

    with tabs[2]:
        st.markdown("##### Model configuration")
        reg_scope = st.radio(
            "Analysis scope",
            ["Current workflow variables only", "Link climate predictors with health outcomes"],
            horizontal=True,
            key=f"reg_scope_{page_name}",
        )

        if reg_scope == "Current workflow variables only":
            model_candidates = [c for c in numeric_columns(d) if d[c].notna().any()]
            if len(model_candidates) < 2:
                st.info("At least two numeric variables are needed for regression analysis.")
            else:
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    outcome = st.selectbox("Outcome variable", model_candidates, key=f"reg_out_{page_name}")
                with r2:
                    predictors = st.multiselect("Predictor variables", [c for c in model_candidates if c != outcome], default=[c for c in model_candidates if c != outcome][:2], key=f"reg_pred_{page_name}")
                with r3:
                    model_name = st.selectbox("Model", ["Linear regression", "Multiple linear regression", "Logistic regression", "Poisson regression", "Negative binomial regression", "Mixed-effects model"], key=f"reg_model_{page_name}")
                with r4:
                    possible_groups = ["None"] + [c for c in categorical_columns(d) if c != area_field]
                    group_var = st.selectbox("Group variable", possible_groups, key=f"reg_group_{page_name}")
                if predictors:
                    result, coef, note = fit_selected_model(d, outcome, predictors, model_name, group_var if group_var != "None" else None)
                    if note:
                        st.caption(note)
                    if coef is not None:
                        st.dataframe(coef, use_container_width=True)
                    if result is not None:
                        try:
                            st.text(result.summary().as_text())
                        except Exception:
                            st.write(result.summary())
                else:
                    st.info("Choose at least one predictor variable.")
        else:
            st.markdown(
                '<div class="note-box"><strong>Climate–Health linked modelling:</strong> choose climate variables from the current workflow as predictors or explanatory variables, '
                'then choose a DHS or health variable as the response or outcome. Load a health dataset on the Health page first, or use the built-in demo below.</div>',
                unsafe_allow_html=True,
            )
            if health_df_session.empty:
                st.warning("No health dataset is active in this session yet.")
                if (SAMPLE_DIR / "demo_brazil_anc_dhs.csv").exists():
                    if st.button("Load built-in DHS-style demo health data for modelling", key=f"reg_load_demo_health_{page_name}"):
                        st.session_state["health_df"] = load_demo_dataframe("demo_brazil_anc_dhs.csv")
                        st.rerun()
            else:
                climate_numeric = [c for c in numeric_columns(d) if d[c].notna().any()]
                health_numeric = [c for c in get_health_outcome_candidates(health_df_session) if health_df_session[c].notna().any()]
                if not climate_numeric or not health_numeric:
                    st.info("Usable numeric climate and health fields are both needed for linked modelling.")
                else:
                    r1, r2, r3, r4 = st.columns(4)
                    with r1:
                        climate_key = st.selectbox("Climate join field", d.columns.tolist(), index=d.columns.tolist().index(area_field) if area_field in d.columns else 0, key=f"chm_ck_{page_name}")
                    with r2:
                        default_hk = health_df_session.columns.tolist().index("RegionName") if "RegionName" in health_df_session.columns else (health_df_session.columns.tolist().index("CharacteristicLabel") if "CharacteristicLabel" in health_df_session.columns else 0)
                        health_key = st.selectbox("Health join field", health_df_session.columns.tolist(), index=default_hk, key=f"chm_hk_{page_name}")
                    with r3:
                        climate_predictors = st.multiselect("Predictor / explanatory variables (climate or hazard)", climate_numeric, default=climate_numeric[:min(3, len(climate_numeric))], key=f"chm_pred_{page_name}")
                    with r4:
                        health_outcome = st.selectbox("Outcome / response variable (health)", health_numeric, index=health_numeric.index("Value") if "Value" in health_numeric else 0, key=f"chm_out_{page_name}")

                    rr1, rr2, rr3, rr4 = st.columns(4)
                    with rr1:
                        health_covs = st.multiselect("Optional health covariates", get_health_covariate_candidates(health_df_session, health_outcome), default=[], key=f"chm_hcov_{page_name}")
                    with rr2:
                        model_name = st.selectbox("Model", ["Linear regression", "Multiple linear regression", "Logistic regression", "Poisson regression", "Negative binomial regression", "Mixed-effects model"], key=f"chm_model_{page_name}")
                    with rr3:
                        temporal_mode = st.selectbox("Temporal join mode", ["No temporal join", "Year only", "Exact field match"], key=f"chm_tmode_{page_name}")
                    with rr4:
                        group_choices = ["None"]
                        group_var_placeholder = st.selectbox("Group variable (after join)", group_choices, key=f"chm_group_placeholder_{page_name}")

                    rt1, rt2 = st.columns(2)
                    with rt1:
                        climate_time = st.selectbox("Climate time field", ["None"] + [c for c in d.columns if c == date_field or "year" in c.lower() or "date" in c.lower()], key=f"chm_ctime_{page_name}")
                    with rt2:
                        health_time = st.selectbox("Health time field", ["None"] + [c for c in health_df_session.columns if c == "SurveyYear" or "year" in c.lower() or "date" in c.lower()], key=f"chm_htime_{page_name}")

                    if climate_predictors:
                        joined, notes = build_climate_health_model_df(
                            d,
                            health_df_session,
                            climate_key,
                            health_key,
                            climate_predictors,
                            health_outcome,
                            temporal_mode=temporal_mode,
                            climate_time_field=None if climate_time == "None" else climate_time,
                            health_time_field=None if health_time == "None" else health_time,
                            health_covariates=health_covs,
                        )
                        for note in notes:
                            st.caption(note)

                        if joined.empty:
                            st.warning("No matched rows were available for the selected climate and health fields. Try another join field, use Year only, or load a more compatible health dataset.")
                        else:
                            st.success(f"Linked climate–health dataset prepared with {len(joined):,} rows.")
                            display_joined = joined.copy()
                            st.dataframe(display_joined.head(200), use_container_width=True)

                            model_predictors = list(climate_predictors) + [f"health_{c}" for c in health_covs if f"health_{c}" in joined.columns]
                            group_choices = ["None"] + [c for c in categorical_columns(joined) if c != "__health_outcome__"]
                            group_var = st.selectbox("Group variable (after join)", group_choices, key=f"chm_group_{page_name}")

                            result, coef, note = fit_selected_model(joined, "__health_outcome__", model_predictors, model_name, group_var if group_var != "None" else None)
                            if note:
                                st.caption(note)
                            if coef is not None:
                                pretty = coef.copy()
                                pretty["term"] = pretty["term"].replace({"__health_outcome__": health_outcome})
                                st.dataframe(pretty, use_container_width=True)
                            if result is not None:
                                try:
                                    st.text(result.summary().as_text())
                                except Exception:
                                    st.write(result.summary())

                            first_pred = climate_predictors[0]
                            plot_df = joined[[first_pred, "__health_outcome__"]].dropna().copy()
                            if not plot_df.empty:
                                plot_df = plot_df.rename(columns={"__health_outcome__": health_outcome})
                                st.plotly_chart(
                                    px.scatter(
                                        plot_df,
                                        x=first_pred,
                                        y=health_outcome,
                                        trendline="ols" if model_name in ["Linear regression", "Multiple linear regression"] else None,
                                        title="Climate predictor vs health outcome",
                                    ),
                                    use_container_width=True,
                                )
                    else:
                        st.info("Choose at least one climate predictor variable.")

    with tabs[3]:
        if date_field and date_field in d.columns and len(selected_vars) >= 1:
            ts_var = st.selectbox("Time-series variable", selected_vars, key=f"ts_var_{page_name}")
            ts_df = d[[date_field, ts_var]].dropna().sort_values(date_field).copy()
            st.plotly_chart(px.line(ts_df, x=date_field, y=ts_var, title="Trend plot"), use_container_width=True)
            if len(selected_vars) >= 2:
                pred_var = st.selectbox("Lag predictor", [v for v in selected_vars if v != ts_var], key=f"lag_pred_{page_name}")
                max_lag = st.slider("Maximum lag", 1, 12, 6, key=f"max_lag_{page_name}")
                lag_df = simple_lag_analysis(d, date_field, ts_var, pred_var, max_lag=max_lag)
                if not lag_df.empty:
                    st.plotly_chart(px.line(lag_df, x="lag", y="correlation", markers=True, title="Lag analysis"), use_container_width=True)
            anomaly_df = anomaly_table(d, date_field, ts_var)
            if not anomaly_df.empty:
                st.plotly_chart(px.line(anomaly_df, x=date_field, y="anomaly", title="Anomaly analysis"), use_container_width=True)
            st.markdown("##### Interrupted time-series (partial)")
            intervention_date = st.date_input("Intervention / threshold date", value=ts_df[date_field].median().date(), key=f"its_date_{page_name}")
            its_df = ts_df.copy()
            its_df["time_index"] = np.arange(len(its_df))
            its_df["post"] = (its_df[date_field].dt.date >= intervention_date).astype(int)
            its_df["time_after"] = its_df["time_index"] * its_df["post"]
            if sm is not None and len(its_df) > 8:
                its_model = sm.OLS(pd.to_numeric(its_df[ts_var], errors='coerce'), sm.add_constant(its_df[["time_index", "post", "time_after"]], has_constant='add')).fit()
                st.text(its_model.summary().as_text())
            else:
                st.info("Interrupted time-series output is shown when enough dated observations are available and statsmodels is installed.")
        else:
            st.info("A date field and at least one selected variable are needed for time-series analysis.")
    with tabs[4]:
        render_maps_for_explorer(page_name, key_suffix="stats_spatial")
    with tabs[5]:
        adv_numeric = [c for c in numeric_columns(d) if c not in {date_field}]
        st.markdown("##### PCA")
        if PCA is not None and len(adv_numeric) >= 2:
            pca_vars = st.multiselect("Variables for PCA", adv_numeric, default=adv_numeric[:min(5, len(adv_numeric))], key=f"pca_vars_{page_name}")
            if len(pca_vars) >= 2:
                pca_df = d[pca_vars].dropna().copy()
                if len(pca_df) >= 3:
                    pca = PCA(n_components=min(3, len(pca_vars)))
                    pcs = pca.fit_transform(pca_df)
                    ev = pd.DataFrame({"component": [f"PC{i+1}" for i in range(pca.n_components_)], "explained_variance_ratio": pca.explained_variance_ratio_})
                    st.dataframe(ev, use_container_width=True)
                    if pcs.shape[1] >= 2:
                        pc_df = pd.DataFrame({"PC1": pcs[:,0], "PC2": pcs[:,1]})
                        st.plotly_chart(px.scatter(pc_df, x="PC1", y="PC2", title="PCA scores"), use_container_width=True)
        else:
            st.info("PCA requires scikit-learn and at least two numeric variables.")
        st.markdown("##### Random forest / boosted trees")
        if len(adv_numeric) >= 2 and RandomForestRegressor is not None:
            outcome_adv = st.selectbox("Outcome for advanced models", adv_numeric, key=f"adv_out_{page_name}")
            preds_adv = st.multiselect("Predictors for advanced models", [c for c in adv_numeric if c != outcome_adv], default=[c for c in adv_numeric if c != outcome_adv][:3], key=f"adv_pred_{page_name}")
            if preds_adv:
                model_df = d[[outcome_adv] + preds_adv].dropna().copy()
                X = model_df[preds_adv]
                y = pd.to_numeric(model_df[outcome_adv], errors='coerce')
                if len(model_df) >= 10:
                    rf = RandomForestRegressor(n_estimators=200, random_state=42)
                    rf.fit(X, y)
                    imp = pd.DataFrame({"variable": preds_adv, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
                    st.dataframe(imp, use_container_width=True)
                    st.plotly_chart(px.bar(imp, x="importance", y="variable", orientation="h", title="Random forest importance"), use_container_width=True)
                    gb = GradientBoostingRegressor(random_state=42)
                    gb.fit(X, y)
                    imp2 = pd.DataFrame({"variable": preds_adv, "importance": gb.feature_importances_}).sort_values("importance", ascending=False)
                    st.plotly_chart(px.bar(imp2, x="importance", y="variable", orientation="h", title="Boosted-tree importance"), use_container_width=True)
                else:
                    st.info("Advanced tree-based models need more rows to be informative.")
        st.markdown("##### GAM / hotspot / DLNM-style workflows")
        st.info("These advanced workflows are included as guided placeholders in this release. Use the AI-Guided Analysis tab to design a GAM-style, hotspot, or lagged climate-health workflow, then refine it with backend or notebook support if needed.")
    with tabs[6]:
        ai_cols = list(d.columns)
        if not health_df_session.empty:
            ai_cols = ai_cols + [c for c in health_df_session.columns if c not in ai_cols]
        ai_date = date_field or ("SurveyYear" if not health_df_session.empty and "SurveyYear" in health_df_session.columns else None)
        render_ai_box(page_name, plot_type, selected_vars, "Exploratory", False, [], columns=ai_cols, date_field=ai_date)
    with tabs[7]:
        render_figure_export_panel(fig, d, d[selected_vars].describe().T if selected_vars else pd.DataFrame(), page_name, plot_type, selected_vars, x_label_default=str(date_field or "Period"), y_label_default=", ".join(selected_vars[:2]))



def get_figure_presets():
    return {
        "General Medical / Public Health": {"template": "simple_white", "font_size": 16, "bg": "white", "grid": True},
        "Environmental Epidemiology / Environmental Health": {"template": "simple_white", "font_size": 15, "bg": "white", "grid": True},
        "Climate and Planetary Health": {"template": "simple_white", "font_size": 16, "bg": "#fbfdff", "grid": True},
        "Biometeorology / Climate Impacts": {"template": "simple_white", "font_size": 15, "bg": "white", "grid": True},
    }


def available_palettes():
    return {
        "Plotly": px.colors.qualitative.Plotly,
        "Safe": px.colors.qualitative.Safe,
        "Dark24": px.colors.qualitative.Dark24,
        "Set2": px.colors.qualitative.Set2,
        "Pastel": px.colors.qualitative.Pastel,
    }


def apply_figure_customisation(fig, settings: dict, plot_type: str | None = None, source_df: pd.DataFrame | None = None, selected_vars: list[str] | None = None):
    if fig is None:
        return None
    presets = get_figure_presets()
    preset = presets.get(settings.get("preset"), presets["General Medical / Public Health"])
    fig.update_layout(template=preset.get("template", "simple_white"), title={"text": settings.get("title", ""), "font": {"size": settings.get("font_size", 16)+2}}, font={"size": settings.get("font_size", 16)}, legend_title_text=settings.get("legend_title", ""), width=settings.get("fig_width", 1000), height=settings.get("fig_height", 560), paper_bgcolor=settings.get("background", preset.get("bg", "white")), plot_bgcolor=settings.get("background", preset.get("bg", "white")), margin=dict(l=40, r=40, t=70, b=50))
    if settings.get("subtitle"):
        fig.add_annotation(text=settings["subtitle"], x=0, y=1.09, xref="paper", yref="paper", showarrow=False, align="left", font={"size": max(10, settings.get("font_size", 16)-2)})
    fig.update_xaxes(title_text=settings.get("x_label"), tickangle=settings.get("label_angle", 0), showgrid=settings.get("show_grid", True))
    fig.update_yaxes(title_text=settings.get("y_label"), showgrid=settings.get("show_grid", True), tickformat=f'.{settings.get("decimals", 1)}f')
    palette = available_palettes().get(settings.get("palette"), px.colors.qualitative.Plotly)
    for i, tr in enumerate(fig.data):
        try:
            if hasattr(tr, "line") and tr.line is not None:
                tr.line.width = settings.get("line_thickness", 2.5)
                tr.line.color = palette[i % len(palette)]
        except Exception:
            pass
        try:
            if hasattr(tr, "marker") and tr.marker is not None:
                tr.marker.size = settings.get("point_size", 8)
                tr.marker.color = palette[i % len(palette)]
        except Exception:
            pass
    if settings.get("annotate_peak") and source_df is not None and selected_vars:
        first_var = selected_vars[0]
        try:
            s = pd.to_numeric(source_df[first_var], errors="coerce")
            idx = s.idxmax()
            xcol = source_df.columns[0]
            fig.add_annotation(x=source_df.loc[idx, xcol], y=s.loc[idx], text="Peak", showarrow=True, arrowhead=2)
        except Exception:
            pass
    return fig


def figure_to_bytes(fig, fmt: str = "png", width: int = 1400, height: int = 800, scale: int = 2):
    if fig is None:
        return None
    try:
        return fig.to_image(format=fmt, width=width, height=height, scale=scale)
    except Exception:
        return None


def dataframe_to_excel_bytes(sheets: dict):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            (frame if frame is not None else pd.DataFrame()).to_excel(writer, sheet_name=name[:31], index=False)
    bio.seek(0)
    return bio.read()


def build_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns,
        "missing_n": [int(df[c].isna().sum()) for c in df.columns],
        "missing_pct": [round(float(df[c].isna().mean()*100), 2) for c in df.columns],
        "dtype": [str(df[c].dtype) for c in df.columns],
    }).sort_values(["missing_pct", "missing_n"], ascending=False)


def fit_selected_model(df: pd.DataFrame, outcome: str, predictors: list[str], model_name: str, group_var: str | None = None):
    if sm is None:
        return None, None, "statsmodels is not available. Add statsmodels to requirements to enable regression models."
    model_df = df[[outcome] + predictors + ([group_var] if group_var and group_var != "None" else [])].copy().dropna()
    if model_df.empty:
        return None, None, "No complete rows remain after filtering missing values for the selected model variables."
    X = model_df[predictors].apply(pd.to_numeric, errors="coerce")
    keep = X.notna().all(axis=1) & pd.to_numeric(model_df[outcome], errors="coerce").notna()
    model_df = model_df.loc[keep].copy()
    X = X.loc[keep]
    y = pd.to_numeric(model_df[outcome], errors="coerce")
    if model_df.empty:
        return None, None, "No usable numeric rows remained for model fitting."
    Xc = sm.add_constant(X, has_constant='add')
    result = None
    note = None
    try:
        if model_name in ["Linear regression", "Multiple linear regression"]:
            result = sm.OLS(y, Xc).fit()
        elif model_name == "Logistic regression":
            y_bin = y.astype(float)
            uniq = sorted(set(y_bin.dropna().unique().tolist()))
            if not set(uniq).issubset({0.0, 1.0}):
                med = float(y_bin.median())
                y_bin = (y_bin > med).astype(int)
                note = f"Outcome was converted to a binary variable using the median ({med:.3f}) because it was not already 0/1."
            result = sm.Logit(y_bin, Xc).fit(disp=False)
        elif model_name == "Poisson regression":
            result = sm.GLM(y, Xc, family=sm.families.Poisson()).fit()
        elif model_name == "Negative binomial regression":
            result = sm.GLM(y, Xc, family=sm.families.NegativeBinomial()).fit()
        elif model_name == "Mixed-effects model":
            if not group_var or group_var == "None":
                return None, None, "Choose a grouping variable for mixed-effects modelling."
            model_df[group_var] = model_df[group_var].astype(str)
            result = sm.MixedLM(endog=y, exog=Xc, groups=model_df[group_var]).fit()
        else:
            return None, None, f"Model {model_name} is not implemented in this release."
        coef = pd.DataFrame({"term": result.params.index if hasattr(result.params, 'index') else range(len(result.params)), "coef": np.asarray(result.params), "p_value": np.asarray(getattr(result, 'pvalues', np.repeat(np.nan, len(result.params))))})
        return result, coef, note
    except Exception as e:
        return None, None, f"Model fitting failed: {e}"


def simple_lag_analysis(df: pd.DataFrame, date_field: str, outcome: str, predictor: str, max_lag: int = 6):
    work = df[[date_field, outcome, predictor]].dropna().copy().sort_values(date_field)
    if work.empty:
        return pd.DataFrame()
    out = []
    y = pd.to_numeric(work[outcome], errors='coerce')
    x = pd.to_numeric(work[predictor], errors='coerce')
    for lag in range(0, max_lag + 1):
        corr = y.corr(x.shift(lag))
        out.append({"lag": lag, "correlation": corr})
    return pd.DataFrame(out)


def anomaly_table(df: pd.DataFrame, date_field: str, variable: str):
    work = df[[date_field, variable]].dropna().copy().sort_values(date_field)
    if work.empty:
        return pd.DataFrame()
    work["month"] = work[date_field].dt.month
    work["baseline"] = work.groupby("month")[variable].transform("mean")
    work["anomaly"] = work[variable] - work["baseline"]
    return work




def prepare_health_df_for_analysis(health_df: pd.DataFrame | None) -> pd.DataFrame:
    if health_df is None or health_df.empty:
        return pd.DataFrame()
    work = health_df.loc[:, ~health_df.columns.duplicated()].copy()
    for c in work.columns:
        if c in {"Value", "SurveyYear"} or any(k in c.lower() for k in ["value", "year", "score", "rate", "percent", "coverage"]):
            try:
                work[c] = pd.to_numeric(work[c], errors="ignore")
            except Exception:
                pass
    return work


def normalise_join_key(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def derive_temporal_key(df: pd.DataFrame, field: str | None, mode: str) -> pd.Series | None:
    if field is None or field not in df.columns or mode == "No temporal join":
        return None
    s = df[field]
    if mode == "Year only":
        if pd.api.types.is_datetime64_any_dtype(s):
            return s.dt.year.astype("Int64").astype(str)
        coerced = pd.to_numeric(s, errors="coerce")
        if coerced.notna().any():
            return coerced.astype("Int64").astype(str)
        return s.astype(str).str.extract(r"(\d{4})", expand=False).fillna("")
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.strftime("%Y-%m-%d")
    return s.astype(str).str.strip().str.upper()


def build_climate_health_model_df(
    climate_df: pd.DataFrame,
    health_df: pd.DataFrame,
    climate_key: str,
    health_key: str,
    climate_predictors: list[str],
    health_outcome: str,
    temporal_mode: str = "No temporal join",
    climate_time_field: str | None = None,
    health_time_field: str | None = None,
    health_covariates: list[str] | None = None,
):
    health_covariates = health_covariates or []
    notes = []
    if climate_key not in climate_df.columns or health_key not in health_df.columns:
        return pd.DataFrame(), ["The selected join fields were not found in one of the datasets."]

    climate_keep = [climate_key] + climate_predictors + ([climate_time_field] if climate_time_field else [])
    climate_keep = [c for c in climate_keep if c in climate_df.columns]
    health_keep = [health_key, health_outcome] + health_covariates + ([health_time_field] if health_time_field else [])
    health_keep = [c for c in health_keep if c in health_df.columns]

    cdf = climate_df[climate_keep].copy()
    hdf = health_df[health_keep].copy()

    cdf["join_key"] = normalise_join_key(cdf[climate_key])
    hdf["join_key"] = normalise_join_key(hdf[health_key])

    if temporal_mode != "No temporal join":
        cdf["time_key"] = derive_temporal_key(cdf, climate_time_field, temporal_mode)
        hdf["time_key"] = derive_temporal_key(hdf, health_time_field, temporal_mode)
        cdf = cdf[cdf["time_key"].notna() & (cdf["time_key"] != "")]
        hdf = hdf[hdf["time_key"].notna() & (hdf["time_key"] != "")]
        group_cols = ["join_key", "time_key"]
        notes.append(f"Temporal join mode: {temporal_mode}.")
    else:
        group_cols = ["join_key"]

    climate_numeric = [c for c in climate_predictors if c in cdf.columns]
    health_numeric = [c for c in [health_outcome] + list(health_covariates) if c in hdf.columns]

    for c in climate_numeric:
        cdf[c] = pd.to_numeric(cdf[c], errors="coerce")
    for c in health_numeric:
        hdf[c] = pd.to_numeric(hdf[c], errors="coerce")

    c_grouped = cdf[group_cols + climate_numeric].dropna(subset=climate_numeric, how="all").groupby(group_cols, as_index=False).mean(numeric_only=True)
    h_grouped = hdf[group_cols + health_numeric].dropna(subset=[health_outcome]).groupby(group_cols, as_index=False).mean(numeric_only=True)

    joined = c_grouped.merge(h_grouped, on=group_cols, how="inner")
    if joined.empty:
        return pd.DataFrame(), notes + ["No rows matched between the selected climate and health fields."]

    joined = joined.rename(columns={health_outcome: "__health_outcome__"})
    for cov in health_covariates:
        if cov in joined.columns:
            joined = joined.rename(columns={cov: f"health_{cov}"})
    notes.append(f"Joined {len(joined):,} rows across climate and health fields.")
    return joined, notes


def render_statistical_analysis_tabs(d: pd.DataFrame, aggregated: pd.DataFrame, page_name: str, area_field: str | None, date_field: str | None, selected_vars: list[str], group_col: str, plot_type: str, fig):
    st.markdown("#### Statistical analysis")
    tabs = st.tabs(["Summary", "Correlation", "Regression", "Time Series", "Spatial", "Advanced", "AI-Guided Analysis", "Downloads"])
    with tabs[0]:
        st.dataframe(d[selected_vars].describe().T, use_container_width=True)
        st.markdown("##### Grouped summaries")
        if group_col != "None":
            frames = []
            for col in selected_vars:
                g = d.groupby(group_col)[col].agg(["count", "mean", "median", "min", "max", "std"]).reset_index()
                g.insert(1, "variable", col)
                frames.append(g)
            st.dataframe(pd.concat(frames, ignore_index=True), use_container_width=True)
        else:
            st.info("Choose a group / category field in the Explore controls to enable grouped summaries.")
        st.markdown("##### Missing-data summary")
        st.dataframe(build_missing_summary(d), use_container_width=True)
    with tabs[1]:
        if len(selected_vars) >= 2:
            pearson = d[selected_vars].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
            spearman = d[selected_vars].apply(pd.to_numeric, errors="coerce").corr(method="spearman")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Pearson correlation**")
                st.plotly_chart(px.imshow(pearson, text_auto=True, aspect="auto"), use_container_width=True)
            with c2:
                st.markdown("**Spearman correlation**")
                st.plotly_chart(px.imshow(spearman, text_auto=True, aspect="auto"), use_container_width=True)
        else:
            st.info("Choose at least two numeric variables to run correlation analysis.")
    with tabs[2]:
        model_candidates = [c for c in numeric_columns(d) if d[c].notna().any()]
        if len(model_candidates) < 2:
            st.info("At least two numeric variables are needed for regression analysis.")
        else:
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                outcome = st.selectbox("Outcome variable", model_candidates, key=f"reg_out_{page_name}")
            with r2:
                predictors = st.multiselect("Predictor variables", [c for c in model_candidates if c != outcome], default=[c for c in model_candidates if c != outcome][:2], key=f"reg_pred_{page_name}")
            with r3:
                model_name = st.selectbox("Model", ["Linear regression", "Multiple linear regression", "Logistic regression", "Poisson regression", "Negative binomial regression", "Mixed-effects model"], key=f"reg_model_{page_name}")
            with r4:
                possible_groups = ["None"] + [c for c in categorical_columns(d) if c != area_field]
                group_var = st.selectbox("Group variable", possible_groups, key=f"reg_group_{page_name}")
            if predictors:
                result, coef, note = fit_selected_model(d, outcome, predictors, model_name, group_var if group_var != "None" else None)
                if note:
                    st.caption(note)
                if coef is not None:
                    st.dataframe(coef, use_container_width=True)
                if result is not None:
                    try:
                        st.text(result.summary().as_text())
                    except Exception:
                        st.write(result.summary())
            else:
                st.info("Choose at least one predictor variable.")
    with tabs[3]:
        if date_field and date_field in d.columns and len(selected_vars) >= 1:
            ts_var = st.selectbox("Time-series variable", selected_vars, key=f"ts_var_{page_name}")
            ts_df = d[[date_field, ts_var]].dropna().sort_values(date_field).copy()
            st.plotly_chart(px.line(ts_df, x=date_field, y=ts_var, title="Trend plot"), use_container_width=True)
            if len(selected_vars) >= 2:
                pred_var = st.selectbox("Lag predictor", [v for v in selected_vars if v != ts_var], key=f"lag_pred_{page_name}")
                max_lag = st.slider("Maximum lag", 1, 12, 6, key=f"max_lag_{page_name}")
                lag_df = simple_lag_analysis(d, date_field, ts_var, pred_var, max_lag=max_lag)
                if not lag_df.empty:
                    st.plotly_chart(px.line(lag_df, x="lag", y="correlation", markers=True, title="Lag analysis"), use_container_width=True)
            anomaly_df = anomaly_table(d, date_field, ts_var)
            if not anomaly_df.empty:
                st.plotly_chart(px.line(anomaly_df, x=date_field, y="anomaly", title="Anomaly analysis"), use_container_width=True)
            st.markdown("##### Interrupted time-series (partial)")
            intervention_date = st.date_input("Intervention / threshold date", value=ts_df[date_field].median().date(), key=f"its_date_{page_name}")
            its_df = ts_df.copy()
            its_df["time_index"] = np.arange(len(its_df))
            its_df["post"] = (its_df[date_field].dt.date >= intervention_date).astype(int)
            its_df["time_after"] = its_df["time_index"] * its_df["post"]
            if sm is not None and len(its_df) > 8:
                its_model = sm.OLS(pd.to_numeric(its_df[ts_var], errors='coerce'), sm.add_constant(its_df[["time_index", "post", "time_after"]], has_constant='add')).fit()
                st.text(its_model.summary().as_text())
            else:
                st.info("Interrupted time-series output is shown when enough dated observations are available and statsmodels is installed.")
        else:
            st.info("A date field and at least one selected variable are needed for time-series analysis.")
    with tabs[4]:
        render_maps_for_explorer(page_name, key_suffix="stats_spatial")
    with tabs[5]:
        adv_numeric = [c for c in numeric_columns(d) if c not in {date_field}]
        st.markdown("##### PCA")
        if PCA is not None and len(adv_numeric) >= 2:
            pca_vars = st.multiselect("Variables for PCA", adv_numeric, default=adv_numeric[:min(5, len(adv_numeric))], key=f"pca_vars_{page_name}")
            if len(pca_vars) >= 2:
                pca_df = d[pca_vars].dropna().copy()
                if len(pca_df) >= 3:
                    pca = PCA(n_components=min(3, len(pca_vars)))
                    pcs = pca.fit_transform(pca_df)
                    ev = pd.DataFrame({"component": [f"PC{i+1}" for i in range(pca.n_components_)], "explained_variance_ratio": pca.explained_variance_ratio_})
                    st.dataframe(ev, use_container_width=True)
                    if pcs.shape[1] >= 2:
                        pc_df = pd.DataFrame({"PC1": pcs[:,0], "PC2": pcs[:,1]})
                        st.plotly_chart(px.scatter(pc_df, x="PC1", y="PC2", title="PCA scores"), use_container_width=True)
        else:
            st.info("PCA requires scikit-learn and at least two numeric variables.")
        st.markdown("##### Random forest / boosted trees")
        if len(adv_numeric) >= 2 and RandomForestRegressor is not None:
            outcome_adv = st.selectbox("Outcome for advanced models", adv_numeric, key=f"adv_out_{page_name}")
            preds_adv = st.multiselect("Predictors for advanced models", [c for c in adv_numeric if c != outcome_adv], default=[c for c in adv_numeric if c != outcome_adv][:3], key=f"adv_pred_{page_name}")
            if preds_adv:
                model_df = d[[outcome_adv] + preds_adv].dropna().copy()
                X = model_df[preds_adv]
                y = pd.to_numeric(model_df[outcome_adv], errors='coerce')
                if len(model_df) >= 10:
                    rf = RandomForestRegressor(n_estimators=200, random_state=42)
                    rf.fit(X, y)
                    imp = pd.DataFrame({"variable": preds_adv, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
                    st.dataframe(imp, use_container_width=True)
                    st.plotly_chart(px.bar(imp, x="importance", y="variable", orientation="h", title="Random forest importance"), use_container_width=True)
                    gb = GradientBoostingRegressor(random_state=42)
                    gb.fit(X, y)
                    imp2 = pd.DataFrame({"variable": preds_adv, "importance": gb.feature_importances_}).sort_values("importance", ascending=False)
                    st.plotly_chart(px.bar(imp2, x="importance", y="variable", orientation="h", title="Boosted-tree importance"), use_container_width=True)
                else:
                    st.info("Advanced tree-based models need more rows to be informative.")
        st.markdown("##### GAM / hotspot / DLNM-style workflows")
        st.info("These advanced workflows are included as guided placeholders in this release. Use the AI-Guided Analysis tab to design a GAM-style, hotspot, or lagged climate-health workflow, then refine it with backend or notebook support if needed.")
    with tabs[6]:
        render_ai_box(page_name, plot_type, selected_vars, "Exploratory", False, [], columns=list(d.columns), date_field=date_field)
    with tabs[7]:
        render_figure_export_panel(fig, d, d[selected_vars].describe().T if selected_vars else pd.DataFrame(), page_name, plot_type, selected_vars, x_label_default=str(date_field or "Period"), y_label_default=", ".join(selected_vars[:2]))


def render_explore(df: pd.DataFrame, meta: dict, page_name: str):
    d, date_field = prep_dataframe(df, meta)
    area_field = detect_area_field(d, meta["area_candidates"])
    num_cols = numeric_columns(d)
    if not num_cols:
        st.warning("No numeric columns were found in this dataset.")
        st.dataframe(d.head(100), use_container_width=True)
        return

    st.markdown('<div class="download-card"><p><strong>Pathway 1:</strong> Visualise existing or uploaded data. Use the controls below to filter data, create figures, run statistical analysis, and export journal-ready outputs.</p></div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        area_value = "All"
        if area_field:
            area_value = st.selectbox("Area", ["All"] + sorted(d[area_field].dropna().astype(str).unique().tolist()), key=f"area_{page_name}")
    with f2:
        selected_vars = st.multiselect("Variables", num_cols, default=num_cols[: min(3, len(num_cols))], key=f"vars_{page_name}")
    with f3:
        aggregation = st.selectbox("Aggregation", ["Raw", "Daily", "Weekly", "Monthly", "Yearly"], index=3, key=f"agg_{page_name}")
    with f4:
        statistic = st.selectbox("Statistic", ["Mean", "Sum", "Max", "Min", "Median"], key=f"stat_{page_name}")

    if area_field and area_value != "All":
        d = d[d[area_field].astype(str) == area_value].copy()

    if date_field and date_field in d.columns and d[date_field].notna().any():
        dmin = d[date_field].min().date()
        dmax = d[date_field].max().date()
        dr = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax, key=f"dr_{page_name}")
        if isinstance(dr, tuple) and len(dr) == 2:
            d = d[(d[date_field].dt.date >= dr[0]) & (d[date_field].dt.date <= dr[1])].copy()

    if not selected_vars:
        st.info("Choose at least one variable before running visualisation or analysis.")
        render_ai_box(page_name, columns=list(d.columns), date_field=date_field)
        return
    if d.empty:
        st.error("The selected filters returned no matching data. Please change the area, date range, or variables and try again.")
        return

    d = build_period_column(d, date_field, aggregation)
    aggregated = aggregate_multi(d, selected_vars, statistic) if aggregation != "Raw" else d.copy()
    xcol = "_period" if aggregation != "Raw" else (date_field or "_period")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        plot_type = st.selectbox("Plot type", ["Line", "Bar", "Box", "Histogram", "Scatter", "Heatmap", "Pie"], key=f"plot_{page_name}")
    with p2:
        group_col = st.selectbox("Group / category", ["None"] + [c for c in categorical_columns(d) if c != area_field], key=f"group_{page_name}")
    with p3:
        scatter_y = st.selectbox("Scatter Y variable", ["None"] + [c for c in num_cols if c not in selected_vars[:1]], key=f"scatter_{page_name}")
    with p4:
        use_secondary = st.checkbox("Use secondary y-axis", value=False, key=f"sec_{page_name}")
    secondary_vars = []
    if use_secondary and plot_type == "Line":
        secondary_vars = st.multiselect("Variables on secondary axis", selected_vars, default=selected_vars[-1:] if len(selected_vars) > 1 else [], key=f"secvars_{page_name}")

    st.session_state[f"latest_filtered_{page_name}"] = d.copy()
    source = aggregated if aggregation != "Raw" else d
    fig = None
    if plot_type == "Line":
        if use_secondary and secondary_vars:
            fig = build_secondary_axis_figure(source, xcol, selected_vars, secondary_vars)
        else:
            long_df = source.melt(id_vars=[xcol], value_vars=selected_vars, var_name="variable", value_name="value")
            fig = px.line(long_df, x=xcol, y="value", color="variable", markers=(aggregation != "Raw"), height=560)
    elif plot_type == "Bar":
        long_df = source.melt(id_vars=[xcol], value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.bar(long_df, x=xcol, y="value", color="variable", barmode="group", height=560)
    elif plot_type == "Box":
        long_df = d.melt(value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.box(long_df, x="variable", y="value", color="variable", height=560)
    elif plot_type == "Histogram":
        long_df = d.melt(value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.histogram(long_df, x="value", color="variable", nbins=40, barmode="overlay", height=560)
    elif plot_type == "Scatter":
        xvar = selected_vars[0]
        yvar = scatter_y if scatter_y != "None" else (selected_vars[1] if len(selected_vars) > 1 else None)
        if yvar is None:
            st.info("Choose at least two variables for a scatter plot.")
        else:
            fig = px.scatter(d, x=xvar, y=yvar, color=group_col if group_col != "None" else None, trendline="ols" if sm is not None else None, height=560)
    elif plot_type == "Heatmap":
        corr_df = d[selected_vars].corr(numeric_only=True)
        fig = px.imshow(corr_df, text_auto=True, aspect="auto", height=560)
    elif plot_type == "Pie":
        if group_col == "None":
            st.info("Choose a category / group field for a pie chart.")
        else:
            pie_var = selected_vars[0]
            pie_df = d.groupby(group_col, as_index=False)[pie_var].sum()
            fig = px.pie(pie_df, names=group_col, values=pie_var, height=560)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    interpret_lines, take_home, caution = interpret_dataset(aggregated if aggregation != "Raw" else d, selected_vars, aggregation, statistic, secondary_vars)
    st.markdown("#### Interpretation")
    for line in interpret_lines:
        st.write("- " + line)
    st.success("Take-home message: " + take_home)
    st.caption("Caution: " + caution)

    render_statistical_analysis_tabs(d, aggregated, page_name, area_field, date_field, selected_vars, group_col, plot_type, fig)

    pdf_lines = [f"Workflow: {page_name}", f"Rows after filtering: {len(d)}", f"Area field: {area_field}", f"Selected area: {area_value if area_field else 'All'}", f"Date field: {date_field}", f"Selected variables: {', '.join(selected_vars)}", f"Aggregation: {aggregation}", f"Statistic: {statistic}", f"Secondary axis variables: {', '.join(secondary_vars) if secondary_vars else 'None'}", "", "Interpretation:", *interpret_lines, "", "Take-home message:", take_home, "", "Caution:", caution, "", d[selected_vars].describe().to_string()]

    st.markdown("#### Persistent results & downloads")
    st.markdown('<div class="download-card"><p><strong>Recommended outputs:</strong> keep a persistent filtered CSV and narrative PDF so results remain available in Results & Downloads even after reruns or restarts.</p></div>', unsafe_allow_html=True)
    if st.button("Prepare filtered CSV and narrative PDF", key=f"prepare_export_{page_name}", use_container_width=True, type="primary"):
        manifest = run_export_pipeline(page_name, d, pdf_lines, f"{page_name} summary")
        st.session_state["last_export_id"] = manifest["id"]
    latest_export_id = st.session_state.get("last_export_id")
    if latest_export_id:
        manifest = load_json(manifest_path("export", latest_export_id), {})
        if manifest and manifest.get("status") == "completed":
            render_export_download_buttons(manifest)


def render_maps_for_explorer(page_name: str, key_suffix: str = "main"):
    st.markdown("#### Spatial view")
    if page_name == "Zambia Multi-Hazard":
        geojson_data, meta = load_zambia_hfd_geojson()
        if geojson_data is not None and meta is not None:
            basemap = st.selectbox("Basemap", ["CartoDB Positron", "OpenStreetMap", "Esri Satellite"], key=f"bm_{page_name}_risk_{key_suffix}")
            m = folium.Map(location=meta["center"], zoom_start=6, tiles=None)
            add_selected_basemap(m, basemap)

            risk_colors = {
                "Low": "#93c5fd",
                "Medium": "#facc15",
                "High": "#fb923c",
                "Extreme": "#ef4444",
                "Unknown": "#cbd5e1",
            }

            def style_function(feature):
                label = str(feature["properties"].get("risk_label", "Unknown"))
                color = risk_colors.get(label, "#cbd5e1")
                return {
                    "fillColor": color,
                    "color": "#475569",
                    "weight": 0.8,
                    "fillOpacity": 0.65,
                }

            tooltip = folium.GeoJsonTooltip(
                fields=["DISTRICT", "compound_HFD", "risk_label"],
                aliases=["District", "Compound HFD score", "Risk class"],
                localize=True,
                sticky=False,
                labels=True,
            )

            folium.GeoJson(
                geojson_data,
                name="Multi-Hazard risk",
                style_function=style_function,
                tooltip=tooltip,
            ).add_to(m)

            legend_html = """
            <div style="
                position: fixed;
                bottom: 30px;
                left: 30px;
                z-index: 9999;
                background: white;
                padding: 10px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                font-size: 13px;
            ">
            <strong>Risk legend</strong><br>
            <span style="display:inline-block;width:14px;height:14px;background:#93c5fd;border:1px solid #94a3b8;"></span> Low<br>
            <span style="display:inline-block;width:14px;height:14px;background:#facc15;border:1px solid #94a3b8;"></span> Medium<br>
            <span style="display:inline-block;width:14px;height:14px;background:#fb923c;border:1px solid #94a3b8;"></span> High<br>
            <span style="display:inline-block;width:14px;height:14px;background:#ef4444;border:1px solid #94a3b8;"></span> Extreme
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            folium.LayerControl().add_to(m)
            st_folium(m, height=560, use_container_width=True, key=f"map_{page_name}_risk_{key_suffix}")
            st.caption("Interactive Zambia district Multi-Hazard map for Flood-Heat-Drought risk classes.")
            return

    c1, c2, c3 = st.columns(3)
    with c1:
        basemap = st.selectbox("Basemap", ["OpenStreetMap", "Esri Satellite", "CartoDB Positron"], key=f"bm_{page_name}_{key_suffix}")
    with c2:
        lat = st.number_input("Center latitude", value=0.0, format="%.6f", key=f"lat_{page_name}_{key_suffix}")
    with c3:
        lon = st.number_input("Center longitude", value=25.0, format="%.6f", key=f"lon_{page_name}_{key_suffix}")
    zoom = st.slider("Zoom", 2, 12, 5, key=f"zoom_{page_name}_{key_suffix}")
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)
    if basemap == "OpenStreetMap":
        folium.TileLayer("OpenStreetMap", name="Street").add_to(m)
    elif basemap == "Esri Satellite":
        folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
    else:
        folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    Draw(export=True).add_to(m)
    folium.LayerControl().add_to(m)
    out = st_folium(m, height=560, use_container_width=True, key=f"map_{page_name}_{key_suffix}")
    if out and out.get("last_active_drawing"):
        st.success("Area of interest captured from the map.")
        st.json(out["last_active_drawing"])


def workflow_page(page_name: str):
    meta = WORKFLOW_META[page_name]
    banner_title = DISPLAY_PAGE_LABELS.get(page_name, page_name)
    case_note = "Case-study dataset: Brazil" if page_name in ["Brazil Flood", "Brazil Heat"] else ("Case-study dataset: Zambia" if page_name == "Zambia Multi-Hazard" else "Global/custom upload module")
    st.markdown(f'<div class="section-banner {meta["banner_class"]}"><h2 style="margin:0;">{banner_title}</h2><div>{meta["summary"]}<br><strong>{case_note}</strong></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="note-box"><strong>Pathway 1 · Data Analysis and Visualisation</strong> — use this module to work through data preview, interactive figures, nested statistical analysis tabs, AI-guided analysis, and figure/data export.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 3.4], gap="medium")
    with left:
        df = render_upload_block(page_name, meta)
    with right:
        if df is None:
            st.markdown('<div class="white-card"><h4>Ready to explore</h4><p>Choose a REACH Project dataset or upload a CSV/ZIP file to unlock the full Data Analysis and Visualisation pathway.</p><p class="small-muted">Inside <strong>Explore</strong> you will find the nested analysis suite for Summary, Correlation, Regression, Time Series, Spatial, Advanced, AI-Guided Analysis, and Figure & Data Export.</p></div>', unsafe_allow_html=True)
        else:
            d, _ = prep_dataframe(df, meta)
            area_field = detect_area_field(d, meta["area_candidates"])
            year_count = 0
            for yc in meta["year_candidates"]:
                if yc in d.columns:
                    year_count = int(pd.to_numeric(d[yc], errors="coerce").dropna().nunique())
                    break
            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="metric-card"><h3>{len(d):,}</h3><div class="small-muted">Rows</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><h3>{int(d[area_field].astype(str).nunique()) if area_field else 0}</h3><div class="small-muted">Areas</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><h3>{year_count}</h3><div class="small-muted">Years</div></div>', unsafe_allow_html=True)
    if page_name == "Zambia Multi-Hazard" and st.session_state.pop("open_multi_map", False):
        st.markdown('<div class="note-box"><strong>Interactive Multi-Hazard map opened from the homepage.</strong> You can use the full map below and then continue with the other tabs as needed.</div>', unsafe_allow_html=True)
        render_maps_for_explorer(page_name, key_suffix="home_open")
        st.markdown("---")
    tabs = st.tabs(["Overview", "Explore", "Spatial view", "Factsheet", "Variable dictionary", "Downloads"])
    with tabs[0]:
        st.markdown(safe_read_text(FACTSHEETS_DIR / meta["workflow_file"]))
        if df is not None:
            st.markdown("#### Data preview")
            st.dataframe(df.head(100), use_container_width=True)
    with tabs[1]:
        if df is None:
            st.info("Choose a REACH Project dataset or upload a CSV/ZIP file first.")
        else:
            st.markdown('<div class="download-card"><p><strong>Analysis suite:</strong> Summary · Correlation · Regression · Time Series · Spatial · Advanced · AI-Guided Analysis · Figure & Data Export</p></div>', unsafe_allow_html=True)
            render_explore(df, meta, page_name)
    with tabs[2]:
        render_maps_for_explorer(page_name, key_suffix="workflow_tab")
    with tabs[3]:
        st.markdown(safe_read_text(FACTSHEETS_DIR / meta["workflow_file"]))
    with tabs[4]:
        render_variable_dictionary(meta)
    with tabs[5]:
        st.info("Prepare filtered outputs from the Explore tab. Finished outputs remain visible in Results & Downloads even after reruns or restarts.")


@st.cache_data(show_spinner=False)
def fetch_dhs_data(country_code: str, indicator_id: str, breakdown: str):
    if requests is None:
        raise RuntimeError("The requests package is not available. Add requests to requirements.txt.")
    params = {
        "countryIds": country_code,
        "indicatorIds": indicator_id,
        "breakdown": breakdown,
        "f": "json",
    }
    response = requests.get("https://api.dhsprogram.com/rest/dhs/data", params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("Data", [])
    return pd.DataFrame(data)


@st.cache_data(show_spinner=False)
def fetch_dhs_indicators(country_code: str):
    if requests is None:
        raise RuntimeError("The requests package is not available. Add requests to requirements.txt.")
    params = {"countryIds": country_code, "f": "json"}
    response = requests.get("https://api.dhsprogram.com/rest/dhs/indicators", params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload.get("Data", []))


@st.cache_data(show_spinner=False)
def fetch_dhs_countries():
    if requests is None:
        return pd.DataFrame()
    try:
        response = requests.get("https://api.dhsprogram.com/rest/dhs/countries", params={"f": "json"}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        countries = pd.DataFrame(payload.get("Data", []))
        if countries.empty:
            return countries
        # Try common field variants from the DHS API.
        name_col = next((c for c in ["CountryName", "countryName", "Country", "country"] if c in countries.columns), None)
        code_col = next((c for c in ["DHS_CountryCode", "CountryCode", "countryCode", "CountryId", "countryId"] if c in countries.columns), None)
        if name_col is None or code_col is None:
            return pd.DataFrame()
        cleaned = countries[[name_col, code_col]].dropna().copy()
        cleaned.columns = ["CountryName", "CountryCode"]
        cleaned["CountryName"] = cleaned["CountryName"].astype(str).str.strip()
        cleaned["CountryCode"] = cleaned["CountryCode"].astype(str).str.strip().str.upper()
        cleaned = cleaned[cleaned["CountryName"] != ""]
        cleaned = cleaned.drop_duplicates(subset=["CountryName", "CountryCode"]).sort_values("CountryName").reset_index(drop=True)
        return cleaned
    except Exception:
        return pd.DataFrame()


def render_health_page():
    st.markdown('<div class="section-banner health-banner"><h2 style="margin:0;">Health</h2><div>Early health-data integration using DHS-style extracts or live DHS API access where available. Use this page to discover indicators, inspect survey values, and start climate–health and health-systems comparisons.</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="note-box"><strong>Beta note:</strong> this page adds a practical health-data layer to the platform, but full health-systems analytics still need richer facility and service-readiness sources. Use survey outputs carefully, especially when linking them with climate time series.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 2.3], gap="large")
    with left:
        source = st.radio("Health data source", ["Use built-in Brazil ANC demo", "Use built-in Brazil PNC demo", "Use built-in Zambia ANC demo", "Use built-in Zambia PNC demo", "Fetch from DHS API", "Upload DHS-style CSV"], key="health_source")
        if source == "Use built-in Brazil ANC demo":
            demo_health = load_demo_dataframe("demo_brazil_anc_dhs.csv")
            if demo_health is not None:
                st.session_state["health_df"] = demo_health.loc[:, ~demo_health.columns.duplicated()].copy()
                st.success(f"Loaded built-in Brazil ANC demo ({len(demo_health):,} rows).")
                st.markdown('<div class="note-box"><strong>Demo note:</strong> this is a DHS-style demonstration table aligned to the homepage Brazil flood preview. It is useful for testing climate–health plots and matrices, but it is not an official DHS extract. Use API fetch or your own CSV for real DHS analysis.</div>', unsafe_allow_html=True)
            else:
                st.error("Built-in Brazil ANC demo file was not found.")
        elif source == "Use built-in Brazil PNC demo":
            demo_health = load_demo_dataframe("demo_brazil_pnc_dhs.csv")
            if demo_health is not None:
                st.session_state["health_df"] = demo_health.loc[:, ~demo_health.columns.duplicated()].copy()
                st.success(f"Loaded built-in Brazil PNC demo ({len(demo_health):,} rows).")
            else:
                st.error("Built-in Brazil PNC demo file was not found.")
        elif source == "Use built-in Zambia ANC demo":
            demo_health = load_demo_dataframe("demo_zambia_anc_dhs.csv")
            if demo_health is not None:
                st.session_state["health_df"] = demo_health.loc[:, ~demo_health.columns.duplicated()].copy()
                st.success(f"Loaded built-in Zambia ANC demo ({len(demo_health):,} rows).")
            else:
                st.error("Built-in Zambia ANC demo file was not found.")
        elif source == "Use built-in Zambia PNC demo":
            demo_health = load_demo_dataframe("demo_zambia_pnc_dhs.csv")
            if demo_health is not None:
                st.session_state["health_df"] = demo_health.loc[:, ~demo_health.columns.duplicated()].copy()
                st.success(f"Loaded built-in Zambia PNC demo ({len(demo_health):,} rows).")
            else:
                st.error("Built-in Zambia PNC demo file was not found.")
        elif source == "Fetch from DHS API":
            countries_df = fetch_dhs_countries()
            if not countries_df.empty:
                country_names = countries_df["CountryName"].tolist()
                default_name = "Brazil" if "Brazil" in country_names else country_names[0]
                default_index = country_names.index(default_name)
                country_name = st.selectbox("Country", country_names, index=default_index)
                selected_row = countries_df.loc[countries_df["CountryName"] == country_name].iloc[0]
                default_code = str(selected_row["CountryCode"]).upper().strip()
            else:
                fallback_names = sorted(COUNTRIES)
                default_index = fallback_names.index("Brazil") if "Brazil" in fallback_names else 0
                country_name = st.selectbox("Country", fallback_names, index=default_index)
                default_code = DHS_COUNTRY_HINTS.get(country_name, "")
                st.caption("Live DHS country list could not be loaded, so a broad global fallback list is shown. Enter the DHS country code if needed.")
            country_code = st.text_input("Country code", default_code).upper().strip()
            indicator_id = st.text_input("Indicator ID", "CN_NUTS_C_HA2")
            breakdown = st.selectbox("Breakdown", ["all", "subnational", "national"], index=1)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Fetch DHS data", use_container_width=True, type="primary"):
                    try:
                        data = fetch_dhs_data(country_code, indicator_id, breakdown)
                        if data.empty:
                            st.error("No DHS data were returned for this country, indicator, and breakdown combination.")
                        else:
                            st.session_state["health_df"] = data
                            st.success(f"Fetched {len(data):,} DHS records.")
                    except Exception as e:
                        st.error(f"DHS fetch failed: {e}")
            with c2:
                if st.button("Browse indicators", use_container_width=True):
                    try:
                        indicators = fetch_dhs_indicators(country_code)
                        st.session_state["health_indicators"] = indicators
                    except Exception as e:
                        st.error(f"Indicator lookup failed: {e}")
        else:
            st.markdown('<div class="upload-box"><strong>Upload DHS-style CSV</strong><br><span class="small-muted">Expected fields may include Value, SurveyYear, Indicator, CharacteristicLabel, RegionId, SurveyType, and similar DHS export columns.</span></div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Upload health CSV", type=["csv"], key="health_upload")
            if uploaded is not None:
                try:
                    health_df = pd.read_csv(uploaded)
                    health_df = health_df.loc[:, ~health_df.columns.duplicated()].copy()
                    st.session_state["health_df"] = health_df
                    st.success(f"Loaded {len(health_df):,} health records.")
                except Exception as e:
                    st.error(f"Health upload failed: {e}")
        render_ai_box("Health", columns=list(st.session_state.get("health_df", pd.DataFrame()).columns) if st.session_state.get("health_df") is not None else [], date_field="SurveyYear" if st.session_state.get("health_df") is not None and "SurveyYear" in st.session_state.get("health_df").columns else None)

    with right:
        if "health_indicators" in st.session_state:
            st.markdown("#### Indicator browser")
            st.dataframe(st.session_state["health_indicators"].head(200), use_container_width=True)
        health_df = st.session_state.get("health_df")
        if health_df is None or health_df.empty:
            st.markdown('<div class="health-card"><h4>No health dataset loaded yet</h4><p class="small-muted">Load the built-in Brazil ANC demo, fetch DHS data, or upload a DHS-style CSV to start health exploration and climate–health interpretation.</p></div>', unsafe_allow_html=True)
            return

        health_df = health_df.loc[:, ~health_df.columns.duplicated()].copy()
        st.markdown('<div class="note-box"><strong>Cross-workflow use:</strong> once a health dataset is loaded on this page, it becomes available in the <strong>Correlation</strong> and <strong>Regression</strong> tabs of the climate workflow Explore pages. There you can choose climate or hazard variables as predictors and DHS or health variables as outcomes.</div>', unsafe_allow_html=True)
        if "Value" in health_df.columns:
            health_df["Value"] = pd.to_numeric(health_df["Value"], errors="coerce")
        if "SurveyYear" in health_df.columns:
            health_df["SurveyYear"] = pd.to_numeric(health_df["SurveyYear"], errors="coerce")

        numeric_cols = numeric_columns(health_df)
        cat_cols = categorical_columns(health_df)
        chart_col = "Value" if "Value" in health_df.columns else (numeric_cols[0] if numeric_cols else None)

        st.markdown("#### Health dataset preview")
        st.dataframe(health_df.head(100), use_container_width=True)
        hc0, hc1 = st.columns([1.2, 1.3])
        with hc0:
            analysis_mode = st.selectbox(
                "Health analysis mode",
                [
                    "Health-only descriptive analysis",
                    "Climate–Health comparison",
                    "Health systems / service comparison",
                ],
                key="health_analysis_mode",
            )
        with hc1:
            plot_family = st.selectbox(
                "Plot family",
                [
                    "Trend or comparison plot",
                    "Correlation heatmap",
                    "Priority matrix",
                ],
                key="health_plot_family",
            )

        if chart_col is None:
            st.warning("No numeric health field was found. Add a numeric Value column or another numeric measure to use the health analysis page.")
            return

        def aggregate_health(df, groupers, value_col, stat_name):
            groupers = unique_non_none(groupers)
            stat_fn = {"Mean": "mean", "Median": "median", "Max": "max", "Sum": "sum"}[stat_name]
            if not groupers:
                return pd.DataFrame({value_col: [pd.to_numeric(df[value_col], errors="coerce").agg(stat_fn)]})
            grouped = (
                df.groupby(groupers, dropna=False, as_index=False)[value_col]
                .agg(stat_fn)
            )
            grouped = grouped.loc[:, ~grouped.columns.duplicated()].copy()
            return grouped

        if plot_family == "Trend or comparison plot":
            hc1, hc2, hc3, hc4 = st.columns(4)
            with hc1:
                x_choices = [c for c in ["SurveyYear", "CharacteristicLabel", "RegionName", "SurveyType"] if c in health_df.columns] or health_df.columns.tolist()
                x_col = st.selectbox("X-axis / category", x_choices, key="health_x")
            with hc2:
                colour_choices = [c for c in cat_cols if c != x_col]
                colour_col = st.selectbox("Colour / group", ["None"] + colour_choices, key="health_group")
            with hc3:
                agg_mode = st.selectbox("Statistic", ["Mean", "Median", "Max", "Sum"], key="health_stat")
            with hc4:
                chart_type = st.selectbox(
                    "Chart type",
                    ["Auto", "Line", "Bar", "Box"],
                    key="health_chart_type",
                )
            hplot = aggregate_health(health_df, [x_col, colour_col], chart_col, agg_mode)
            if x_col == "SurveyYear" and chart_type in ["Auto", "Line"]:
                fig = px.line(hplot, x=x_col, y=chart_col, color=colour_col if colour_col != "None" else None, markers=True, title="Health indicator trend")
            elif chart_type == "Box" and colour_col != "None":
                fig = px.box(health_df, x=colour_col, y=chart_col, points="outliers", title="Health indicator distribution")
            else:
                fig = px.bar(hplot, x=x_col if x_col == "SurveyYear" else chart_col, y=chart_col if x_col == "SurveyYear" else x_col, color=colour_col if colour_col != "None" else None, orientation="v" if x_col == "SurveyYear" else "h", title="Health indicator comparison")
            st.plotly_chart(fig, use_container_width=True)

        elif plot_family == "Correlation heatmap":
            heat_candidates = [c for c in numeric_cols if health_df[c].notna().any()]
            if len(heat_candidates) < 2:
                st.info("At least two numeric health or service variables are needed for a correlation heatmap.")
            else:
                chosen = st.multiselect("Variables for correlation heatmap", heat_candidates, default=heat_candidates[: min(6, len(heat_candidates))], key="health_heat_vars")
                if len(chosen) >= 2:
                    corr = health_df[chosen].apply(pd.to_numeric, errors="coerce").corr(numeric_only=True)
                    st.plotly_chart(px.imshow(corr, text_auto=True, aspect="auto", title="Health / service correlation heatmap"), use_container_width=True)
                else:
                    st.info("Choose at least two numeric variables.")

        else:
            st.markdown("#### Priority matrix")
            pm1, pm2, pm3 = st.columns(3)
            with pm1:
                x_metric = st.selectbox("X metric", numeric_cols, index=0, key="health_pm_x")
            with pm2:
                y_metric = st.selectbox("Y metric", numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key="health_pm_y")
            with pm3:
                label_col = st.selectbox("Label field", [c for c in ["CharacteristicLabel", "RegionName", "Indicator", "SurveyType"] if c in health_df.columns] or cat_cols, key="health_pm_label")
            matrix_df = health_df[[label_col, x_metric, y_metric]].dropna().copy()
            if matrix_df.empty:
                st.info("No rows are available for the selected priority-matrix fields.")
            else:
                grouped = matrix_df.groupby(label_col, as_index=False)[[x_metric, y_metric]].mean()
                grouped["priority_flag"] = np.where(
                    (grouped[x_metric] >= grouped[x_metric].median()) & (grouped[y_metric] >= grouped[y_metric].median()),
                    "Higher priority",
                    "Review / lower priority",
                )
                fig = px.scatter(
                    grouped,
                    x=x_metric,
                    y=y_metric,
                    color="priority_flag",
                    text=label_col,
                    title="Health or service priority matrix",
                )
                fig.update_traces(textposition="top center")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(grouped.sort_values(["priority_flag", y_metric], ascending=[True, False]), use_container_width=True)

        st.markdown("#### Climate–health and health-systems comparison")
        available_workflows = [k for k in ["Brazil Flood", "Brazil Heat", "Zambia Multi-Hazard", "Custom Dataset Explorer"] if st.session_state.get(f"latest_filtered_{k}") is not None]
        if not available_workflows:
            st.info("Open one of the climate workflows, filter a dataset, and come back here to compare climate with health or health-systems variables in this session.")
            return

        wf = st.selectbox("Climate workflow dataset", available_workflows)
        climate_df = st.session_state.get(f"latest_filtered_{wf}").copy()
        climate_df = climate_df.loc[:, ~climate_df.columns.duplicated()].copy()
        ccols = climate_df.columns.tolist()
        hcols = health_df.columns.tolist()
        climate_numeric = numeric_columns(climate_df)
        health_numeric = [c for c in numeric_cols if c in health_df.columns]

        join_mode = st.selectbox(
            "Comparison type",
            [
                "Climate–Health scatter",
                "Climate–Health table",
                "Climate–Health Systems matrix",
            ],
            key="health_join_mode",
        )

        jc1, jc2, jc3, jc4 = st.columns(4)
        with jc1:
            default_hk = hcols.index("CharacteristicLabel") if "CharacteristicLabel" in hcols else 0
            health_key = st.selectbox("Health join field", hcols, index=default_hk, key="health_join_field")
        with jc2:
            default_ck = ccols.index("municipality") if "municipality" in ccols else 0
            climate_key = st.selectbox("Climate join field", ccols, index=default_ck, key="climate_join_field")
        with jc3:
            health_val = st.selectbox("Health value field", health_numeric, index=0, key="health_value_field")
        with jc4:
            climate_val = st.selectbox("Climate value field", climate_numeric, index=0, key="climate_value_field")

        if health_key and climate_key and health_val and climate_val:
            health_small = health_df[[health_key, health_val]].dropna().rename(columns={health_key: "join_key"})
            climate_small = climate_df[[climate_key, climate_val]].dropna().rename(columns={climate_key: "join_key"})
            if analysis_mode == "Health systems / service comparison":
                service_candidates = [c for c in health_numeric if c != health_val]
                if service_candidates:
                    service_val = st.selectbox("Health systems / service field", service_candidates, key="health_service_field")
                    service_small = health_df[[health_key, service_val]].dropna().rename(columns={health_key: "join_key"})
                    joined = climate_small.merge(health_small, on="join_key", how="inner").merge(service_small, on="join_key", how="inner")
                else:
                    joined = climate_small.merge(health_small, on="join_key", how="inner")
                    service_val = None
            else:
                joined = climate_small.merge(health_small, on="join_key", how="inner")
                service_val = None

            if joined.empty:
                st.warning("No rows matched between the selected health and climate fields. Try another join field, another climate workflow, or simpler admin-level matching.")
            else:
                st.success(f"Joined {len(joined):,} rows across the selected fields.")
                if join_mode == "Climate–Health scatter":
                    fig = px.scatter(joined, x=climate_val, y=health_val, trendline="ols", title="Climate–Health comparison")
                    st.plotly_chart(fig, use_container_width=True)
                elif join_mode == "Climate–Health table":
                    st.dataframe(joined.head(300), use_container_width=True)
                    summary = joined[[climate_val, health_val] + ([service_val] if service_val else [])].describe().T
                    st.dataframe(summary, use_container_width=True)
                else:
                    if service_val and service_val in joined.columns:
                        matrix = joined[[climate_val, health_val, service_val]].dropna().copy()
                        matrix["priority_flag"] = np.where(
                            (matrix[climate_val] >= matrix[climate_val].median()) & (matrix[service_val] >= matrix[service_val].median()),
                            "Higher climate + systems concern",
                            "Lower combined concern",
                        )
                        fig = px.scatter(matrix, x=climate_val, y=service_val, size=health_val, color="priority_flag", title="Climate–Health Systems matrix")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig = px.scatter(joined, x=climate_val, y=health_val, title="Climate–Health matrix starter")
                        st.plotly_chart(fig, use_container_width=True)
                st.dataframe(joined.head(150), use_container_width=True)


def build_unit_list(country: str, hazard: str):

    if country == "Brazil" and hazard == "Flood":
        df = load_demo_dataframe("demo_brazil_flood.csv")
        if df is not None and "municipality" in df.columns:
            return sorted(df["municipality"].dropna().astype(str).unique().tolist())
    if country == "Brazil" and hazard == "Heat":
        df = load_demo_dataframe("demo_brazil_heat.csv")
        if df is not None and "municipality" in df.columns:
            return sorted(df["municipality"].dropna().astype(str).unique().tolist())
    if country == "Zambia" or hazard == "Multi-Hazard":
        df = load_demo_dataframe("demo_zambia_multihazard.csv")
        if df is not None and "DISTRICT" in df.columns:
            return sorted(df["DISTRICT"].dropna().astype(str).unique().tolist())
    return ["Unit_01", "Unit_02", "Unit_03", "Unit_04", "Unit_05"]


def create_analysis_manifest(payload: dict) -> dict:
    job_id = f"job_{uuid4().hex[:10]}"
    units = build_unit_list(payload["country"], payload["hazard"])
    manifest = {
        "id": job_id,
        "kind": "job",
        "title": f"{payload['hazard']} analysis setup for {payload['country']}",
        "status": "queued",
        "message": "Your request has started.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "payload": payload,
        "steps": [
            {"name": "validate_inputs", "status": "pending"},
            {"name": "prepare_job_spec", "status": "pending"},
            {"name": "process_units", "status": "pending"},
            {"name": "register_outputs", "status": "pending"},
        ],
        "units": [{"name": u, "status": "pending"} for u in units],
        "job_spec_path": None,
    }
    return register_manifest("job", manifest)


def run_analysis_manifest(job_id: str):
    manifest = load_json(manifest_path("job", job_id), {})
    if not manifest:
        st.error("The selected job manifest could not be found.")
        return
    steps = manifest["steps"]
    total_units = len(manifest["units"])
    progress = st.progress(0)
    log_box = st.empty()
    lines = []

    def mark_step(name: str, status: str):
        for step in steps:
            if step["name"] == name:
                step["status"] = status
        manifest["steps"] = steps
        register_manifest("job", manifest)

    manifest["status"] = "running"
    manifest["message"] = "Analysis is running."
    register_manifest("job", manifest)

    if steps[0]["status"] != "completed":
        mark_step("validate_inputs", "running")
        payload = manifest["payload"]
        if not payload.get("variables"):
            manifest["status"] = "failed"
            manifest["message"] = "Analysis could not start because no variables were selected."
            mark_step("validate_inputs", "failed")
            register_manifest("job", manifest)
            st.error(manifest["message"])
            return
        if payload.get("start_date") > payload.get("end_date"):
            manifest["status"] = "failed"
            manifest["message"] = "Analysis could not start because the start date is later than the end date."
            mark_step("validate_inputs", "failed")
            register_manifest("job", manifest)
            st.error(manifest["message"])
            return
        mark_step("validate_inputs", "completed")

    if steps[1]["status"] != "completed":
        mark_step("prepare_job_spec", "running")
        spec_path = JOBS_DIR / f"{job_id}_job_spec.json"
        spec_path.write_text(json.dumps(manifest["payload"], indent=2), encoding="utf-8")
        manifest["job_spec_path"] = str(spec_path)
        mark_step("prepare_job_spec", "completed")
        register_manifest("job", manifest)

    mark_step("process_units", "running")
    done = sum(1 for u in manifest["units"] if u["status"] == "completed")
    for idx, unit in enumerate(manifest["units"], start=1):
        if unit["status"] == "completed":
            lines.append(f"⏭️ Already complete: {unit['name']}, skipping...")
            continue
        unit["status"] = "completed"
        done += 1
        manifest["message"] = f"Processing units: {done}/{total_units} complete"
        register_manifest("job", manifest)
        progress.progress(int(done / max(total_units, 1) * 100))
        log_box.code("\n".join(lines + [f"✅ Completed: {unit['name']}"]))
    mark_step("process_units", "completed")

    mark_step("register_outputs", "running")
    summary_path = JOBS_DIR / f"{job_id}_summary.txt"
    summary_path.write_text("\n".join([f"Job title: {manifest['title']}", f"Completed units: {done}/{total_units}", f"Updated: {now_iso()}"]), encoding="utf-8")
    manifest["summary_path"] = str(summary_path)
    mark_step("register_outputs", "completed")
    manifest["status"] = "completed"
    manifest["message"] = "Analysis setup completed successfully. Results and job files are available in Results & Downloads."
    register_manifest("job", manifest)
    lines.append(f"✅ Job finished: {manifest['title']}")
    log_box.code("\n".join(lines))
    st.success(manifest["message"])


def render_existing_job_status():
    jobs = list_manifests("job")
    active = next((j for j in jobs if j.get("status") in {"queued", "running"}), None)
    if active:
        completed = sum(1 for u in active.get("units", []) if u.get("status") == "completed")
        total = len(active.get("units", []))
        st.markdown("#### Resume available")
        render_status_box(active["title"], active["status"], active.get("message", ""), progress=(completed / total if total else 0))
        if st.button("Resume unfinished job", use_container_width=True):
            run_analysis_manifest(active["id"])
        if completed:
            st.write(f"Previous progress detected. {completed} of {total} units already completed.")
            for unit in active["units"][:10]:
                if unit.get("status") == "completed":
                    st.write(f"⏭️ Already complete: {unit['name']}, skipping...")



def run_new_analysis_page():
    st.markdown('<div class="section-banner multi-banner"><h2 style="margin:0;">Create Climate–Health Data Job</h2><div>Define your area of interest (AOI), choose a workflow, and submit a job to extract, process, and download climate and health data outputs.</div></div>', unsafe_allow_html=True)
    render_existing_job_status()
    s1, s2 = st.columns([1.15, 2.1], gap="large")

    workflow_options = ["Flood", "Heatwaves", "Multi-Hazard", "Health", "Future workflow"]
    input_mode_order = ["Predefined area", "Upload boundary file", "Draw on map", "Point and buffer"]
    risk_label_labels = {
        "Very Low": "Very Low",
        "Low": "Low",
        "Medium": "Moderate",
        "High": "High",
        "Very High": "Very High",
        "Extreme": "Extreme",
    }
    risk_label_internal = ["Very Low", "Low", "Medium", "High", "Very High", "Extreme"]

    with s1:
        st.markdown("#### Job configuration")
        country = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index("Brazil"), help="Select the country that contains your area of interest.")
        spatial_unit_type = st.selectbox("Region / spatial unit type", ["Country", "Admin 1 / Province / State", "Admin 2 / District / Municipality", "Basin / catchment", "Uploaded custom polygon", "Coordinates and buffer"], help="Choose the spatial level or geometry type for the data job.")
        hazard = st.selectbox("Workflow type", workflow_options, help="Choose the extraction or processing workflow to run.")
        input_mode = st.selectbox("AOI definition method", input_mode_order, help="Select how you want to define the area of interest.")
        if input_mode == "Upload boundary file":
            st.markdown('<div class="note-box"><strong>AOI upload mode:</strong> the shapefile ZIP and GeoJSON upload boxes appear immediately below.</div>', unsafe_allow_html=True)

        if input_mode == "Upload boundary file":
            st.info("Upload a zipped shapefile or a GeoJSON boundary file to define the AOI.")
        elif input_mode == "Draw on map":
            st.info("Use the map panel to draw the AOI. The geometry will be captured from the interactive map.")
        elif input_mode == "Point and buffer":
            st.info("Use latitude, longitude, and buffer radius to create a simple circular AOI.")
        else:
            st.info("Use a predefined area or continue with other settings below.")

        start_date = st.date_input("Start date", help="Choose the start date for the processing period.")
        end_date = st.date_input("End date", help="Choose the end date for the processing period.")
        temporal_resolution = st.selectbox("Temporal resolution", ["Daily", "Weekly", "Monthly", "Seasonal", "Yearly"], index=2, help="Choose the temporal resolution for the requested outputs.")
        variables = st.multiselect(
            "Variables to extract",
            ["Tmax", "Tmin", "Tmean", "RH", "SPI", "SSI", "RX1day", "RX5day", "Flood area", "Population exposed", "Health facility exposure", "Health indicator value"],
            default=["Tmax", "RX1day"],
            placeholder="Select variables",
            help="Select the climate, environmental, and health-related variables to include.",
        )
        outputs = st.multiselect(
            "Requested outputs",
            ["Summary table", "Spatial risk layer", "Filtered CSV", "Risk classes", "PDF summary"],
            default=["Summary table", "Spatial risk layer", "Risk classes"],
            placeholder="Select outputs",
            help="Choose the tables, maps, indicators, and downloadable files to generate.",
        )
        gee_project = st.text_input("Google Earth Engine project", "ee-reachprojectlshtm", help="Enter the Earth Engine project to use for data access and processing.")

        uploaded_shp = None
        uploaded_geo = None
        lat = None
        lon = None
        buffer_km = None
        predefined_name = None

        if input_mode == "Upload boundary file":
            uploaded_shp = st.file_uploader("Upload shapefile ZIP", type=["zip"], key="rna_shp", help="Upload a zipped shapefile containing the AOI boundary.")
            uploaded_geo = st.file_uploader("Upload GeoJSON", type=["geojson", "json"], key="rna_geo", help="Upload a GeoJSON boundary file for the AOI.")
            if uploaded_shp is None and uploaded_geo is None:
                st.warning("No AOI boundary file has been uploaded yet.")
            else:
                if uploaded_shp is not None:
                    st.success(f"Shapefile uploaded: {uploaded_shp.name}")
                if uploaded_geo is not None:
                    st.success(f"GeoJSON uploaded: {uploaded_geo.name}")
        elif input_mode == "Point and buffer":
            lat = st.number_input("Latitude", value=0.0, format="%.6f", key="rna_lat", help="Enter the latitude of the AOI centre point.")
            lon = st.number_input("Longitude", value=25.0, format="%.6f", key="rna_lon", help="Enter the longitude of the AOI centre point.")
            buffer_km = st.number_input("Buffer radius (km)", value=10.0, min_value=0.0, key="rna_buffer", help="Set the radius around the centre point to create the AOI.")
        elif input_mode == "Predefined area":
            predefined_name = st.text_input("Predefined area name", value="", help="Type the area name, code, or identifier used in your backend workflow.")
        else:
            st.caption("Draw the AOI on the map panel and then create the job once the geometry is captured.")

        risk_method = st.selectbox("Risk classification method", ["Quantiles", "Fixed thresholds", "Z-score / standardised"], help="Choose how risk values should be classified.")
        risk_labels = st.multiselect(
            "Risk labels",
            risk_label_internal,
            default=risk_label_internal,
            format_func=lambda x: risk_label_labels.get(x, x),
            placeholder="Select risk labels",
            help="Select the labels to use for risk categories.",
        )

        if st.button("Create job", use_container_width=True, type="primary"):
            if not variables:
                st.error("Cannot start analysis because no variable was selected.")
            elif start_date > end_date:
                st.error("Cannot start analysis because the start date is later than the end date.")
            elif input_mode == "Upload boundary file" and uploaded_shp is None and uploaded_geo is None:
                st.error("Cannot start analysis because no AOI file was uploaded. Upload a shapefile ZIP or GeoJSON file.")
            else:
                file_prefix = f"aoi_{uuid4().hex[:8]}"
                payload = {
                    "country": country,
                    "spatial_unit_type": spatial_unit_type,
                    "hazard": hazard,
                    "temporal_resolution": temporal_resolution,
                    "input_mode": input_mode,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "variables": variables,
                    "outputs": outputs,
                    "gee_project": gee_project,
                    "lat": lat,
                    "lon": lon,
                    "buffer_km": buffer_km,
                    "predefined_name": predefined_name,
                    "risk_method": risk_method,
                    "risk_labels": risk_labels,
                    "uploaded_shp": bool(uploaded_shp),
                    "uploaded_geo": bool(uploaded_geo),
                    "uploaded_shp_path": save_uploaded_aoi_file(uploaded_shp, file_prefix + "_boundary") if uploaded_shp is not None else None,
                    "uploaded_geo_path": save_uploaded_aoi_file(uploaded_geo, file_prefix + "_boundary") if uploaded_geo is not None else None,
                }
                manifest = create_analysis_manifest(payload)
                st.session_state["active_job_id"] = manifest["id"]
                st.success("Job created. Submit it below now or continue later from Results & Downloads.")
                st.json(payload)

        if st.session_state.get("active_job_id"):
            if st.button("Submit job", use_container_width=True):
                run_analysis_manifest(st.session_state["active_job_id"])

    with s2:
        st.markdown("#### AOI Selection Map")
        st.caption("Use the map to draw, upload, or review your area of interest before submitting the job.")
        basemap = st.selectbox("Basemap", ["OpenStreetMap", "Esri Satellite", "CartoDB Positron"], key="rna_basemap")
        map_lat = lat if lat is not None else 0.0
        map_lon = lon if lon is not None else 25.0
        m = folium.Map(location=[map_lat, map_lon], zoom_start=4, tiles=None)
        if basemap == "OpenStreetMap":
            folium.TileLayer("OpenStreetMap", name="Street").add_to(m)
        elif basemap == "Esri Satellite":
            folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
        else:
            folium.TileLayer("CartoDB positron", name="Light").add_to(m)
        Draw(export=True).add_to(m)
        folium.LayerControl().add_to(m)
        out = st_folium(m, height=540, use_container_width=True, key="rna_map")
        if out and out.get("last_active_drawing"):
            st.success("AOI captured from interactive map.")
            st.json(out["last_active_drawing"])
        st.markdown('<div class="note-box"><strong>Resume-enabled workflow:</strong> This demo stores job settings and step-level progress locally so interrupted jobs can continue from the last completed step. If extraction stops unexpectedly, users do not need to restart from the beginning. Full live processing in production still requires a backend worker service.</div>', unsafe_allow_html=True)
    render_ai_box("Run New Analysis", columns=["temperature", "rainfall", "flood", "population", "health", "infrastructure"], date_field="date")
    st.markdown("#### Earth Engine initialisation block")
    st.code("""try:
    ee.Initialize(project='ee-reachprojectlshtm')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='ee-reachprojectlshtm')""", language="python")

def documentation_page():
    st.title("Guides & Documentation")
    st.markdown('<div class="note-box"><strong>Platform structure:</strong> the app is organised around two main pathways. <strong>Pathway 1 · Data Analysis and Visualisation</strong> is for exploring built-in REACH Project datasets or uploaded data through figures, statistics, AI-guided analysis, and export. <strong>Pathway 2 · Create a new data job for any region in the world</strong> is for defining a new AOI, selecting variables, dates, temporal resolution, and outputs, and creating a job request for downstream processing.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Platform overview", "Pathway 1 · Data Analysis and Visualisation", "Pathway 2 · Create Data Job", "Flood", "Heatwaves", "Multi-Hazard", "Custom Dataset Explorer"])
    with tabs[0]:
        st.markdown("""
### Main purpose of the platform
The platform supports two complementary functions:

1. **Data Analysis and Visualisation** for built-in REACH Project datasets and user-uploaded datasets.
2. **Create a new data job** for any region in the world using uploaded AOIs, map drawing, predefined areas, or coordinates and buffer.

### Analysis suite available inside Explore
- Summary
- Correlation
- Regression
- Time Series
- Spatial
- Advanced
- AI-Guided Analysis
- Figure & Data Export

The figure export area also supports building multi-panel layouts such as 1x2, 2x2, 3x3, 4x4, 5x5, or custom rows × columns.
""")
        render_analysis_suite_chips()
    with tabs[1]:
        st.markdown("""
### Pathway 1 · Data Analysis and Visualisation
Use this pathway to:
- open a built-in REACH Project dataset
- upload your own CSV or ZIP dataset
- visualise and compare data without coding
- run statistical analysis
- receive AI-guided support in plain language
- export publication-ready outputs

Open any module and go to **Explore** to access the full analysis suite.

If a health dataset has been loaded on the **Health** page, the **Correlation** and **Regression** tabs can also be used for linked climate–health modelling, where climate variables act as predictors and DHS or other health variables act as outcomes.
""")
    with tabs[2]:
        st.markdown("""
### Pathway 2 · Create a new data job for any region in the world
Use this pathway to:
- choose a country and region / spatial unit type
- define an AOI with an uploaded boundary file, map drawing, coordinates and buffer, or predefined area
- choose climate, hazard, environmental, population, infrastructure, and health variables
- set the time period and temporal resolution
- request tables, risk layers, filtered CSV, and summary outputs

This pathway is designed as the bridge to larger-scale backend processing.
""")
    files = ["brazil_flood.md", "brazil_heat.md", "zambia_multihazard.md", "custom_dataset.md"]
    for tab, fn in zip(tabs[3:], files):
        with tab:
            st.markdown(safe_read_text(FACTSHEETS_DIR / fn))


def downloads_page():
    st.title("Results & Downloads")
    st.markdown("Use this page to review completed exports and guided-analysis jobs. Finished files remain visible here after completion so users do not need to search for them.")
    export_items = list_manifests("export")
    job_items = list_manifests("job")
    t1, t2 = st.tabs(["Prepared downloads", "Guided-analysis jobs"])
    with t1:
        if not export_items:
            st.info("No prepared exports yet. Generate a filtered CSV or PDF from one of the workflow pages.")
        for item in export_items:
            render_status_box(item.get("title", "Prepared export"), item.get("status", "queued"), item.get("message", ""))
            if item.get("status") == "completed":
                render_export_download_buttons(item)
            st.caption(f"Updated: {item.get('updated_at', '')}")
    with t2:
        if not job_items:
            st.info("No guided-analysis jobs found yet.")
        for item in job_items:
            completed = sum(1 for u in item.get("units", []) if u.get("status") == "completed")
            total = len(item.get("units", []))
            render_status_box(item.get("title", "Analysis job"), item.get("status", "queued"), item.get("message", ""), progress=(completed / total if total else 0))
            if item.get("job_spec_path") and Path(item["job_spec_path"]).exists():
                st.download_button("Download job specification JSON", Path(item["job_spec_path"]).read_bytes(), file_name=Path(item["job_spec_path"]).name, mime="application/json", key=f"jobspec_{item['id']}")
            if item.get("summary_path") and Path(item["summary_path"]).exists():
                st.download_button("Download job summary", Path(item["summary_path"]).read_bytes(), file_name=Path(item["summary_path"]).name, mime="text/plain", key=f"jobsum_{item['id']}")
            if item.get("status") in {"queued", "running"}:
                if st.button(f"Resume {item['id']}", key=f"resume_{item['id']}"):
                    run_analysis_manifest(item["id"])
            st.caption(f"Updated: {item.get('updated_at', '')}")


def author_page():
    st.title("About / Credits")
    st.markdown(safe_read_text(BASE_DIR / "author_credit.md"))
    st.markdown('<div class="note-box"><strong>Scope note:</strong> this release focuses on the public-facing analytics platform, demo workflows, upload-based exploration, persistent downloads, a checkpoint-ready guided-analysis workflow, a DHS health-data beta page, and documentation. Full backend engineering and live processing integration are still a later development phase.</div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## Navigate")
    st.caption("Pathway 1: Data Analysis and Visualisation · Pathway 2: Create Data Job")
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"
    for page in PAGES:
        wrapper = "nav-active" if st.session_state["page"] == page else "nav-wrap"
        label = DISPLAY_PAGE_LABELS.get(page, page)
        st.markdown(f'<div class="{wrapper}">', unsafe_allow_html=True)
        if st.button(label, use_container_width=True, key=f"nav_{page}"):
            st.session_state["page"] = page
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

page = st.session_state["page"]
if page == "Home":
    render_home()
elif page in ["Brazil Flood", "Brazil Heat", "Zambia Multi-Hazard", "Custom Dataset Explorer"]:
    workflow_page(page)
elif page == "Health":
    render_health_page()
elif page == "Run New Analysis":
    run_new_analysis_page()
elif page == "Guides & Documentation":
    documentation_page()
elif page == "Results & Downloads":
    downloads_page()
elif page == "About / Credits":
    author_page()
elif page == "Admin":
    render_admin_page()