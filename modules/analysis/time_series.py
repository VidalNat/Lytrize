"""
modules/analysis/time_series.py
Time series line charts with optional date-part aggregation.
Supports Year, Quarter, Month, Weekday, Day, Hour groupings.
"""

import pandas as pd
import plotly.express as px
from modules.charts import chart_layout, COLORS, num_cols as _num_cols


# Month and weekday ordering maps for categorical x-axis sorting
_MONTH_ORDER   = {m: i for i, m in enumerate([
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"])}
_WEEKDAY_ORDER = {d: i for i, d in enumerate(
    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}


def run_time_series(df, x_cols=None, y_cols=None, agg="mean", date_part=None, palette=None, **kwargs):
    """
    Args:
        x_cols:     list with one date/time column (auto-detected if omitted)
        y_cols:     list of numeric metric columns
        agg:        aggregation string: 'mean', 'sum', 'median', 'count', 'min', 'max'
        date_part:  pandas period alias or special string —
                    'Y', 'Q', 'M', 'D', 'H', 'month_name', 'weekday_name', or None
        palette:    list of hex colour strings

    Returns:
        list of (title, fig) tuples
    """
    charts    = []
    num       = y_cols or _num_cols()[:4]
    df        = df.copy()
    dt_col    = x_cols[0] if x_cols else None
    agg_label = agg.title()
    pal       = palette or COLORS

    # ── Auto-detect a date column if none specified ───────────────────────────
    if not dt_col:
        for col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
                dt_col  = col
                break
            except Exception:
                pass

    # ── Ensure the date column is datetime dtype ──────────────────────────────
    if dt_col and not pd.api.types.is_datetime64_any_dtype(df[dt_col]):
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    plot_x     = dt_col
    x_label    = dt_col or "Index"
    order_map  = None

    # ── Apply date-part aggregation ───────────────────────────────────────────
    if dt_col and date_part:
        temp_dt = pd.to_datetime(df[dt_col].astype(str), errors="coerce")

        if date_part == "month_name":
            df["_period"] = temp_dt.dt.month_name()
            order_map     = _MONTH_ORDER
            plot_x, x_label = "_period", "Month"

        elif date_part == "weekday_name":
            df["_period"] = temp_dt.dt.day_name()
            order_map     = _WEEKDAY_ORDER
            plot_x, x_label = "_period", "Weekday"

        else:
            try:
                df["_period"] = temp_dt.dt.to_period(date_part).astype(str)
                plot_x, x_label = "_period", f"{dt_col} ({date_part})"
            except Exception:
                pass  # fall back to raw datetime

    # ── Build one chart per metric ────────────────────────────────────────────
    for i, col in enumerate(num):
        colour = [pal[i % len(pal)]]

        if dt_col and plot_x == "_period":
            grp = df.groupby("_period")[col].agg(agg).reset_index()
            grp.columns = ["Period", col]
            if order_map:
                grp["_sort"] = grp["Period"].map(order_map)
                grp = grp.sort_values("_sort").drop(columns="_sort")
            else:
                grp = grp.sort_values("Period")
            fig = px.line(
                grp, x="Period", y=col,
                title=f"{agg_label} {col} by {x_label}",
                color_discrete_sequence=colour, markers=True)
            fig.update_xaxes(type="category", title_text=x_label)

        elif dt_col:
            fig = px.line(
                df.sort_values(dt_col), x=dt_col, y=col,
                title=f"Time Series: {col}",
                color_discrete_sequence=colour)

        else:
            fig = px.line(
                df.reset_index(), x="index", y=col,
                title=f"Trend: {col}",
                color_discrete_sequence=colour)

        fig.update_layout(**chart_layout())
        charts.append((f"TS: {col}", fig))

    return charts
