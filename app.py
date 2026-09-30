from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Netflix Insights",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------- Styling --------------------------------------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      :root { --ink: #172033; --muted: #727b8d; --accent: #e50914; --line: #e9ebf0; }
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: #f6f7fb; }
      [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
      [data-testid="stSidebar"] > div { padding-top: 1.5rem; }
      .block-container { padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1440px; }
      h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); }
      .hero { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:1.2rem; }
      .hero h1 { font-size:2.1rem; letter-spacing:-1.2px; margin:0 0 .3rem 0; }
      .hero p { margin:0; color:var(--muted); font-size:.98rem; }
      .pill { display:inline-block; border:1px solid #f2c5c8; color:#bd0710; background:#fff5f5; border-radius:999px; padding:.4rem .75rem; font-size:.78rem; font-weight:700; white-space:nowrap; }
      .section-title { font-family:'Manrope',sans-serif; font-size:1.08rem; font-weight:700; color:var(--ink); margin:.4rem 0 .85rem 0; }
      .stMetric { background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; box-shadow:0 2px 8px rgba(20,32,55,.025); }
      [data-testid="stMetricLabel"] { color:var(--muted); font-size:.82rem; }
      [data-testid="stMetricValue"] { color:var(--ink); font-family:'Manrope',sans-serif; font-size:1.7rem; }
      div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; }
      .hint { color:var(--muted); font-size:.86rem; }
      div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
      .stTabs [data-baseweb="tab-list"] { gap:1rem; }
      .stTabs [data-baseweb="tab"] { padding:10px 4px; }
      footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- Data helpers ---------------------------------
