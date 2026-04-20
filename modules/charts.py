"""
modules/charts.py
Chart colour palettes, layout defaults, Plotly serialisation, and the
auto-insight engine. Import from here in any analysis module.
"""

import json
import uuid
import streamlit as st
import pandas as pd
import plotly.io as pio

# ── Colour defaults ───────────────────────────────────────────────────────────
COLORS = ["#4f6ef7","#8b5cf6","#06b6d4","#f59e0b","#ef4444","#10b981","#ec4899","#f97316"]
DANGER = ["#bbf7d0","#fbbf24","#ef4444"]

PALETTES = {
    "🔵 Default Blue-Purple": ["#4f6ef7","#8b5cf6","#06b6d4","#f59e0b","#ef4444","#10b981","#ec4899","#f97316"],
    "🌈 Vibrant":             ["#e63946","#f4a261","#2a9d8f","#457b9d","#e9c46a","#264653","#a8dadc","#f1faee"],
    "🍃 Nature Green":        ["#2d6a4f","#40916c","#52b788","#74c69d","#95d5b2","#b7e4c7","#d8f3dc","#1b4332"],
    "🌅 Warm Sunset":         ["#e76f51","#f4a261","#e9c46a","#264653","#2a9d8f","#e63946","#f1faee","#457b9d"],
    "🩷 Pink & Coral":        ["#ff6b6b","#feca57","#48dbfb","#ff9ff3","#54a0ff","#5f27cd","#01abc6","#ff9f43"],
    "🌊 Ocean Blues":         ["#03045e","#0077b6","#00b4d8","#90e0ef","#caf0f8","#023e8a","#0096c7","#ade8f4"],
    "🟣 Monochrome Purple":   ["#3c096c","#5a189a","#7b2fbe","#9d4edd","#c77dff","#e0aaff","#240046","#10002b"],
    "🔆 Pastel Light":        ["#ffadad","#ffd6a5","#fdffb6","#caffbf","#9bf6ff","#a0c4ff","#bdb2ff","#ffc6ff"],
}


