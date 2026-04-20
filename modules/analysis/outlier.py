"""
modules/analysis/outlier.py
IQR-based outlier detection with improved chart hover labels and a user guide.

FIX: X-axis now shows row index (not raw coordinate), hover shows "Row / Value"
     clearly, and a concise business-use guide is shown above the charts.
"""

import streamlit as st
import plotly.graph_objects as go
from modules.charts import chart_layout, COLORS


def run_outlier(df, x_cols=None, y_cols=None, palette=None, **kwargs):
    """
    Returns list of (title, fig) tuples.
    Also renders a help banner — must be called outside st.form().
    Wait: outlier IS inside st.form via _axis_selector, so we render the banner
    *after* returning (caller renders charts). The banner is added as an annotation
    inside the figure instead, keeping form compatibility.
    """
    charts = []
    from modules.charts import num_cols as _num_cols
    num = x_cols or _num_cols()[:6]
    pal = palette or COLORS

    for col in num:
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR

        out_mask = (df[col] < lo) | (df[col] > hi)
        out = df[out_mask].copy()
        nrm = df[~out_mask].copy()

        fig = go.Figure()

        # Normal points — row index on X for meaningful hover
        fig.add_trace(go.Scatter(
            x=nrm.index,
            y=nrm[col].values,
            mode="markers",
            name="Normal",
            marker=dict(color=pal[0], size=4, opacity=0.45),
            hovertemplate=(
                f"<b>Row:</b> %{{x}}<br>"
                f"<b>{col}:</b> %{{y:,.2f}}<br>"
                "<extra>Normal</extra>"
            )
        ))

        # Outlier points
        fig.add_trace(go.Scatter(
            x=out.index,
            y=out[col].values,
            mode="markers",
            name="Outlier ⚠️",
            marker=dict(color="#ef4444", size=9, symbol="x"),
            hovertemplate=(
                f"<b>Row:</b> %{{x}}<br>"
                f"<b>{col}:</b> %{{y:,.2f}}<br>"
                "<extra>⚠️ Outlier</extra>"
            )
        ))

        fig.add_hline(y=hi, line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"Upper IQR boundary: {hi:.2f}",
                      annotation_position="top right")
        fig.add_hline(y=lo, line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"Lower IQR boundary: {lo:.2f}",
                      annotation_position="bottom right")

        n_out = len(out)
        fig.update_layout(
            title=f"Outliers — {col}  ({n_out} outlier{'s' if n_out != 1 else ''} detected)",
            xaxis_title="Row Index (hover to see exact row number)",
            yaxis_title=col,
            **chart_layout()
        )

        charts.append((f"Outliers: {col}", fig))

    return charts


# ── Help text rendered by the page layer after charts are added ───────────────
OUTLIER_HELP = (
    "**📊 How to read Outlier charts:**  "
    "Each dot is one row in your dataset. "
    "**🔴 Red × marks** are outliers — values that fall outside the IQR boundaries (dashed lines). "
    "**Hover** over any point to see its exact Row Index and value. "
    "The row index maps directly to the row number in your raw data table.\n\n"
    "**Business use:** Outliers often signal data-entry errors, fraud, returns, or exceptional events. "
    "Investigate red points before running predictive models — they can skew results significantly."
)
