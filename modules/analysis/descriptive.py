"""
modules/analysis/descriptive.py
Descriptive statistics table — numeric columns only.
Returns an empty list (renders inline via st.dataframe, not a Plotly chart).
"""

import streamlit as st
from modules.charts import num_cols as _num_cols


def run_descriptive(df):
    """
    Renders a stats summary table directly into the Streamlit page.
    Returns [] — no Plotly charts produced.
    """
    num = _num_cols()
    if not num:
        st.warning("No numeric columns found. Check your column classification.")
        return []

    desc = df[num].describe().T.reset_index()
    desc.columns = [c.title() if c != "index" else "Column" for c in desc.columns]
    desc[desc.select_dtypes("number").columns] = desc.select_dtypes("number").round(4)

    st.dataframe(desc, use_container_width=True, hide_index=True)
    return []
