"""
modules/analysis/correlation.py
Pearson correlation heatmap for selected numeric columns.
Requires at least 2 numeric columns.
"""

import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols


def run_correlation(df, x_cols=None, y_cols=None, palette=None, **kwargs):
    """
    Args:
        x_cols:  primary list of numeric columns
        y_cols:  additional numeric columns to include (merged with x_cols)
        palette: list of hex colour strings used as the colour scale

    Returns:
        list of (title, fig) tuples — always zero or one chart
    """
    charts = []
    num = list(dict.fromkeys((x_cols or []) + (y_cols or []) or _num_cols()))

    if len(num) < 2:
        return charts   # caller handles the empty result

    pal  = palette or COLORS
    corr = df[num].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        title="Correlation Heatmap",
        color_continuous_scale=pal,
        aspect="auto",
        zmin=-1, zmax=1)
    fig.update_layout(**chart_layout())
    charts.append(("Correlation", fig))

    return charts