def chart_layout():
    """Shared transparent Plotly layout kwargs."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=48, b=20),
        bargap=0.28,
        bargroupgap=0.1,
    )


# ── Session column helpers ────────────────────────────────────────────────────
def num_cols():
    return st.session_state.get("num_cols", [])

def cat_cols():
    return st.session_state.get("cat_cols", [])

def dt_cols():
    return st.session_state.get("dt_cols", [])


# ── Serialisation ─────────────────────────────────────────────────────────────
def charts_to_json(charts):
    out = []
    for chart in charts:
        uid, title, fig = chart[:3]
        desc = st.session_state.get(f"desc_{uid}", "")
        try:
            out.append({"uid": uid, "title": title, "fig_json": pio.to_json(fig), "desc": desc})
        except Exception:
            pass
    return json.dumps(out)


# ── Auto-insight engine ───────────────────────────────────────────────────────
def generate_chart_insights(chart_type: str, title: str, fig, col_descriptions: dict = None) -> list:
    """
    Rule-based, no-LLM insight generator. Returns a list of markdown strings.
    Future: replace body with an LLM call while keeping the same interface.
    """
    insights = []
    tl = title.lower()

    if chart_type == "distribution" or "dist:" in tl:
        try:
            arr = pd.Series(fig.data[0].x).dropna()
            mean, median, std = arr.mean(), arr.median(), arr.std()
            skew = float(arr.skew())
            insights.append(f"📊 **Mean**: {mean:.2f}  ·  **Median**: {median:.2f}  ·  **Std Dev**: {std:.2f}")
            if abs(skew) > 1:
                d = "right (positive)" if skew > 0 else "left (negative)"
                insights.append(f"📐 Skewed **{d}** (skewness {skew:.2f}) — mean is pulled by extreme values.")
            else:
                insights.append(f"📐 Approximately symmetric distribution (skewness {skew:.2f}).")
            q1, q3 = arr.quantile(0.25), arr.quantile(0.75)
            iqr = q3 - q1
            n_out = ((arr < q1-1.5*iqr) | (arr > q3+1.5*iqr)).sum()
            if n_out > 0:
                insights.append(f"🚨 **{n_out}** potential outlier(s) outside 1.5×IQR bounds.")
        except Exception:
            pass

    elif chart_type == "correlation" or "correlation" in tl:
        try:
            z = fig.data[0].z
            if z is not None:
                flat = [v for row in z for v in row if v is not None and abs(v) < 1.0]
                if flat:
                    strongest = max(flat, key=abs)
                    insights.append(f"🔗 Strongest off-diagonal correlation: **{strongest:.2f}**")
            insights.append("💡 |r| > 0.7 = strong · 0.4–0.7 = moderate · < 0.4 = weak")
            insights.append("⚠️ Correlation does not imply causation.")
        except Exception:
            pass

    elif chart_type == "outlier" or "outlier" in tl:
        try:
            outlier_trace = next((t for t in fig.data if getattr(t, "name", "") == "Outlier"), None)
            if outlier_trace and len(outlier_trace.y) > 0:
                n = len(outlier_trace.y)
                insights.append(f"🚨 **{n}** outlier point(s) detected via IQR method.")
                if n > 10:
                    insights.append("⚠️ High outlier count — check for data entry errors or consider a different scale.")
            else:
                insights.append("✅ No outliers detected — data is within expected IQR bounds.")
        except Exception:
            pass

    elif chart_type == "time_series" or "ts:" in tl or "trend" in tl:
        try:
            y = pd.Series(fig.data[0].y).dropna()
            if len(y) >= 2:
                trend = "📈 Upward" if y.iloc[-1] > y.iloc[0] else "📉 Downward"
                pct = (y.iloc[-1] - y.iloc[0]) / abs(y.iloc[0]) * 100 if y.iloc[0] != 0 else 0
                insights.append(f"{trend} trend — **{pct:+.1f}%** change from start to end.")
                rolling_std = y.rolling(max(3, len(y)//5)).std().mean()
                insights.append(f"📊 Average rolling variability (std): {rolling_std:.2f}")
        except Exception:
            pass
        insights.append("📅 Look for seasonal cycles — repeating patterns often signal time-based effects.")

    elif chart_type in ("categorical", "pie_chart") or any(k in tl for k in ("count", "bar", "pie", "donut")):
        try:
            data = fig.data[0]
            if hasattr(data, "y") and data.y is not None:
                vals = list(data.y); xs = list(data.x) if hasattr(data, "x") and data.x is not None else []
            elif hasattr(data, "values") and data.values is not None:
                vals = list(data.values); xs = list(data.labels) if hasattr(data, "labels") else []
            else:
                vals, xs = [], []
            if vals:
                total = sum(vals)
                top_i = vals.index(max(vals))
                top_cat = xs[top_i] if xs else str(top_i)
                top_pct = (max(vals) / total * 100) if total else 0
                insights.append(f"🏆 **Top category**: {top_cat} — {top_pct:.1f}% of total.")
                n_cats = len(vals)
                if n_cats > 1:
                    even_pct = 100 / n_cats
                    concentration = max(vals) / total * 100
                    if concentration > 2 * even_pct:
                        insights.append("⚠️ Distribution is **concentrated** — top category dominates significantly.")
                    else:
                        insights.append(f"✅ Distribution is relatively **balanced** across {n_cats} categories.")
        except Exception:
            pass

    elif chart_type == "statistical" or any(k in tl for k in ("mean", "std", "min", "max")):
        insights.append("📐 Compare magnitudes across columns — large differences in scale may affect modelling.")
        insights.append("💡 High std relative to mean suggests high variability — consider normalisation.")

    elif chart_type == "data_quality" or any(k in tl for k in ("missing", "duplicate", "quality")):
        insights.append("🕳️ Missing values: if <5% consider dropping rows; if >20% consider imputation or dropping the column.")
        insights.append("🔁 Duplicate rows can inflate counts and bias aggregations — remove before analysis.")

    if col_descriptions:
        for col, desc in col_descriptions.items():
            if col.lower() in tl and desc.strip():
                insights.append(f"📖 **{col}**: {desc}")

    return insights
