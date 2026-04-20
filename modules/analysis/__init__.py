"""
modules/analysis/__init__.py
Central registry: ANALYSIS_OPTIONS, _RUNNERS, axis selector, and _run().

Adding a new analysis:
  1. Create modules/analysis/my_feature.py with run_my_feature(df, **kwargs)
  2. Import it here and add to ANALYSIS_OPTIONS + _RUNNERS
  3. Add axis config to _axis_selector() if needed
  4. Done — it appears automatically in page_analysis.
"""

import uuid
import streamlit as st

from modules.analysis.descriptive  import run_descriptive
from modules.analysis.statistical  import run_statistical
from modules.analysis.distribution import run_distribution
from modules.analysis.correlation  import run_correlation
from modules.analysis.categorical  import run_categorical
from modules.analysis.pie_chart    import run_pie_chart
from modules.analysis.time_series  import run_time_series

from modules.analysis.data_quality import run_data_quality
from modules.analysis.outlier import run_outlier, OUTLIER_HELP
from modules.charts import PALETTES, num_cols as _num_cols, cat_cols as _cat_cols, dt_cols as _dt_cols

# ── Registry ──────────────────────────────────────────────────────────────────
ANALYSIS_OPTIONS = [
    {"id":"descriptive",  "icon":"🗂️", "name":"Descriptive",      "desc":"Stats table — numeric cols"},
    {"id":"data_quality", "icon":"🧹", "name":"Data Quality",      "desc":"Missing values & duplicates"},
    {"id":"statistical",  "icon":"📐", "name":"Statistical",       "desc":"Mean, std, min, max"},
    {"id":"distribution", "icon":"📊", "name":"Distribution",      "desc":"Histograms & box plots"},
    {"id":"correlation",  "icon":"🔗", "name":"Correlation",       "desc":"Heatmap & scatter matrix"},
    {"id":"categorical",  "icon":"🏷️", "name":"Categorical Bar",   "desc":"Bar charts for categories"},
    {"id":"pie_chart",    "icon":"🍩", "name":"Pie & Donut",       "desc":"Proportion & share analysis"},
    {"id":"time_series",  "icon":"⏱️", "name":"Time Series",       "desc":"Trends & time patterns"},
    {"id":"outlier",      "icon":"🚨", "name":"Outlier Detection", "desc":"IQR-based anomaly analysis"},
]

_RUNNERS = {
    "descriptive":  run_descriptive,
    "data_quality": run_data_quality,
    "statistical":  run_statistical,
    "distribution": run_distribution,
    "correlation":  run_correlation,
    "categorical":  run_categorical,
    "pie_chart":    run_pie_chart,
    "time_series":  run_time_series,
    "outlier":      run_outlier,
}

# Analyses that need axis/palette selection before generating charts.
_NEEDS_AXES = {"statistical","distribution","correlation","categorical","pie_chart","time_series","outlier"}

# Analyses whose runner renders interactive widgets (st.button etc.)
# MUST be executed OUTSIDE st.form().
_NO_FORM = {"data_quality"}

_AGG_FUNCS  = {"Mean (Avg)":"mean","Sum":"sum","Median":"median","Count":"count","Min":"min","Max":"max"}
_DATE_PARTS = {
    "None": None, "Year":"Y", "Quarter":"Q", "Month (number)":"M",
    "Month Name":"month_name", "Weekday Name":"weekday_name", "Day":"D", "Hour":"H"
}


def _axis_selector(aid, df):
    num, cat, dt, all_cols = _num_cols(), _cat_cols(), _dt_cols(), df.columns.tolist()

    pal_col, _ = st.columns([2, 3])
    with pal_col:
        pal_label = st.selectbox("🎨 Chart Palette", list(PALETTES.keys()), index=0, key=f"palette_{aid}")
    palette = PALETTES[pal_label]
    st.markdown("<br>", unsafe_allow_html=True)

    x, y, agg_func, date_part, sort_by = None, None, "mean", None, None

    if aid == "statistical":
        c1, c2, c3 = st.columns(3)
        with c1: x = st.multiselect("Group by", cat, max_selections=1)
        with c2: y = st.multiselect("Metrics", num, default=num[:4])
        with c3: agg_func = _AGG_FUNCS[st.selectbox("Aggregation", list(_AGG_FUNCS.keys()))]
        x = x or None; y = y or num

    elif aid == "distribution":
        c1, c2 = st.columns(2)
        with c1: x = st.multiselect("Columns", num, default=num[:4])
        with c2: y = st.multiselect("Color by", cat, max_selections=1)
        x = x or num[:4]; y = y or None

    elif aid == "correlation":
        c1, c2 = st.columns(2)
        with c1: x = st.multiselect("Primary", num, default=num)
        with c2: y = st.multiselect("Additional", num)
        x = x or num; y = y or None

    elif aid in ("categorical", "pie_chart"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: x = st.multiselect("Dimensions", cat, default=cat[:2])
        with c2: y = st.multiselect("Metrics", num)
        with c3: agg_func = _AGG_FUNCS[st.selectbox("Aggregation", list(_AGG_FUNCS.keys()))]
        with c4: sort_by = st.selectbox("Sort", ["Value (Desc)","Value (Asc)","Category (A-Z)","Category (Z-A)"])
        x = x or cat[:2]; y = y or None

    elif aid == "time_series":
        dt_candidates = dt if dt else all_cols
        c1, c2, c3, c4 = st.columns(4)
        with c1: x = st.multiselect("Date column", dt_candidates, default=dt_candidates[:1] if dt_candidates else None, max_selections=1)
        with c2: y = st.multiselect("Metrics", num, default=num[:2])
        with c3: date_part = _DATE_PARTS[st.selectbox("Date part", list(_DATE_PARTS.keys()))]
        with c4: agg_func = _AGG_FUNCS[st.selectbox("Aggregation", list(_AGG_FUNCS.keys()))]
        x = x or None; y = y or num[:2]

    elif aid == "outlier":
        c1, c2 = st.columns(2)
        with c1: x = st.multiselect("Columns", num, default=num[:4])
        with c2: y = st.multiselect("Group by", cat, max_selections=1)
        x = x or num[:4]; y = y or None

    return {"x_cols": x, "y_cols": y, "agg": agg_func, "date_part": date_part,
            "palette": palette, "sort_by": sort_by}


def _run(aid, df, **kwargs):
    fn = _RUNNERS.get(aid)
    if not fn:
        return []
    try:
        raw = fn(df) if aid in ("descriptive", "data_quality") else fn(df, **kwargs)
        return [(str(uuid.uuid4())[:8], title, fig) for title, fig in raw]
    except Exception as e:
        st.error(f"Analysis error ({aid}): {e}")
        return None
