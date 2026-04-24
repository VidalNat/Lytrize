"""
modules/pages/upload.py
File upload & pre-processing page.

CSV files -> loaded directly as before.
Excel (.xlsx / .xls) -> routed through excel_loader.show_excel_loader()
  which lets the user pick a single sheet OR build a star schema from
  multiple sheets before continuing to analysis.
"""

import streamlit as st
import pandas as pd
from modules.ui.column_manager import show_column_manager
from modules.ui.column_tools import show_dtype_transformer, show_column_classifier
from modules.ui.excel_loader import show_excel_loader
from modules.ui.css import inject_footer


def _is_excel(name: str) -> bool:
    return name.lower().endswith((".xlsx", ".xls"))


def page_upload():
    if st.button("← Home"):
        st.session_state.page = "home"; st.rerun()

    st.markdown("## 📂 Upload Dataset")
    uploaded = st.file_uploader(
        "CSV or Excel (single or multi-sheet)",
        type=["csv", "xlsx", "xls"]
    )

    if not uploaded:
        inject_footer()
        return

    is_excel = _is_excel(uploaded.name)
    file_changed = st.session_state.get("file_name") != uploaded.name

    # CSV: load once, proceed directly
    if not is_excel:
        if "df" not in st.session_state or file_changed:
            with st.spinner("Reading file..."):
                df = pd.read_csv(uploaded)
            st.session_state.df        = df
            st.session_state.file_name = uploaded.name
            _clear_excel_state()
        else:
            df = st.session_state.df
        _show_analysis_pipeline(df, uploaded.name)

    # Excel: route through sheet selector / schema builder
    # Excel: route through sheet selector / schema builder
    else:
        if file_changed:
            st.session_state.pop("df", None)
            _clear_excel_state(uploaded.name)
            st.session_state.file_name = uploaded.name

        schema_info = st.session_state.get("_star_schema_info")
        if schema_info and "df" in st.session_state:
            st.markdown(
                '<div style="background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.25);'
                'border-radius:12px;padding:0.8rem 1.1rem;margin-bottom:1rem;">'
                '&#127775; <b>Star schema active</b> — '
                f'Fact: <b>{schema_info["fact"]}</b> joined with '
                + ", ".join(f"<b>{d}</b>" for d in schema_info["dims"]) +
                f' &nbsp;·&nbsp; {schema_info["shape"][0]:,} rows x {schema_info["shape"][1]} cols'
                '</div>',
                unsafe_allow_html=True
            )

        # FIX: Check if we already have the dataframe in session state
        if "df" not in st.session_state:
            df = show_excel_loader(uploaded)
            
            # If the user just finished building/selecting the sheet:
            if df is not None:
                st.session_state.df = df
                st.rerun()  # Instantly restart to lock in state and move to analysis
        else:
            # Provide an escape hatch if they want to change their sheet mapping
            if st.button("⚙️ Edit Excel Configuration", key="_xl_edit_config"):
                st.session_state.pop("df", None)
                st.rerun()
                
            # Render the pipeline directly from the saved session state
            _show_analysis_pipeline(st.session_state.df, uploaded.name)


def _show_analysis_pipeline(df: pd.DataFrame, file_name: str):
    st.markdown("---")
    st.success(f"✅ **{file_name}** — {df.shape[0]:,} rows × {df.shape[1]} columns")
    st.dataframe(df.head(), use_container_width=True)

    df = show_column_manager(df)
    df = show_dtype_transformer(df)
    show_column_classifier(df)

    with st.expander("📖 Describe Your Columns (optional — improves auto-insights)", expanded=False):
        st.markdown(
            "Describe what each column means. These appear in chart insights "
            "to give context-aware observations. Leave blank to skip."
        )
        col_descs = st.session_state.get("col_descriptions", {})
        for col in df.columns:
            col_descs[col] = st.text_input(
                f"`{col}`",
                value=col_descs.get(col, ""),
                key=f"coldesc_{col}",
                placeholder="e.g. 'Total revenue in USD per transaction'"
            )
        if st.button("💾 Save Column Descriptions", key="save_col_descs"):
            st.session_state.col_descriptions = col_descs
            st.success("✅ Column descriptions saved.")


def _clear_excel_state(new_file_name: str = ""):
    keys_to_delete = [
        k for k in list(st.session_state.keys())
        if k.startswith("_xl_sheets_") and not k.endswith(new_file_name)
    ]
    for k in keys_to_delete:
        del st.session_state[k]
    st.session_state.pop("_star_schema_info", None)
