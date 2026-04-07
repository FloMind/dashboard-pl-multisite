"""
app.py — Dashboard P&L Multi-sites
Point d'entrée Streamlit. Routing + sidebar uniquement.

Usage : streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Dashboard P&L Multi-sites",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #f0f4f8; }
[data-testid="stSidebar"] { background: #0d2b45 !important; }
[data-testid="stSidebar"] * { color: #cfe2f3 !important; }
[data-testid="stSidebar"] label {
    font-size: 10px !important; text-transform: uppercase;
    letter-spacing: 0.1em; color: #85aacc !important; font-weight: 600;
}
[data-testid="stSidebar"] hr { border-color: #1a5f8a !important; opacity: 0.4; }
[data-testid="stSidebar"] .stCaption { color: #7aa3c4 !important; font-size: 10px !important; }
[data-testid="metric-container"] {
    background: #ffffff; border: 1px solid #dce8f5;
    border-left: 4px solid #1a5f8a; border-radius: 4px; padding: 14px 16px 12px;
}
[data-testid="stMetricLabel"] > div {
    font-size: 10px !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important; color: #5d7a8c !important; font-weight: 600 !important;
}
[data-testid="stMetricValue"] > div {
    font-size: 20px !important; font-weight: 600 !important;
    color: #0d2b45 !important; line-height: 1.2;
}
h1 { color: #0d2b45 !important; font-size: 20px !important; font-weight: 600 !important; }
h2 { color: #0d2b45 !important; font-size: 14px !important; font-weight: 600 !important; }
hr { border-color: #dce8f5 !important; margin: 10px 0 !important; }
[data-testid="stDataFrame"] { border: 1px solid #dce8f5 !important; border-radius: 4px !important; }
.sh {
    background: #0d2b45; color: white; padding: 7px 14px;
    border-radius: 3px; font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from core.loader import load_all, filter_data
from core.constants import ONGLETS

import views.vue_ensemble        as v_ensemble
import views.evolution_mensuelle as v_evolution
import views.comparaison_sites   as v_comparaison
import views.drill_down          as v_drill
import views.point_mort          as v_pm
import views.treso_bfr           as v_bfr
import views.detail_comptable    as v_detail

# ── CHARGEMENT UNIQUE ─────────────────────────────────────────────────────────
if "data_pl" not in st.session_state:
    with st.spinner("Chargement des données…"):
        load_all()

data = st.session_state["data_pl"]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filtres")
    all_sites = data["all_sites"]
    sites_sel = st.multiselect("Sites", all_sites, default=all_sites, key="pl_sites")
    st.markdown("---")
    vue = st.radio("Navigation", ONGLETS)
    st.markdown("---")
    nb = len(data["df"])
    st.caption(f"{nb:,} lignes · {len(all_sites)} sites · Déc. 2025")

    # Expander aide glossaire
    with st.expander("📖 Glossaire"):
        st.markdown("""
**MB Commerciale** : CA − Achats marchandises  
**MB Totale** : MB commerciale + RFA siège + variation de stock  
**DSO** : Délai client en jours (créances / CA × 365)  
**DSI** : Délai stock en jours (stock / achats × 365)  
**DPO** : Délai fournisseur en jours (dettes / achats × 365)  
**BFR** : Stocks + Créances − Dettes fournisseurs  
**Point mort** : CA à partir duquel l'entreprise est rentable  
**Indice sécurité** : (CA − seuil PM) / CA × 100  
""")

if not sites_sel:
    st.warning("Sélectionne au moins un site.")
    st.stop()

# ── FILTRAGE SESSION STATE ────────────────────────────────────────────────────
filtered = filter_data(data, sites_sel)
pl_f  = filtered["pl_f"]
df_f  = filtered["df_f"]
bal_f = filtered["bal_f"]
mon_f = filtered["mon_f"]

# ── HEADER ────────────────────────────────────────────────────────────────────
c_t, c_s = st.columns([3, 1])
with c_t:
    st.markdown("# Dashboard P&L — Multi-sites")
with c_s:
    st.markdown(
        '<p style="text-align:right;color:#7f8c8d;font-size:11px;margin-top:18px;">'
        'R2025 · Budget 2025 · N-1 2024 · Cumul fin décembre</p>',
        unsafe_allow_html=True)
st.markdown('<hr style="margin:4px 0 16px;">', unsafe_allow_html=True)

# ── ROUTING ───────────────────────────────────────────────────────────────────
if vue == "Vue d'ensemble":
    v_ensemble.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Évolution mensuelle":
    v_evolution.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Comparaison sites":
    v_comparaison.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Drill-down charges":
    v_drill.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Point mort":
    v_pm.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Tréso & BFR":
    v_bfr.render(pl_f, df_f, bal_f, mon_f)
elif vue == "Détail comptable":
    v_detail.render(pl_f, df_f, bal_f, mon_f)
