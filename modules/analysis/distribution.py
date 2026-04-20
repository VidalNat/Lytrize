"""
modules/analysis/distribution.py
Histogram + box-plot marginal for each selected numeric column.
"""

import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols


def run_distribution(df, x_cols=None, y_cols=None, palette=None, **kwargs):
    """
    Args:
        x_cols:  list of numeric columns to plot (defaults to first 6 numeric cols)
        y_cols:  list with one categorical column to colour-split (optional)
        palette: list of hex colour strings

    Returns:
        list of (title, fig) tuples
    """
    charts = []
    num = x_cols or _num_cols()[:6]
    pal = palette or COLORS

    for i, col in enumerate(num):
        fig = px.histogram(
            df, x=col, nbins=35, marginal="box",
            title=f"Distribution: {col}",
            color_discrete_sequence=[pal[i % len(pal)]])
        fig.update_layout(**chart_layout())
        charts.append((f"Dist: {col}", fig))

    return charts