def demo_data() -> pd.DataFrame:
    """Create a small deterministic dataset so the dashboard is usable immediately."""
    rows = []
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    plans = ["Basic", "Standard", "Premium"]
    categories = ["Drama", "Comedy", "Documentary", "Action", "Thriller"]
    for i in range(96):
        rows.append(
            {
                "Watch_Date": pd.Timestamp("2025-01-01") + pd.Timedelta(days=(i * 7) % 365),
                "Region": regions[(i * 3 + i // 5) % len(regions)],
                "Monthly_Revenue": [8.99, 13.99, 19.99][(i // 2 + i % 3) % 3],
                "Subscription_Plan": plans[(i + i // 7) % len(plans)],
                "Rating": round(2.5 + ((i * 7) % 26) / 10, 1),
                "Category": categories[(i * 2 + i // 4) % len(categories)],
                "Title": f"Sample title {i + 1:02d}",
            }
        )
    return pd.DataFrame(rows)


def load_data(uploaded_file) -> tuple[pd.DataFrame, str]:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), "Uploaded CSV"
    local_csv = Path(__file__).resolve().parent / "netflix.csv"
    if local_csv.exists():
        return pd.read_csv(local_csv), "netflix.csv"
    return demo_data(), "Demo data"


def format_currency(value) -> str:
    if pd.isna(value):
        return "—"
    return f"${value:,.2f}"


# -------------------------------- Sidebar ------------------------------------
st.sidebar.markdown("## 🎬 Netflix Insights")
st.sidebar.caption("A clear view of your viewing and subscription data")
uploaded_file = st.sidebar.file_uploader("Load your Netflix CSV", type=["csv"])
try:
    raw_data, source_name = load_data(uploaded_file)
except Exception as exc:
    st.error(f"Couldn't read this CSV: {exc}")
    st.stop()

if raw_data.empty:
    st.warning("This CSV has no rows. Upload a file with data to continue.")
    st.stop()

data = raw_data.copy()
if "Watch_Date" in data.columns:
    data["Watch_Date"] = pd.to_datetime(data["Watch_Date"], errors="coerce")
for column in ("Monthly_Revenue", "Rating"):
    if column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")
filtered = data.copy()
for column, label in (
    ("Region", "Region"),
    ("Subscription_Plan", "Subscription plan"),
    ("Category", "Category"),
):
    if column in filtered.columns:
        options = sorted(filtered[column].dropna().astype(str).unique().tolist())
        selected = st.sidebar.multiselect(label, options, default=options, key=f"filter_{column}")
        if len(selected) < len(options):
            filtered = filtered[filtered[column].astype(str).isin(selected)]

if "Watch_Date" in filtered.columns:
    valid_dates = filtered["Watch_Date"].dropna()
    if not valid_dates.empty:
        date_range = st.sidebar.date_input(
            "Watch date range",
            value=(valid_dates.min().date(), valid_dates.max().date()),
            min_value=valid_dates.min().date(),
            max_value=valid_dates.max().date(),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered = filtered[
                filtered["Watch_Date"].isna()
                | filtered["Watch_Date"].dt.date.between(start_date, end_date)
            ]

# -------------------------------- Dashboard ----------------------------------
st.markdown(
    f"""
    <div class="hero">
      <div><h1>Netflix Insights</h1><p>Understand revenue, subscriptions, and viewing trends at a glance.</p></div>
      <span class="pill">● &nbsp;{source_name}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
if source_name == "Demo data":
    st.info("Showing illustrative demo data. Upload your CSV in the sidebar, or place your file beside app.py as netflix.csv.")

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
    st.stop()

revenue = filtered["Monthly_Revenue"].sum(min_count=1) if "Monthly_Revenue" in filtered else float("nan")
avg_rating = filtered["Rating"].mean() if "Rating" in filtered else float("nan")
regions_count = filtered["Region"].nunique() if "Region" in filtered else None

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Records", f"{len(filtered):,}", delta=f"of {len(data):,} total")
with metric_cols[1]:
    st.metric("Monthly revenue", format_currency(revenue))
with metric_cols[2]:
    st.metric("Average rating", f"{avg_rating:.1f} / 5" if pd.notna(avg_rating) else "—")
with metric_cols[3]:
    st.metric("Regions covered", f"{regions_count:,}" if regions_count is not None else "—")

st.markdown("<br>", unsafe_allow_html=True)
overview_tab, data_tab, quality_tab = st.tabs(["Overview", "Explore data", "Data quality"])

with overview_tab:
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Revenue by region</div>', unsafe_allow_html=True)
            if {"Region", "Monthly_Revenue"}.issubset(filtered.columns):
                chart_data = filtered.groupby("Region", as_index=True)["Monthly_Revenue"].sum().sort_values(ascending=False)
                st.bar_chart(chart_data, color="#e50914", height=300)
            else:
                st.info("Add Region and Monthly_Revenue columns to see this chart.")
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Records by subscription plan</div>', unsafe_allow_html=True)
            if "Subscription_Plan" in filtered.columns:
                plan_data = filtered["Subscription_Plan"].value_counts().sort_values(ascending=False)
                st.bar_chart(plan_data, color="#493b78", height=300)
            else:
                st.info("Add a Subscription_Plan column to see this chart.")

    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Revenue trend</div>', unsafe_allow_html=True)
            if {"Watch_Date", "Monthly_Revenue"}.issubset(filtered.columns):
                trend = filtered.dropna(subset=["Watch_Date"]).set_index("Watch_Date")["Monthly_Revenue"].resample("MS").sum()
                if not trend.empty:
                    st.line_chart(trend, color="#e50914", height=270)
                else:
                    st.info("No valid watch dates are available for the selected data.")
            else:
                st.info("Add Watch_Date and Monthly_Revenue columns to see this chart.")
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Titles by category</div>', unsafe_allow_html=True)
            if "Category" in filtered.columns:
                category_data = filtered["Category"].value_counts().sort_values(ascending=False)
                st.bar_chart(category_data, color="#178f82", height=270)
            else:
                st.info("Add a Category column to see this chart.")

with data_tab:
    st.markdown('<div class="section-title">Filtered records</div>', unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered):,} rows from {source_name}.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="netflix_filtered.csv",
        mime="text/csv",
        type="primary",
    )

with quality_tab:
    st.markdown('<div class="section-title">Dataset health</div>', unsafe_allow_html=True)
    quality_cols = st.columns(3)
    quality_cols[0].metric("Rows", f"{len(data):,}")
    quality_cols[1].metric("Columns", f"{data.shape[1]:,}")
    quality_cols[2].metric("Duplicate rows", f"{int(data.duplicated().sum()):,}")
    missing = data.isna().sum().rename("Missing values").to_frame()
    missing["Missing %"] = (data.isna().mean() * 100).round(1)
    st.dataframe(missing, use_container_width=True)
    st.markdown("<p class='hint'>Date and numeric fields are converted automatically when possible. Original records are otherwise preserved.</p>", unsafe_allow_html=True)
