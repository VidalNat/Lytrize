"""
modules/analysis/pie_chart.py
Pie / Donut charts — proportion and share breakdown by category.
"""

import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols, cat_cols as _cat_cols


def _sort_df(df_target, col_x, col_y, sort_by):
    if sort_by == "Value (Desc)":   return df_target.sort_values(col_y, ascending=False)
    if sort_by == "Value (Asc)":    return df_target.sort_values(col_y, ascending=True)
    if sort_by == "Category (A-Z)": return df_target.sort_values(col_x, ascending=True)
    if sort_by == "Category (Z-A)": return df_target.sort_values(col_x, ascending=False)
    return df_target


def run_pie_chart(df, x_cols=None, y_cols=None, agg="mean", sort_by=None, palette=None, **kwargs):
    """
    Args:
        x_cols:   list of categorical dimension columns (slices of the pie)
        y_cols:   list of numeric metric columns (optional — falls back to value counts)
        agg:      aggregation string: 'mean', 'sum', 'median', 'count', 'min', 'max'
        sort_by:  sorting preference passed through to pre-sort before plotting
        palette:  list of hex colour strings

    Returns:
        list of (title, fig) tuples
    """
    charts    = []
    dims      = x_cols or _cat_cols()[:2]
    metrics   = y_cols
    agg_label = agg.title()
    pal       = palette or COLORS

    for col in dims:
        if metrics:
            # ── Aggregated metric donut ───────────────────────────────────────
            for metric in metrics:
                agg_vals = df.groupby(col)[metric].agg(agg).reset_index()
                agg_vals.columns = [col, "Value"]
                agg_vals = _sort_df(agg_vals, col, "Value", sort_by)
                fig = px.pie(
                    agg_vals, names=col, values="Value",
                    title=f"{agg_label} {metric} Split by {col}",
                    color_discrete_sequence=pal, hole=0.45)
                fig.update_layout(**chart_layout())
                charts.append((f"Pie: {col}", fig))
        else:
            # ── Value count donut ─────────────────────────────────────────────
            vc = df[col].value_counts().reset_index()
            vc.columns = [col, "Count"]
            vc = _sort_df(vc, col, "Count", sort_by)
            fig = px.pie(
                vc, names=col, values="Count",
                title=f"Distribution of {col}",
                color_discrete_sequence=pal, hole=0.45)
            fig.update_layout(**chart_layout())
            charts.append((f"Pie Counts: {col}", fig))

    return charts
