"""
modules/analysis/runners.py
All remaining analysis runner functions (non-data-quality, non-outlier).
Each returns a list of (title, fig) tuples.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.charts import chart_layout, COLORS, num_cols as _num_cols, cat_cols as _cat_cols, dt_cols as _dt_cols


# ── Sorting helper ────────────────────────────────────────────────────────────
def _sort_df(df_target, col_x, col_y, sort_by):
    if sort_by == "Value (Desc)":   return df_target.sort_values(col_y, ascending=False)
    if sort_by == "Value (Asc)":    return df_target.sort_values(col_y, ascending=True)
    if sort_by == "Category (A-Z)": return df_target.sort_values(col_x, ascending=True)
    if sort_by == "Category (Z-A)": return df_target.sort_values(col_x, ascending=False)
    return df_target


# ── Descriptive ───────────────────────────────────────────────────────────────
def run_descriptive(df):
    num = _num_cols()
    if not num:
        return []
    desc = df[num].describe().T.reset_index()
    desc.columns = [c.title() if c != "index" else "Column" for c in desc.columns]
    desc[desc.select_dtypes("number").columns] = desc.select_dtypes("number").round(4)
    st.dataframe(desc, use_container_width=True, hide_index=True)
    return []


# ── Statistical ───────────────────────────────────────────────────────────────
def run_statistical(df, x_cols=None, y_cols=None, agg="mean", palette=None, **kwargs):
    charts = []
    num = y_cols or _num_cols()
    grp = x_cols[0] if x_cols else None
    agg_label = agg.title()
    pal = palette or COLORS

    if grp and grp in df.columns:
        for metric in num:
            agg_vals = df.groupby(grp)[metric].agg(agg).reset_index()
            agg_vals.columns = [grp, f"{agg_label} {metric}"]
            fig = px.bar(agg_vals, x=grp, y=f"{agg_label} {metric}",
                         title=f"{agg_label} of {metric} by {grp}",
                         color=grp, color_discrete_sequence=pal, text_auto=".2f")
            fig.update_layout(**chart_layout())
            charts.append((f"{agg_label} by {grp}", fig))
    else:
        summary = df[num].agg(agg).reset_index()
        summary.columns = ["Column", agg_label]
        fig = px.bar(summary, x="Column", y=agg_label, title=f"{agg_label} Overview",
                     color="Column", color_discrete_sequence=pal, text_auto=".2f")
        fig.update_layout(**chart_layout())
        charts.append((f"{agg_label} Values", fig))

        stds = df[num].std().reset_index()
        stds.columns = ["Column", "Std Dev"]
        fig2 = px.bar(stds, x="Column", y="Std Dev", title="Standard Deviation",
                      color="Column", color_discrete_sequence=pal, text_auto=".2f")
        fig2.update_layout(**chart_layout())
        charts.append(("Standard Deviation", fig2))
    return charts


# ── Distribution ──────────────────────────────────────────────────────────────
def run_distribution(df, x_cols=None, y_cols=None, palette=None, **kwargs):
    charts = []
    num = x_cols or _num_cols()[:6]
    pal = palette or COLORS
    for i, col in enumerate(num):
        fig = px.histogram(df, x=col, nbins=35, marginal="box",
                           title=f"Distribution: {col}",
                           color_discrete_sequence=[pal[i % len(pal)]])
        fig.update_layout(**chart_layout())
        charts.append((f"Dist: {col}", fig))
    return charts


# ── Correlation ───────────────────────────────────────────────────────────────
def run_correlation(df, x_cols=None, y_cols=None, palette=None, **kwargs):
    charts = []
    num = list(dict.fromkeys((x_cols or []) + (y_cols or []) or _num_cols()))
    if len(num) < 2:
        return charts
    pal = palette or COLORS
    corr = df[num].corr()
    fig = px.imshow(corr, text_auto=".2f", title="Correlation Heatmap",
                    color_continuous_scale=pal, aspect="auto", zmin=-1, zmax=1)
    fig.update_layout(**chart_layout())
    charts.append(("Correlation", fig))
    return charts


# ── Categorical Bar ───────────────────────────────────────────────────────────
def run_categorical(df, x_cols=None, y_cols=None, agg="mean", sort_by=None, palette=None, **kwargs):
    charts = []
    dims = x_cols or _cat_cols()[:4]
    metrics = y_cols
    agg_label = agg.title()
    pal = palette or COLORS

    for col in dims:
        if metrics:
            for metric in metrics:
                agg_vals = df.groupby(col)[metric].agg(agg).reset_index()
                agg_vals.columns = [col, f"{agg_label} {metric}"]
                agg_vals = _sort_df(agg_vals, col, f"{agg_label} {metric}", sort_by)
                fig = px.bar(agg_vals, x=col, y=f"{agg_label} {metric}",
                             title=f"{agg_label} of {metric} by {col}",
                             color=col, color_discrete_sequence=pal, text_auto=".2f")
                fig.update_layout(**chart_layout(), showlegend=False)
                charts.append((f"{agg_label} {metric}", fig))
        else:
            vc = df[col].value_counts().reset_index()
            vc.columns = [col, "Count"]
            vc = _sort_df(vc, col, "Count", sort_by)
            fig = px.bar(vc, x=col, y="Count", title=f"Value Counts: {col}",
                         color=col, color_discrete_sequence=pal, text_auto=True)
            fig.update_layout(**chart_layout(), showlegend=False)
            charts.append((f"Counts: {col}", fig))
    return charts


# ── Pie / Donut ───────────────────────────────────────────────────────────────
def run_pie_chart(df, x_cols=None, y_cols=None, agg="mean", sort_by=None, palette=None, **kwargs):
    charts = []
    dims = x_cols or _cat_cols()[:2]
    metrics = y_cols
    agg_label = agg.title()
    pal = palette or COLORS

    for col in dims:
        if metrics:
            for metric in metrics:
                agg_vals = df.groupby(col)[metric].agg(agg).reset_index()
                agg_vals.columns = [col, "Value"]
                agg_vals = _sort_df(agg_vals, col, "Value", sort_by)
                fig = px.pie(agg_vals, names=col, values="Value",
                             title=f"{agg_label} {metric} Split by {col}",
                             color_discrete_sequence=pal, hole=0.45)
                fig.update_layout(**chart_layout())
                charts.append((f"Pie: {col}", fig))
        else:
            vc = df[col].value_counts().reset_index()
            vc.columns = [col, "Count"]
            vc = _sort_df(vc, col, "Count", sort_by)
            fig = px.pie(vc, names=col, values="Count",
                         title=f"Distribution of {col}",
                         color_discrete_sequence=pal, hole=0.45)
            fig.update_layout(**chart_layout())
            charts.append((f"Pie Counts: {col}", fig))
    return charts


# ── Time Series ───────────────────────────────────────────────────────────────
def run_time_series(df, x_cols=None, y_cols=None, agg="mean", date_part=None, palette=None, **kwargs):
    charts = []
    num = y_cols or _num_cols()[:4]
    df = df.copy()
    dt_col = x_cols[0] if x_cols else None
    agg_label = agg.title()
    pal = palette or COLORS

    if not dt_col:
        for col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
                dt_col = col; break
            except Exception:
                pass

    if dt_col and not pd.api.types.is_datetime64_any_dtype(df[dt_col]):
        df[dt_col] = pd.to_datetime(df[dt_col], errors='coerce')

    plot_x = dt_col
    x_label = dt_col or "Index"
    order_map = None

    if dt_col:
        temp_dt = pd.to_datetime(df[dt_col].astype(str), errors='coerce')
        if date_part:
            if date_part == "month_name":
                df["_period"] = temp_dt.dt.month_name()
                order_map = {m: i for i, m in enumerate([
                    "January","February","March","April","May","June",
                    "July","August","September","October","November","December"])}
                plot_x, x_label = "_period", "Month"
            elif date_part == "weekday_name":
                df["_period"] = temp_dt.dt.day_name()
                order_map = {d: i for i, d in enumerate(
                    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
                plot_x, x_label = "_period", "Weekday"
            else:
                try:
                    df["_period"] = temp_dt.dt.to_period(date_part).astype(str)
                    plot_x, x_label = "_period", f"{dt_col} ({date_part})"
                except Exception:
                    pass

    for i, col in enumerate(num):
        if dt_col and plot_x == "_period":
            grp = df.groupby("_period")[col].agg(agg).reset_index()
            grp.columns = ["Period", col]
            if order_map:
                grp["_sort"] = grp["Period"].map(order_map)
                grp = grp.sort_values("_sort").drop(columns="_sort")
            else:
                grp = grp.sort_values("Period")
            fig = px.line(grp, x="Period", y=col,
                          title=f"{agg_label} {col} by {x_label}",
                          color_discrete_sequence=[pal[i % len(pal)]], markers=True)
            fig.update_xaxes(type='category', title_text=x_label)
        elif dt_col:
            fig = px.line(df.sort_values(dt_col), x=dt_col, y=col,
                          title=f"Time Series: {col}",
                          color_discrete_sequence=[pal[i % len(pal)]])
        else:
            fig = px.line(df.reset_index(), x="index", y=col,
                          title=f"Trend: {col}",
                          color_discrete_sequence=[pal[i % len(pal)]])
        fig.update_layout(**chart_layout())
        charts.append((f"TS: {col}", fig))
    return charts
