
from pathlib import Path
from io import BytesIO
import json, zipfile, textwrap
import folium
from folium.plugins import Draw
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from streamlit_folium import st_folium

st.set_page_config(page_title="Climate–Health and Health Systems Analytics Platform", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

COUNTRIES = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon', 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo', 'Democratic Republic of the Congo', 'Costa Rica', 'Côte d’Ivoire', 'Croatia', 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius', 'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Korea', 'North Macedonia', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Syria', 'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe', 'Custom / user-defined region']

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1550px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(243,247,255,0.98) 0%, rgba(234,244,255,0.98) 48%, rgba(244,239,255,0.98) 100%);}
.hero {background: linear-gradient(120deg, #0b132b 0%, #1d4ed8 35%, #6d28d9 70%, #c026d3 100%); border-radius: 24px; padding: 1.6rem 1.4rem; color: white; box-shadow: 0 14px 34px rgba(15,23,42,0.18); margin-bottom: 1rem;}
.hero h1 {margin: 0 0 0.25rem 0; font-size: 2.35rem;}
.hero p {margin: 0.2rem 0;}
.white-card, .metric-card, .workflow-card {background: white; border: 1px solid #e5e7eb; border-radius: 18px; box-shadow: 0 6px 16px rgba(15,23,42,0.05);}
.white-card {padding: 1rem;}
.metric-card {padding: 0.9rem; text-align: center;}
.workflow-card {min-height: 210px; padding: 1.05rem;}
.flood-top {border-top: 7px solid #2563eb;}
.heat-top {border-top: 7px solid #ea580c;}
.multi-top {border-top: 7px solid #7c3aed;}
.custom-top {border-top: 7px solid #0f766e;}
.info-chip {display: inline-block; padding: 0.42rem 0.75rem; margin: 0.18rem 0.28rem 0.18rem 0; border-radius: 999px; border: 1px solid #d8e1f0; background: white; font-size: 0.92rem;}
.note-box {border: 1px solid #dbe4ff; border-radius: 14px; background: linear-gradient(90deg, #eef2ff 0%, #f5f3ff 100%); padding: 0.9rem 1rem;}
.upload-box {border: 1px dashed #c8d5ec; border-radius: 16px; background: #fbfdff; padding: 0.9rem 1rem;}
.ai-box {border-radius: 16px; background: linear-gradient(135deg, #ecfeff 0%, #eef2ff 100%); border: 1px solid #c7d2fe; padding: 1rem;}
.section-banner {border-radius: 18px; padding: 0.95rem 1rem; color: white; margin-bottom: 0.8rem; box-shadow: 0 8px 22px rgba(15,23,42,0.08);}
.flood-banner {background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%);}
.heat-banner {background: linear-gradient(135deg, #c2410c 0%, #fb923c 100%);}
.multi-banner {background: linear-gradient(135deg, #6d28d9 0%, #a78bfa 100%);}
.custom-banner {background: linear-gradient(135deg, #0f766e 0%, #2dd4bf 100%);}
.small-muted {color: #475569; font-size: 0.93rem;}
.nav-wrap button {width: 100%; border-radius: 14px !important; padding: 0.68rem 0.78rem !important; margin-bottom: 0.22rem !important; border: 1px solid rgba(148,163,184,0.35) !important; background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(239,246,255,0.98) 100%) !important; color: #1e293b !important; font-weight: 600 !important;}
.nav-active button {width: 100%; border-radius: 14px !important; padding: 0.68rem 0.78rem !important; margin-bottom: 0.22rem !important; border: 0 !important; background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%) !important; color: white !important; font-weight: 700 !important;}
</style>
""", unsafe_allow_html=True)

HOME_TITLE = "Climate–Health and Health Systems Analytics Platform"
HOME_SUBTITLE = "An interactive multi-hazard research and decision-support platform for climate risk, health, and health systems analysis."
HOME_AUTHOR = "Developed by Sisay Debele"
HOME_AFFILIATION = "REACH Project | London School of Hygiene & Tropical Medicine"
HOME_DESCRIPTION = "This platform brings together climate, hazard, exposure, risk, and health systems analytics in one integrated environment. It supports the exploration of flood, heat, drought, and multi-hazard patterns across Brazil and Zambia through reproducible workflows, interactive visualisation, workflow factsheets, and downloadable outputs for research, policy, and operational use."
HOME_FEATURES = [
    "Interactive climate, hazard, exposure, risk, and susceptibility analytics",
    "Flood, heatwaves, and multi-hazard modules in one platform",
    "Workflow factsheets, variable dictionaries, and documentation",
    "Validation plots, trends, comparative visualisations, and mixed-axis charts",
    "Downloadable filtered data, figures, summary tables, and narrative PDF notes",
]
PAGES = ["Home","Brazil Flood","Brazil Heat","Zambia Multi-Hazard","Custom Dataset Explorer","Run New Analysis","Documentation","Downloads","Author / Credits"]

DISPLAY_PAGE_LABELS = {
    "Home": "Home",
    "Brazil Flood": "Flood",
    "Brazil Heat": "Heatwaves",
    "Zambia Multi-Hazard": "Multi-Hazard",
    "Custom Dataset Explorer": "Custom Dataset Explorer",
    "Run New Analysis": "Run New Analysis",
    "Documentation": "Documentation",
    "Downloads": "Downloads",
    "Author / Credits": "Author / Credits",
}
WORKFLOW_META = {
    "Brazil Flood": {"upload_label":"Upload Brazil Flood CSV or ZIP of CSVs","summary":"Flood analytics for exposure, impacts, and rainfall context across case-study or uploaded datasets.","workflow_file":"brazil_flood.md","metadata_file":"brazil_flood.json","area_candidates":["municipality","NM_MUN","state","CD_MUN"],"date_candidates":["date","Date","timestamp"],"year_candidates":["year","Year"],"month_candidates":["month","Month"],"banner_class":"flood-banner","card_class":"flood-top"},
    "Brazil Heat": {"upload_label":"Upload Brazil Heat CSV or ZIP of CSVs","summary":"Heatwaves analytics for temperature, humidity, seasonality, and climate-health interpretation across case-study or uploaded datasets.","workflow_file":"brazil_heat.md","metadata_file":"brazil_heat.json","area_candidates":["municipality","NM_MUN","CD_MUN"],"date_candidates":["date","Date","timestamp"],"year_candidates":["year","Year"],"month_candidates":["month","Month"],"banner_class":"heat-banner","card_class":"heat-top"},
    "Zambia Multi-Hazard": {"upload_label":"Upload Zambia Multi-Hazard CSV or ZIP of CSVs","summary":"Integrated multi-hazard analytics for flood, drought, heatwaves, compound events, and related indicators.","workflow_file":"zambia_multihazard.md","metadata_file":"zambia_multihazard.json","area_candidates":["DISTRICT","district","DIST_CODE","district_id"],"date_candidates":["date","Date","timestamp"],"year_candidates":["year","Year"],"month_candidates":["month","Month"],"banner_class":"multi-banner","card_class":"multi-top"},
    "Custom Dataset Explorer": {"upload_label":"Upload custom CSV or ZIP of CSVs","summary":"Flexible upload, visualisation, filtering, statistics, and download environment for user datasets and other countries.","workflow_file":"custom_dataset.md","metadata_file":"custom_dataset.json","area_candidates":["country","state","district","municipality","location","site"],"date_candidates":["date","Date","timestamp","datetime"],"year_candidates":["year","Year"],"month_candidates":["month","Month"],"banner_class":"custom-banner","card_class":"custom-top"},
}
AI_QUICK_GUIDE = {
    "Which plot should I use?":"Use line plots for time series, grouped bar charts for comparing places or months, histograms for distributions, scatter plots for relationships, pie charts for composition, and heatmaps for correlations.",
    "How do I compare Tmax, Tmin, and Tmean together?":"Choose all three variables in the Explore tab, then select Line or Bar plot. The app will place them on one figure with different colours.",
    "When should I use a secondary y-axis?":"Use a secondary y-axis when one variable has a much larger magnitude or different unit than the others, for example exchange flux versus water level.",
    "What does SPI mean?":"SPI is the Standardized Precipitation Index. Negative values usually indicate drier-than-normal conditions, while positive values indicate wetter-than-normal conditions.",
    "What does MH_binary_sum mean?":"MH_binary_sum usually represents how many hazard classes are active or elevated at the same time in the multi-hazard workflow.",
}

def safe_read_text(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else "File not found."

def load_metadata(filename):
    p = Path("metadata") / filename
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

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

def detect_area_field(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    return obj_cols[0] if obj_cols else None

def detect_date_field(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower():
            return c
    return None

def prep_dataframe(df, meta):
    d = df.copy()
    date_field = detect_date_field(d, meta["date_candidates"])
    if date_field:
        d[date_field] = pd.to_datetime(d[date_field], errors="coerce")
    for c in meta["year_candidates"] + meta["month_candidates"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d, date_field

def numeric_columns(df):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

def categorical_columns(df):
    return [c for c in df.columns if df[c].dtype == "object"]

def build_period_column(df, date_field, aggregation):
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
    year_col = next((c for c in ["year","Year"] if c in d.columns), None)
    month_col = next((c for c in ["month","Month"] if c in d.columns), None)
    if year_col:
        if aggregation == "Yearly" or month_col is None:
            d["_period"] = d[year_col].astype("Int64").astype(str)
        else:
            d["_period"] = d[year_col].astype("Int64").astype(str) + "-" + d[month_col].astype("Int64").astype(str).str.zfill(2)
    else:
        d["_period"] = np.arange(len(d)).astype(str)
    return d

def aggregate_multi(df, value_cols, stat):
    fn = {"Mean":"mean","Sum":"sum","Max":"max","Min":"min","Median":"median"}[stat]
    return df.groupby("_period")[value_cols].agg(fn).reset_index()

def interpret_dataset(d, selected_vars, aggregation, statistic, secondary_vars=None):
    msgs = []
    for v in selected_vars[:4]:
        s = pd.to_numeric(d[v], errors="coerce")
        if s.dropna().empty:
            continue
        mean_v = s.mean(); min_v = s.min(); max_v = s.max()
        trend = "has limited observations"
        if len(s.dropna()) > 3:
            y = s.dropna().values
            slope = np.polyfit(np.arange(len(y)), y, 1)[0]
            trend = "shows an increasing pattern" if slope > 0 else ("shows a decreasing pattern" if slope < 0 else "is broadly stable")
        msgs.append(f"{v}: mean={mean_v:.3f}, min={min_v:.3f}, max={max_v:.3f}, and {trend} across the selected {aggregation.lower()} period.")
    take_home = "The selected variables help describe climate, hazard, exposure, or risk conditions in the filtered dataset."
    if any("SPI" in v for v in selected_vars):
        take_home += " SPI values below zero generally indicate drier-than-normal conditions."
    if any("RX" in v for v in selected_vars):
        take_home += " RX indicators describe heavy rainfall intensity and can point to short-duration precipitation extremes."
    if secondary_vars:
        take_home += " A secondary y-axis was used because at least one selected variable has a different magnitude or unit."
    caution = "Interpretation depends on data quality, workflow assumptions, selected aggregation, and the completeness of uploaded fields."
    return msgs, take_home, caution

def make_pdf_bytes(title, lines):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    bio = BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    _, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16); c.drawString(50, y, title); y -= 24
    c.setFont("Helvetica", 10)
    for line in lines:
        for part in textwrap.wrap(str(line), width=96):
            if y < 52:
                c.showPage(); y = height - 50; c.setFont("Helvetica", 10)
            c.drawString(50, y, part); y -= 13
    c.save(); bio.seek(0)
    return bio.read()

def dynamic_ai_suggestion(plot_type, selected_vars, aggregation, use_secondary, secondary_vars):
    notes = []
    if plot_type == "Line":
        notes.append("Line plot is suitable for showing change over time.")
    if plot_type == "Bar" and aggregation in ["Monthly","Yearly"]:
        notes.append("Grouped bar charts work well for comparing seasonal or annual totals across selected variables.")
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
    return notes

def render_ai_box(workflow_name=None, plot_type=None, selected_vars=None, aggregation=None, use_secondary=False, secondary_vars=None):
    st.markdown("#### AI assistance")
    st.markdown('<div class="ai-box">This assistant helps non-technical users choose variables, plot types, aggregation level, secondary-axis logic, and interpretation pathways.</div>', unsafe_allow_html=True)
    prompt = st.selectbox("Quick guidance", ["None"] + list(AI_QUICK_GUIDE.keys()), key=f"ai_{workflow_name or 'home'}")
    if prompt != "None":
        st.info(AI_QUICK_GUIDE[prompt])
    if selected_vars:
        st.markdown("**Live suggestions**")
        for note in dynamic_ai_suggestion(plot_type, selected_vars, aggregation, use_secondary, secondary_vars or []):
            st.write("- " + note)

def render_hero():
    st.markdown(f'<div class="hero"><h1>{HOME_TITLE}</h1><p>{HOME_SUBTITLE}</p><p><strong>{HOME_AUTHOR}</strong></p><p>{HOME_AFFILIATION}</p></div>', unsafe_allow_html=True)
    l1, l2, txt = st.columns([1.1,1.1,4])
    with l1:
        if Path("LSHTM_LOGO.png").exists():
            st.image("LSHTM_LOGO.png", use_container_width=True)
    with l2:
        if Path("REACH_PROJECT_LOGO.png").exists():
            st.image("REACH_PROJECT_LOGO.png", use_container_width=True)
    with txt:
        st.markdown(HOME_DESCRIPTION)

def render_home():
    render_hero()
    st.markdown("### What this platform offers")
    st.markdown("".join(f'<span class="info-chip">{x}</span>' for x in HOME_FEATURES), unsafe_allow_html=True)
    st.markdown("### Core analytics modules")
    cols = st.columns(4)
    cards = [
        ("Brazil Flood","Flood module: explore flood extent, rainfall context, exposure, infrastructure, and health facility indicators using case-study or uploaded datasets."),
        ("Brazil Heat","Heatwaves module: explore temperature, humidity, seasonality, long-term trends, and climate-health analytics with case-study or uploaded datasets."),
        ("Zambia Multi-Hazard","Multi-Hazard module: explore flood, drought, and heatwave indicators, compound events, risk classes, and susceptibility outputs."),
        ("Custom Dataset Explorer","Upload and explore datasets from any country or project with flexible variable selection, plots, multi-axis support, and downloads.")
    ]
    for col, (name, desc) in zip(cols, cards):
        meta = WORKFLOW_META[name]
        with col:
            st.markdown(f'<div class="workflow-card {meta["card_class"]}"><h4>{("Flood" if name=="Brazil Flood" else "Heatwaves" if name=="Brazil Heat" else "Multi-Hazard" if name=="Zambia Multi-Hazard" else name)}</h4><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)
            home_label = ("Flood" if name=="Brazil Flood" else "Heatwaves" if name=="Brazil Heat" else "Multi-Hazard" if name=="Zambia Multi-Hazard" else name)
            if st.button(f"Open {home_label}", use_container_width=True, key=f"home_{name}"):
                st.session_state["page"] = name; st.rerun()
    st.markdown("### How to use this platform")
    st.markdown("1. Choose a workflow or open the custom explorer.\n2. Upload a CSV or ZIP dataset, or go to Run New Analysis for AOI-based extraction planning.\n3. Select place, dates, variables, plot type, aggregation, and optional secondary axis.\n4. Explore line plots, grouped bar charts, histograms, box plots, scatter plots, pie charts, heatmaps, and summary statistics.\n5. Open the factsheet to understand what the workflow is about, what it does, who can use it, and the main limitations.\n6. Download filtered CSV and narrative PDF outputs.")
    render_ai_box("Home")
    st.markdown('<div class="note-box"><strong>Version 10:</strong> this is the final pre-backend public release. It presents generic hazard modules on the homepage and sidebar, while Brazil and Zambia are positioned as case-study examples inside the workflow pages and documentation. It supports demo datasets, user uploads, analysis, narrative PDF download, and AOI-based job specification before later backend engineering.</div>', unsafe_allow_html=True)

def render_upload_block(page_name, meta):
    st.markdown("#### Data input")
    source = st.radio(
        "Choose data source",
        ["Use demo dataset", "Upload my own CSV or ZIP"],
        key=f"source_{page_name}",
        horizontal=False,
    )

    demo_map = {
        "Brazil Flood": [
            ("Recife flood showcase", "demo_brazil_flood.csv"),
            ("Alternative flood showcase", "demo_brazil_flood_2.csv"),
        ],
        "Brazil Heat": [
            ("Brazil heat showcase", "demo_brazil_heat.csv"),
            ("Alternative heat showcase", "demo_brazil_heat_2.csv"),
        ],
        "Zambia Multi-Hazard": [
            ("Zambia multi-hazard showcase", "demo_zambia_multihazard.csv"),
            ("Zambia monthly showcase", "demo_zambia_multihazard_month.csv"),
        ],
        "Custom Dataset Explorer": [],
    }

    if source == "Use demo dataset":
        demos = demo_map.get(page_name, [])
        if demos:
            demo_label = st.selectbox(
                "Choose demo file",
                [label for label, _ in demos],
                key=f"demo_choice_{page_name}"
            )
            demo_name = dict(demos).get(demo_label)
            demo_path = Path("sample_data") / demo_name
            if demo_path.exists():
                demo_df = pd.read_csv(demo_path)
                st.session_state[f"data_{page_name}"] = demo_df
                st.success(f"Loaded demo dataset: {demo_name} ({len(demo_df):,} rows)")
                st.markdown(
                    '<div class="note-box"><strong>Demo mode:</strong> this workflow is using a built-in showcase dataset from <code>sample_data/</code>. Brazil and Zambia are presented as case-study examples rather than the platform identity.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning(f"Demo dataset not found: {demo_name}. Add it to the sample_data folder or switch to upload mode.")
        else:
            st.info("No built-in demo dataset is configured for this page yet. Use upload mode.")
        return st.session_state.get(f"data_{page_name}")

    st.markdown(
        f'<div class="upload-box"><strong>{meta["upload_label"]}</strong><br><span class="small-muted">Accepted: single CSV or ZIP containing one or more CSV files.</span></div>',
        unsafe_allow_html=True
    )
    uploaded = st.file_uploader(meta["upload_label"], type=["csv","zip"], key=f"upload_{page_name}")
    if uploaded is not None:
        parsed = parse_uploaded_table(uploaded)
        if parsed is not None:
            st.session_state[f"data_{page_name}"] = parsed
            st.success(f"Loaded {len(parsed):,} rows from {uploaded.name}")
        else:
            st.error("No usable CSV file was found.")
    return st.session_state.get(f"data_{page_name}")

def render_variable_dictionary(meta):
    md = load_metadata(meta["metadata_file"])
    rows = [{"variable":x.get("name",""),"label":x.get("label",""),"unit":x.get("unit",""),"description":x.get("description","")} for x in md.get("variables",[])]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No variable dictionary found.")

def build_secondary_axis_figure(source, xcol, selected_vars, secondary_vars):
    fig = go.Figure()
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24
    for i, var in enumerate(selected_vars):
        fig.add_trace(go.Scatter(x=source[xcol], y=source[var], mode="lines+markers", name=var, yaxis="y2" if var in secondary_vars else "y1", line=dict(color=palette[i % len(palette)], width=2)))
    fig.update_layout(yaxis=dict(title="Primary axis"), yaxis2=dict(title="Secondary axis", overlaying="y", side="right"), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), height=560, margin=dict(l=40, r=40, t=40, b=40))
    return fig

def render_explore(df, meta, page_name):
    d, date_field = prep_dataframe(df, meta)
    area_field = detect_area_field(d, meta["area_candidates"])
    num_cols = numeric_columns(d)
    if not num_cols:
        st.warning("No numeric columns were found in this dataset."); st.dataframe(d.head(100), use_container_width=True); return
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        area_value = "All"
        if area_field:
            area_value = st.selectbox("Area", ["All"] + sorted(d[area_field].dropna().astype(str).unique().tolist()), key=f"area_{page_name}")
    with f2:
        selected_vars = st.multiselect("Variables", num_cols, default=num_cols[:min(3, len(num_cols))], key=f"vars_{page_name}")
    with f3:
        aggregation = st.selectbox("Aggregation", ["Raw","Daily","Weekly","Monthly","Yearly"], index=3, key=f"agg_{page_name}")
    with f4:
        statistic = st.selectbox("Statistic", ["Mean","Sum","Max","Min","Median"], key=f"stat_{page_name}")
    if area_field and area_value != "All":
        d = d[d[area_field].astype(str) == area_value].copy()
    if date_field and date_field in d.columns and d[date_field].notna().any():
        dmin = d[date_field].min().date(); dmax = d[date_field].max().date()
        dr = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax, key=f"dr_{page_name}")
        if isinstance(dr, tuple) and len(dr) == 2:
            d = d[(d[date_field].dt.date >= dr[0]) & (d[date_field].dt.date <= dr[1])].copy()
    if not selected_vars:
        st.info("Choose at least one variable."); return
    d = build_period_column(d, date_field, aggregation)
    aggregated = aggregate_multi(d, selected_vars, statistic) if aggregation != "Raw" else d.copy()
    xcol = "_period" if aggregation != "Raw" else (date_field or "_period")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        plot_type = st.selectbox("Plot type", ["Line","Bar","Box","Histogram","Scatter","Heatmap","Pie"], key=f"plot_{page_name}")
    with p2:
        group_col = st.selectbox("Group / category", ["None"] + [c for c in categorical_columns(d) if c != area_field], key=f"group_{page_name}")
    with p3:
        scatter_y = st.selectbox("Scatter Y variable", ["None"] + [c for c in num_cols if c not in selected_vars[:1]], key=f"scatter_{page_name}")
    with p4:
        use_secondary = st.checkbox("Use secondary y-axis", value=False, key=f"sec_{page_name}")
    secondary_vars = []
    if use_secondary and plot_type == "Line":
        secondary_vars = st.multiselect("Variables on secondary axis", selected_vars, default=selected_vars[-1:] if len(selected_vars) > 1 else [], key=f"secvars_{page_name}")
    render_ai_box(page_name, plot_type, selected_vars, aggregation, use_secondary, secondary_vars)
    fig = None
    if plot_type == "Line":
        source = aggregated if aggregation != "Raw" else d
        if use_secondary and secondary_vars:
            fig = build_secondary_axis_figure(source, xcol, selected_vars, secondary_vars)
        else:
            long_df = source.melt(id_vars=[xcol], value_vars=selected_vars, var_name="variable", value_name="value")
            fig = px.line(long_df, x=xcol, y="value", color="variable", markers=(aggregation != "Raw"), height=560)
    elif plot_type == "Bar":
        source = aggregated if aggregation != "Raw" else d
        long_df = source.melt(id_vars=[xcol], value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.bar(long_df, x=xcol, y="value", color="variable", barmode="group", height=560)
    elif plot_type == "Box":
        long_df = d.melt(value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.box(long_df, x="variable", y="value", color="variable", height=560)
    elif plot_type == "Histogram":
        long_df = d.melt(value_vars=selected_vars, var_name="variable", value_name="value")
        fig = px.histogram(long_df, x="value", color="variable", nbins=40, barmode="overlay", height=560)
    elif plot_type == "Scatter":
        xvar = selected_vars[0]; yvar = scatter_y if scatter_y != "None" else (selected_vars[1] if len(selected_vars) > 1 else None)
        if yvar is None:
            st.info("Choose at least two variables for scatter plot.")
        else:
            fig = px.scatter(d, x=xvar, y=yvar, color=group_col if group_col != "None" else None, trendline="ols", height=560)
    elif plot_type == "Heatmap":
        corr_df = d[selected_vars].corr(numeric_only=True)
        fig = px.imshow(corr_df, text_auto=True, aspect="auto", height=560)
    elif plot_type == "Pie":
        if group_col == "None":
            st.info("Choose a category / group field for pie chart.")
        else:
            pie_var = selected_vars[0]; pie_df = d.groupby(group_col, as_index=False)[pie_var].sum(); fig = px.pie(pie_df, names=group_col, values=pie_var, height=560)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    interpret_lines, take_home, caution = interpret_dataset(aggregated if aggregation != "Raw" else d, selected_vars, aggregation, statistic, secondary_vars)
    st.markdown("#### Interpretation")
    for line in interpret_lines:
        st.write("- " + line)
    st.success("Take-home message: " + take_home)
    st.caption("Caution: " + caution)
    t1, t2, t3 = st.tabs(["Summary statistics","Grouped statistics","Preview table"])
    with t1:
        st.dataframe(d[selected_vars].describe().T, use_container_width=True)
    with t2:
        if group_col != "None":
            frames = []
            for col in selected_vars:
                g = d.groupby(group_col)[col].agg(["count","mean","median","min","max"]).reset_index(); g.insert(1, "variable", col); frames.append(g)
            st.dataframe(pd.concat(frames, ignore_index=True), use_container_width=True)
        else:
            st.info("Choose a group / category field to create grouped summaries.")
    with t3:
        preview_cols = [c for c in [area_field, date_field] if c and c in d.columns] + selected_vars
        st.dataframe(d[preview_cols].head(300) if preview_cols else d.head(300), use_container_width=True)
    csv_bytes = d.to_csv(index=False).encode("utf-8")
    pdf_lines = [f"Workflow: {page_name}", f"Rows after filtering: {len(d)}", f"Area field: {area_field}", f"Selected area: {area_value if area_field else 'All'}", f"Date field: {date_field}", f"Selected variables: {', '.join(selected_vars)}", f"Aggregation: {aggregation}", f"Statistic: {statistic}", f"Secondary axis variables: {', '.join(secondary_vars) if secondary_vars else 'None'}", "", "Interpretation:", *interpret_lines, "", "Take-home message:", take_home, "", "Caution:", caution, "", d[selected_vars].describe().to_string()]
    pdf_bytes = make_pdf_bytes(f"{page_name} summary", pdf_lines)
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("Download filtered CSV", csv_bytes, file_name=f"{page_name.lower().replace(' ','_')}_filtered.csv", mime="text/csv", use_container_width=True)
    with d2:
        st.download_button("Download narrative PDF", pdf_bytes, file_name=f"{page_name.lower().replace(' ','_')}_summary.pdf", mime="application/pdf", use_container_width=True)

def render_maps_for_explorer(page_name):
    st.markdown("#### Spatial view")
    c1, c2, c3 = st.columns(3)
    with c1:
        basemap = st.selectbox("Basemap", ["OpenStreetMap","Esri Satellite","CartoDB Positron"], key=f"bm_{page_name}")
    with c2:
        lat = st.number_input("Center latitude", value=0.0, format="%.6f", key=f"lat_{page_name}")
    with c3:
        lon = st.number_input("Center longitude", value=25.0, format="%.6f", key=f"lon_{page_name}")
    zoom = st.slider("Zoom", 2, 12, 5, key=f"zoom_{page_name}")
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)
    if basemap == "OpenStreetMap":
        folium.TileLayer("OpenStreetMap", name="Street").add_to(m)
    elif basemap == "Esri Satellite":
        folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
    else:
        folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    Draw(export=True).add_to(m); folium.LayerControl().add_to(m)
    out = st_folium(m, height=560, use_container_width=True, key=f"map_{page_name}")
    if out and out.get("last_active_drawing"):
        st.success("Area of interest captured from the map."); st.json(out["last_active_drawing"])

def workflow_page(page_name):
    meta = WORKFLOW_META[page_name]
    banner_title = ("Flood" if page_name=="Brazil Flood" else "Heatwaves" if page_name=="Brazil Heat" else "Multi-Hazard" if page_name=="Zambia Multi-Hazard" else page_name)
    case_note = ("Case study dataset: Brazil" if page_name in ["Brazil Flood","Brazil Heat"] else "Case study dataset: Zambia" if page_name=="Zambia Multi-Hazard" else "Global/custom upload module")
    st.markdown(f'<div class="section-banner {meta["banner_class"]}"><h2 style="margin:0;">{banner_title}</h2><div>{meta["summary"]}<br><strong>{case_note}</strong></div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.12,3.3], gap="large")
    with left:
        df = render_upload_block(page_name, meta)
    with right:
        if df is None:
            st.markdown('<div class="white-card"><h4 style="margin-top:0;">Ready to explore</h4><p>Choose a demo dataset or upload a CSV/ZIP file to unlock filters, plots, summary tables, factsheets, variable dictionary, downloads, and AI-assisted interpretation.</p></div>', unsafe_allow_html=True)
        else:
            d, _ = prep_dataframe(df, meta)
            area_field = detect_area_field(d, meta["area_candidates"])
            year_count = 0
            for yc in meta["year_candidates"]:
                if yc in d.columns:
                    year_count = int(pd.to_numeric(d[yc], errors="coerce").dropna().nunique()); break
            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="metric-card"><h3>{len(d):,}</h3><div class="small-muted">Rows</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><h3>{int(d[area_field].astype(str).nunique()) if area_field else 0}</h3><div class="small-muted">Areas</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><h3>{year_count}</h3><div class="small-muted">Years</div></div>', unsafe_allow_html=True)
    tabs = st.tabs(["Overview","Explore","Spatial view","Factsheet","Variable dictionary","Downloads"])
    with tabs[0]:
        st.markdown(safe_read_text(Path("factsheets") / meta["workflow_file"]))
        if df is not None:
            st.markdown("#### Data preview"); st.dataframe(df.head(100), use_container_width=True)
    with tabs[1]:
        if df is None:
            st.info("Upload a CSV or ZIP first.")
        else:
            render_explore(df, meta, page_name)
    with tabs[2]:
        render_maps_for_explorer(page_name)
    with tabs[3]:
        st.markdown(safe_read_text(Path("factsheets") / meta["workflow_file"]))
    with tabs[4]:
        render_variable_dictionary(meta)
    with tabs[5]:
        st.markdown("Downloads are created in the Explore tab after you choose variables and apply filters.")

def run_new_analysis_page():
    st.markdown('<div class="section-banner multi-banner"><h2 style="margin:0;">Run New Analysis</h2><div>AOI definition, variable selection, date range, risk setup, job specification, and future live Earth Engine / Python backend integration.</div></div>', unsafe_allow_html=True)
    s1, s2 = st.columns([1.1,2.1], gap="large")
    with s1:
        st.markdown("#### Analysis settings")
        country = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index("Brazil"))
        hazard = st.selectbox("Hazard", ["Flood","Heat","Multi-Hazard"])
        input_mode = st.selectbox("AOI method", ["Predefined area","Shapefile ZIP","GeoJSON","Lat/Lon","Draw ROI"])
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
        variables = st.multiselect("Variables to extract", ["Tmax","Tmin","Tmean","RH","SPI","SSI","RX1day","RX5day","Flood area","Population exposed","Health facility exposure"], default=["Tmax","RX1day"])
        outputs = st.multiselect("Requested outputs", ["Summary table","Spatial risk layer","Filtered CSV","Risk classes","PDF summary"], default=["Summary table","Spatial risk layer","Risk classes"])
        gee_project = st.text_input("Earth Engine project", "ee-reachprojectlshtm")
        st.file_uploader("Upload shapefile ZIP", type=["zip"], key="rna_shp")
        st.file_uploader("Upload GeoJSON", type=["geojson","json"], key="rna_geo")
        lat = st.number_input("Latitude", value=0.0, format="%.6f", key="rna_lat")
        lon = st.number_input("Longitude", value=25.0, format="%.6f", key="rna_lon")
        buffer_km = st.number_input("Buffer radius (km)", value=10.0, min_value=0.0, key="rna_buffer")
    with s2:
        st.markdown("#### AOI map")
        basemap = st.selectbox("Basemap", ["OpenStreetMap","Esri Satellite","CartoDB Positron"], key="rna_basemap")
        m = folium.Map(location=[lat, lon], zoom_start=4, tiles=None)
        if basemap == "OpenStreetMap":
            folium.TileLayer("OpenStreetMap", name="Street").add_to(m)
        elif basemap == "Esri Satellite":
            folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
        else:
            folium.TileLayer("CartoDB positron", name="Light").add_to(m)
        Draw(export=True).add_to(m); folium.LayerControl().add_to(m)
        out = st_folium(m, height=540, use_container_width=True, key="rna_map")
        if out and out.get("last_active_drawing"):
            st.success("AOI captured from interactive map."); st.json(out["last_active_drawing"])
    r1, r2 = st.columns(2)
    with r1:
        risk_method = st.selectbox("Risk classification method", ["Quantiles","Fixed thresholds","Z-score / standardised"])
    with r2:
        risk_labels = st.multiselect("Risk labels", ["Very Low","Low","Medium","High","Very High","Extreme"], default=["Very Low","Low","Medium","High","Very High","Extreme"])
    job = {"country":country,"hazard":hazard,"input_mode":input_mode,"start_date":str(start_date),"end_date":str(end_date),"variables":variables,"outputs":outputs,"gee_project":gee_project,"lat":lat,"lon":lon,"buffer_km":buffer_km,"risk_method":risk_method,"risk_labels":risk_labels,"drawn_aoi_present":bool(out and out.get("last_active_drawing"))}
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Generate job specification", use_container_width=True):
            st.session_state["job_spec_v8"] = job
    with c2:
        st.download_button("Download job specification JSON", json.dumps(job, indent=2).encode("utf-8"), file_name="analysis_job_spec.json", mime="application/json", use_container_width=True)
    with c3:
        if st.button("Simulate run setup", use_container_width=True):
            st.session_state["simulated_run_v8"] = True
    render_ai_box("Run New Analysis", "Line", variables, "Monthly", False, [])
    if "job_spec_v8" in st.session_state:
        st.markdown("#### Job specification"); st.json(st.session_state["job_spec_v8"])
    if st.session_state.get("simulated_run_v8"):
        st.markdown("#### Simulated spatial output preview")
        sim_map = folium.Map(location=[lat, lon], zoom_start=5)
        folium.Circle(location=[lat, lon], radius=max(buffer_km,1)*1000, color="#dc2626", fill=True, fill_opacity=0.18, tooltip="Simulated analysis area").add_to(sim_map)
        st_folium(sim_map, height=420, use_container_width=True, key="sim_map_v8")
        sim_df = pd.DataFrame({"risk_class": risk_labels[:min(len(risk_labels),6)], "count": [9,16,22,14,8,4][:min(len(risk_labels),6)]})
        st.dataframe(sim_df, use_container_width=True)
        st.plotly_chart(px.bar(sim_df, x="risk_class", y="count", color="risk_class", title="Simulated risk-class distribution"), use_container_width=True)
    st.markdown("#### Earth Engine initialisation block")
    st.code("""try:
    ee.Initialize(project='ee-reachprojectlshtm')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='ee-reachprojectlshtm')""", language="python")
    st.markdown('<div class="note-box"><strong>Version 8 status:</strong> this page now includes the full country list, AOI definition, variable selection, date range, risk setup, job specification, and simulated spatial preview. To run real live analysis, connect this job specification to your Earth Engine and Python backend scripts.</div>', unsafe_allow_html=True)

def documentation_page():
    st.title("Documentation")
    st.markdown(
        '<div class="note-box"><strong>Case-study note:</strong> Brazil and Zambia are included in this platform as showcase applications and case-study datasets. The platform itself is designed as a broader climate–health and health systems analytics environment for wider national, subnational, and global use with uploaded data and future backend processing.</div>',
        unsafe_allow_html=True
    )
    tabs = st.tabs(["Flood","Heatwaves","Multi-Hazard","Custom Dataset Explorer"])
    files = ["brazil_flood.md","brazil_heat.md","zambia_multihazard.md","custom_dataset.md"]
    for tab, fn in zip(tabs, files):
        with tab:
            st.markdown(safe_read_text(Path("factsheets") / fn))

def downloads_page():
    st.title("Downloads")
    st.markdown("- Use the Explore tab in each workflow to download filtered CSV outputs.\n- Use the Explore tab to download narrative PDF outputs after choosing variables and filters.\n- Use Run New Analysis to download a job specification JSON for future backend execution.\n- This Version 10 release is the final pre-backend public version. Later engineering work can add live processing, map PNG exports, classified risk layers, and workflow ZIP bundles.")

def author_page():
    st.title("Author / Credits")
    st.markdown(safe_read_text(Path("author_credit.md")))
    st.markdown(
        '<div class="note-box"><strong>Scope note:</strong> this release focuses on the public-facing analytics platform, demo workflows, upload-based exploration, documentation, and download features. Full backend engineering and live processing integration are intended as a later development phase.</div>',
        unsafe_allow_html=True
    )

with st.sidebar:
    st.markdown("## Navigate")
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
elif page in ["Brazil Flood","Brazil Heat","Zambia Multi-Hazard","Custom Dataset Explorer"]:
    workflow_page(page)
elif page == "Run New Analysis":
    run_new_analysis_page()
elif page == "Documentation":
    documentation_page()
elif page == "Downloads":
    downloads_page()
elif page == "Author / Credits":
    author_page()
