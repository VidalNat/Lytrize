"""
modules/ui/css.py
Injects adaptive CSS for DataLyze. Called once from main().
"""

import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sora:wght@600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }

    .kpi-card, .metric-card, .ag-card, .sess-card, .info-bar, .classifier-box, .themed-box {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    .kpi-card { padding: 1.2rem 1rem; text-align: center; }
    .kpi-icon { font-size: 1.4rem; margin-bottom: 0.25rem; }
    .kpi-val { font-family: 'Sora', sans-serif; font-size: 1.75rem; font-weight: 700; line-height: 1.1; color: var(--text-color); }
    .kpi-lbl { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; opacity: 0.7; margin-top: 0.25rem; }

    .ag-card { padding: 1.2rem 1rem; text-align: center; min-height: 130px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .ag-card.done { border-color: #4f6ef7 !important; box-shadow: 0 0 0 1px #4f6ef7; }
    .ag-icon { font-size: 1.9rem; margin-bottom: 0.4rem; }
    .ag-name { font-weight: 600; font-size: 0.9rem; }
    .ag-desc { font-size: 0.72rem; opacity: 0.7; margin-top: 0.2rem; line-height: 1.4; }
    .done-badge { font-size: 0.68rem; background: #10b981; color: #fff; padding: 0.15rem 0.5rem; border-radius: 10px; margin-top: 0.4rem; }

    .brand { font-family: 'Sora', sans-serif; font-size: 1.55rem; font-weight: 800;
              background: linear-gradient(120deg, #4f6ef7 20%, #8b5cf6 80%);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #4f6ef7, #8b5cf6) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        transition: 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    .stButton > button:hover { opacity: 0.9; transform: translateY(-1px); }

    .welcome-banner { background: linear-gradient(135deg, #4f6ef7 0%, #8b5cf6 100%);
                      border-radius: 20px; padding: 2rem 2.5rem; margin-bottom: 1.5rem; }
    .pill { display:inline-block; background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.35); border-radius: 20px;
            padding: 0.28rem 0.85rem; font-size: 0.78rem; margin: 0.2rem; }

    hr { border-top: 1px solid rgba(128, 128, 128, 0.2); }
    .sec-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
                 text-transform: uppercase; opacity: 0.7; margin: 1.2rem 0 0.6rem; }

    .stTextInput input, .stSelectbox div[data-baseweb="select"],
    .stTextArea textarea, .stNumberInput input {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
