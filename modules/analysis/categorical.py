"""
modules/analysis/categorical.py
Categorical bar charts — value counts or aggregated metrics per category.
"""

import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols, cat_cols as _cat_cols


# ── Internal sort helper ──────────────────────────────────────────────────────
def _sort_df(df_target, col_x, col_y, sort_by):
    if sort_by == "Value (Desc)":   return df_target.sort_values(col_y, ascending=False)
    if sort_by == "Value (Asc)":    return df_target.sort_values(col_y, ascending=True)
    if sort_by == "Category (A-Z)": return df_target.sort_values(col_x, ascending=True)
    if sort_by == "Category (Z-A)": return df_target.sort_values(col_x, ascending=False)
    return df_target


def run_categorical(df, x_cols=None, y_cols=None, agg="mean", sort_by=None, palette=None, **kwargs):
    """
    Args:
        x_cols:   list of categorical dimension columns
        y_cols:   list of numeric metric columns (optional — falls back to value counts)
        agg:      aggregation string: 'mean', 'sum', 'median', 'count', 'min', 'max'
        sort_by:  one of 'Value (Desc)', 'Value (Asc)', 'Category (A-Z)', 'Category (Z-A)'
        palette:  list of hex colour strings

    Returns:
        list of (title, fig) tuples
    """
    charts    = []
    dims      = x_cols or _cat_cols()[:4]
    metrics   = y_cols
    agg_label = agg.title()
    pal       = palette or COLORS

    for col in dims:
        if metrics:
            # ── Aggregated metric bar ─────────────────────────────────────────
            for metric in metrics:
                agg_vals = df.groupby(col)[metric].agg(agg).reset_index()
                agg_vals.columns = [col, f"{agg_label} {metric}"]
                agg_vals = _sort_df(agg_vals, col, f"{agg_label} {metric}", sort_by)
                fig = px.bar(
                    agg_vals, x=col, y=f"{agg_label} {metric}",
                    title=f"{agg_label} of {metric} by {col}",
                    color=col, color_discrete_sequence=pal, text_auto=".2f")
                fig.update_layout(**chart_layout(), showlegend=False)
                charts.append((f"{agg_label} {metric}", fig))
        else:
            # ── Value count bar ───────────────────────────────────────────────
            vc = df[col].value_counts().reset_index()
            vc.columns = [col, "Count"]
            vc = _sort_df(vc, col, "Count", sort_by)
            fig = px.bar(
                vc, x=col, y="Count",
                title=f"Value Counts: {col}",
                color=col, color_discrete_sequence=pal, text_auto=True)
            fig.update_layout(**chart_layout(), showlegend=False)
            charts.append((f"Counts: {col}", fig))

    return charts
