"""
modules/analysis/statistical.py
Statistical aggregation charts — mean, sum, median, count, min, max.
Supports optional grouping by a categorical column.
"""

import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols


def run_statistical(df, x_cols=None, y_cols=None, agg="mean", palette=None, **kwargs):
    """
    Args:
        x_cols:  list with one categorical column to group by (optional)
        y_cols:  list of numeric columns to aggregate
        agg:     aggregation function string — 'mean', 'sum', 'median', 'count', 'min', 'max'
        palette: list of hex colour strings

    Returns:
        list of (title, fig) tuples
    """
    charts = []
    num       = y_cols or _num_cols()
    grp       = x_cols[0] if x_cols else None
    agg_label = agg.title()
    pal       = palette or COLORS

    if grp and grp in df.columns:
        # ── Grouped bar per metric ────────────────────────────────────────────
        for metric in num:
            agg_vals = df.groupby(grp)[metric].agg(agg).reset_index()
            agg_vals.columns = [grp, f"{agg_label} {metric}"]
            fig = px.bar(
                agg_vals, x=grp, y=f"{agg_label} {metric}",
                title=f"{agg_label} of {metric} by {grp}",
                color=grp, color_discrete_sequence=pal, text_auto=".2f")
            fig.update_layout(**chart_layout())
            charts.append((f"{agg_label} by {grp}", fig))
    else:
        # ── Overview bar (all numeric cols) ───────────────────────────────────
        summary = df[num].agg(agg).reset_index()
        summary.columns = ["Column", agg_label]
        fig = px.bar(
            summary, x="Column", y=agg_label,
            title=f"{agg_label} Overview",
            color="Column", color_discrete_sequence=pal, text_auto=".2f")
        fig.update_layout(**chart_layout())
        charts.append((f"{agg_label} Values", fig))

        # ── Standard deviation companion chart ────────────────────────────────
        stds = df[num].std().reset_index()
        stds.columns = ["Column", "Std Dev"]
        fig2 = px.bar(
            stds, x="Column", y="Std Dev",
            title="Standard Deviation",
            color="Column", color_discrete_sequence=pal, text_auto=".2f")
        fig2.update_layout(**chart_layout())
        charts.append(("Standard Deviation", fig2))

    return charts
