"""
Dashboard P&L Multi-sites
Données : export comptable annuel (fin décembre)
Stack  : Streamlit + Pandas + Plotly
Usage  : streamlit run dashboard_pl.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard P&L Multi-sites",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FILE     = "data/sample_data.xlsx"
FILE_BAL = "data/sample_balance.xlsx"
FILE_MON = "data/sample_monthly.xlsx"

# ── PALETTE CORPORATE BLEU ─────────────────────────────────────────────────────
C_NAVY   = "#0d2b45"
C_BLUE   = "#1a5f8a"
C_STEEL  = "#2980b9"
C_ICE    = "#d6eaf8"
C_POS    = "#1e8449"
C_NEG    = "#c0392b"
C_BUDGET = "#d68910"
C_N1     = "#7f8c8d"
C_GRID   = "rgba(13,43,69,0.06)"
FONT     = "Inter, Segoe UI, Arial, sans-serif"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #f0f4f8; }

[data-testid="stSidebar"] { background: #0d2b45 !important; }
[data-testid="stSidebar"] section { background: #0d2b45 !important; }
[data-testid="stSidebar"] * { color: #cfe2f3 !important; }
[data-testid="stSidebar"] label {
    font-size: 10px !important; text-transform: uppercase;
    letter-spacing: 0.1em; color: #85aacc !important; font-weight: 600;
}
[data-testid="stSidebar"] hr { border-color: #1a5f8a !important; opacity: 0.4; }
[data-testid="stSidebar"] .stCaption { color: #7aa3c4 !important; font-size: 10px !important; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #dce8f5;
    border-left: 4px solid #1a5f8a;
    border-radius: 4px;
    padding: 14px 16px 12px;
}
[data-testid="stMetricLabel"] > div {
    font-size: 10px !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important; color: #5d7a8c !important; font-weight: 600 !important;
}
[data-testid="stMetricValue"] > div {
    font-size: 20px !important; font-weight: 600 !important;
    color: #0d2b45 !important; line-height: 1.2;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

h1 { color: #0d2b45 !important; font-size: 20px !important; font-weight: 600 !important; }
h2 { color: #0d2b45 !important; font-size: 14px !important; font-weight: 600 !important; }
h3 { color: #1a5f8a !important; font-size: 12px !important; font-weight: 600 !important; }
p  { color: #2c3e50; font-size: 13px; }
hr { border-color: #dce8f5 !important; margin: 10px 0 !important; }
.stCaption { color: #7f8c8d !important; font-size: 11px !important; }
[data-testid="stDataFrame"] { border: 1px solid #dce8f5 !important; border-radius: 4px !important; }
[data-baseweb="select"] { border-color: #dce8f5 !important; background: #fff !important; }
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stRadio"] label {
    font-size: 11px !important; font-weight: 600 !important;
    color: #5d7a8c !important; text-transform: uppercase; letter-spacing: 0.07em;
}
.sh {
    background: #0d2b45; color: white; padding: 7px 14px;
    border-radius: 3px; font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ── CLASSIFICATION COMPTABLE ───────────────────────────────────────────────────
def classe_compte(compte: int) -> str:
    s = str(compte)
    c = int(s)
    if s.startswith("70") or s.startswith("72") or s.startswith("75") or \
       s.startswith("76") or s.startswith("77") or s.startswith("78") or \
       s.startswith("79"):
        return "Produits"
    if c == 609720:
        return "RFA"
    if c == 603700:
        return "Variation de stock"
    if s.startswith("607") or s.startswith("608") or s.startswith("602") or \
       s.startswith("604") or s.startswith("606") or s.startswith("609"):
        return "Achats marchandises"
    if s.startswith("64"):
        return "Charges personnel"
    if s.startswith("61"):
        return "Loyers & entretien"
    if s.startswith("62"):
        return "Services extérieurs"
    if s.startswith("63"):
        return "Impôts & taxes"
    if s.startswith("681") or s.startswith("686") or s.startswith("687"):
        return "Dotations & provisions"
    if s.startswith("654") or s.startswith("6581") or s.startswith("6582") or \
       c in (658005, 658000, 651600):
        return "Pertes & litiges clients"
    return "Autres charges"


# ── CHARGEMENT ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Libellé Compte":           "libelle_compte",
        "Libellé Centre de Coûts":  "site",
        "MENSUEL R 25":             "mensuel_r25",
        "MENSUEL B 25":             "mensuel_b25",
        "MENSUEL R 24":             "mensuel_r24",
        "MENSUEL R 25 vs B 25":     "mensuel_ecart_b",
        "MENSUEL R 25 vs R 24":     "mensuel_ecart_n1",
        "CUMUL R 25":               "cumul_r25",
        "CUMUL B 25":               "cumul_b25",
        "CUMUL R 24":               "cumul_r24",
        "CUMUL R 25 vs B 25":       "cumul_ecart_b",
        "CUMUL R 25 vs R 24":       "cumul_ecart_n1",
        "BUDGET ANNUEL B 25":        "ap_b25",
        "REALISE ANNUEL R 24":        "ap_r24",
    })
    df["Compte"] = pd.to_numeric(df["Compte"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Compte", "site"])
    df["categorie"] = df["Compte"].apply(classe_compte)
    num_cols = ["cumul_r25","cumul_b25","cumul_r24","mensuel_r25",
                "mensuel_b25","mensuel_r24","ap_b25","ap_r24"]
    return df.groupby(["Compte","libelle_compte","site","categorie"])[num_cols].sum().reset_index()


def build_pl(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for site, grp in df.groupby("site"):
        prod  = grp[grp["categorie"] == "Produits"]
        ach   = grp[grp["categorie"] == "Achats marchandises"]
        rfa   = grp[grp["categorie"] == "RFA"]
        stock = grp[grp["categorie"] == "Variation de stock"]
        pers  = grp[grp["categorie"] == "Charges personnel"]
        loyer = grp[grp["categorie"] == "Loyers & entretien"]
        svc   = grp[grp["categorie"] == "Services extérieurs"]
        imp   = grp[grp["categorie"] == "Impôts & taxes"]
        aut   = grp[grp["categorie"] == "Autres charges"]

        ca_r25, ca_b25, ca_r24 = prod["cumul_r25"].sum(), prod["cumul_b25"].sum(), prod["cumul_r24"].sum()
        ach_r25, ach_b25, ach_r24 = ach["cumul_r25"].sum(), ach["cumul_b25"].sum(), ach["cumul_r24"].sum()
        rfa_r25, rfa_r24 = rfa["cumul_r25"].sum(), rfa["cumul_r24"].sum()
        stock_r25, stock_r24 = stock["cumul_r25"].sum(), stock["cumul_r24"].sum()

        mbc_r25, mbc_b25, mbc_r24 = ca_r25+ach_r25, ca_b25+ach_b25, ca_r24+ach_r24
        mb_r25 = mbc_r25 + rfa_r25 + stock_r25
        mb_b25 = mbc_b25
        mb_r24 = mbc_r24 + rfa_r24 + stock_r24

        def ch_sum(g, c): return g[g["categorie"]==c]["cumul_r25"].sum()
        def ch_sum_b(g, c): return g[g["categorie"]==c]["cumul_b25"].sum()
        def ch_sum_n(g, c): return g[g["categorie"]==c]["cumul_r24"].sum()

        ch_r25 = sum(ch_sum(grp, c)   for c in ["Charges personnel","Loyers & entretien","Services extérieurs","Impôts & taxes","Dotations & provisions","Pertes & litiges clients","Autres charges"])
        ch_b25 = sum(ch_sum_b(grp, c) for c in ["Charges personnel","Loyers & entretien","Services extérieurs","Impôts & taxes","Dotations & provisions","Pertes & litiges clients","Autres charges"])
        ch_r24 = sum(ch_sum_n(grp, c) for c in ["Charges personnel","Loyers & entretien","Services extérieurs","Impôts & taxes","Dotations & provisions","Pertes & litiges clients","Autres charges"])

        res_r25, res_b25, res_r24 = mb_r25+ch_r25, mb_b25+ch_b25, mb_r24+ch_r24
        tx_mbc_r25 = (mbc_r25/ca_r25*100) if ca_r25 else 0
        tx_mbc_b25 = (mbc_b25/ca_b25*100) if ca_b25 else 0
        tx_mbc_r24 = (mbc_r24/ca_r24*100) if ca_r24 else 0

        # ── POINT MORT ────────────────────────────────────────────────────────
        # Charges fixes = non pilotables à court terme : personnel, loyers, impôts, dotations
        # Charges variables de structure = partiellement pilotables : services, pertes, autres
        # Convention : toutes les charges sont négatives dans le CR
        ch_fixes_r25      = sum(ch_sum(grp, c) for c in [
            "Charges personnel", "Loyers & entretien",
            "Impôts & taxes",    "Dotations & provisions"])
        ch_var_struct_r25 = sum(ch_sum(grp, c) for c in [
            "Services extérieurs", "Pertes & litiges clients", "Autres charges"])

        # Marge sur coûts variables = CA - achats - charges variables de structure
        # (ach_r25 et ch_var_struct_r25 sont négatifs → addition directe)
        mcv_r25    = ca_r25 + ach_r25 + ch_var_struct_r25
        tx_mcv_r25 = mcv_r25 / ca_r25 * 100 if ca_r25 else 0

        # Point mort : CA nécessaire pour couvrir les charges fixes
        pm_r25     = abs(ch_fixes_r25) / (tx_mcv_r25 / 100) if tx_mcv_r25 else 0
        ms_r25     = ca_r25 - pm_r25           # marge de sécurité (€)
        tx_ms_r25  = ms_r25 / ca_r25 * 100 if ca_r25 else 0   # taux de sécurité %
        pm_jours   = pm_r25 / ca_r25 * 365 if ca_r25 > 0 else 999  # PM en jours de CA
        levier_op  = mcv_r25 / res_r25 if res_r25 and res_r25 != 0 else 0  # levier opérationnel

        rows.append(dict(
            site=site,
            ca_r25=ca_r25,   ca_b25=ca_b25,  ca_r24=ca_r24,
            ach_r25=ach_r25, ach_b25=ach_b25, ach_r24=ach_r24,
            rfa_r25=rfa_r25, rfa_r24=rfa_r24,
            stock_r25=stock_r25, stock_r24=stock_r24,
            mbc_r25=mbc_r25, mbc_b25=mbc_b25, mbc_r24=mbc_r24,
            tx_mbc_r25=tx_mbc_r25, tx_mbc_b25=tx_mbc_b25, tx_mbc_r24=tx_mbc_r24,
            mb_r25=mb_r25,   mb_b25=mb_b25,  mb_r24=mb_r24,
            pers_r25=ch_sum(grp,"Charges personnel"),
            loyer_r25=ch_sum(grp,"Loyers & entretien"),
            svc_r25=ch_sum(grp,"Services extérieurs"),
            imp_r25=ch_sum(grp,"Impôts & taxes"),
            dot_r25=ch_sum(grp,"Dotations & provisions"),
            perte_r25=ch_sum(grp,"Pertes & litiges clients"),
            aut_r25=ch_sum(grp,"Autres charges"),
            ch_r25=ch_r25, ch_b25=ch_b25, ch_r24=ch_r24,
            res_r25=res_r25, res_b25=res_b25, res_r24=res_r24,
            ecart_b=res_r25-res_b25, ecart_n1=res_r25-res_r24,
            # Point mort — champs exportés
            ch_fixes_r25=ch_fixes_r25,
            ch_var_struct_r25=ch_var_struct_r25,
            mcv_r25=mcv_r25,
            tx_mcv_r25=tx_mcv_r25,
            pm_r25=pm_r25,
            ms_r25=ms_r25,
            tx_ms_r25=tx_ms_r25,
            pm_jours=pm_jours,
            levier_op=levier_op,
            # Alias pour l'UI (noms cohérents avec les sections Point mort)
            seuil_r25=pm_r25,
            marge_secu=ms_r25,
            ind_secu=tx_ms_r25,
            charges_fixes=abs(ch_fixes_r25),
        ))
    return pd.DataFrame(rows).sort_values("res_r25", ascending=False)


# ── HELPERS ────────────────────────────────────────────────────────────────────
def fmt_k(v: float, dec: int = 0) -> str:
    """Formate en k€. Évite l'affichage de -0 k€."""
    k = v / 1000
    if abs(k) < 0.05:
        return "—"
    return f"{'+' if k > 0 else ''}{k:,.{dec}f} k€".replace(",", " ")

def fmt_m(v: float, dec: int = 1) -> str:
    """Formate en M€ pour les agrégats réseau."""
    m = v / 1_000_000
    if abs(m) < 0.005:
        return "—"
    return f"{'+' if m > 0 else ''}{m:,.{dec}f} M€".replace(",", " ")

def fmt_k_ecart(v: float, ref: float, dec: int = 0) -> str:
    """Écart vs référence : affiche N/A si référence absente."""
    if ref == 0:
        return "N/A"
    return fmt_k(v, dec)

@st.cache_data
def load_balance(path: str) -> pd.DataFrame:
    """Charge les données bilan (stock, tréso, créances, dettes, BFR)."""
    try:
        return pd.read_excel(path)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data
def load_monthly(path: str) -> pd.DataFrame:
    """Charge les séries mensuelles (CA, MB, résultat par site et mois)."""
    try:
        return pd.read_excel(path)
    except FileNotFoundError:
        return pd.DataFrame()


def bar_colors(s): return [C_POS if v >= 0 else C_NEG for v in s]

def chart_layout(fig, height=380, title="", legend=True):
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, family=FONT, color=C_NAVY), x=0, y=0.98),
        height=height, font=dict(family=FONT, size=11, color="#2c3e50"),
        plot_bgcolor="#ffffff", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=36 if title else 14, b=28, l=8, r=8),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.18, x=0,
                    font=dict(size=10, color="#5d7a8c"), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=True, gridcolor=C_GRID, gridwidth=1,
                     zeroline=False, linecolor="#dce8f5",
                     tickfont=dict(size=10, color="#5d7a8c"))
    fig.update_yaxes(showgrid=True, gridcolor=C_GRID, gridwidth=1,
                     zeroline=True, zerolinecolor="#bcd4e8", zerolinewidth=1.5,
                     tickfont=dict(size=10, color="#5d7a8c"))
    return fig

def sh(label):
    st.markdown(f'<div class="sh">{label}</div>', unsafe_allow_html=True)


def kpi(col, label, valeur, sous_label, sous_val,
        evol=None, rag=C_BLUE, big=False):
    """Fonction KPI unifiée — remplace kpi_card, big_kpi et kpi."""
    fs_val  = "26px" if big else "20px"
    pad     = "16px 18px" if big else "12px 14px"
    mb      = "8px"  if big else "5px"
    fleche  = ("▲" if evol >= 0 else "▼") if evol is not None else ""
    evol_c  = (C_POS if evol >= 0 else C_NEG) if evol is not None else C_N1
    evol_s  = (f'<span style="font-size:11px;font-weight:600;color:{evol_c};">'
               f'{fleche} {abs(evol):.1f}%</span>') if evol is not None else ""
    col.markdown(
        f'<div style="background:#fff;border:1px solid #dce8f5;'
        f'border-top:4px solid {rag};border-radius:4px;padding:{pad};">'
        f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.09em;color:#5d7a8c;margin-bottom:{mb};">{label}</div>'
        f'<div style="font-size:{fs_val};font-weight:600;color:{C_NAVY};'
        f'line-height:1.15;">{valeur}</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-top:{mb};">'
        f'<span style="font-size:11px;color:#7f8c8d;">{sous_label} : {sous_val}</span>'
        f'{evol_s}</div></div>',
        unsafe_allow_html=True
    )


def color_val(v) -> str:
    """Couleur CSS pour une valeur k€ ou % formatée — fonction unifiée."""
    try:
        n = float(str(v).replace(" k€","").replace(" M€","").replace("%","")
                  .replace("+","").replace(" ","").replace(",","."))
        if n > 0:  return f"color:{C_POS};font-weight:500"
        if n < 0:  return f"color:{C_NEG};font-weight:500"
    except Exception:
        pass
    return ""


def pm_mois_label(jours: float) -> str:
    """Convertit un nombre de jours en mois approximatif de l'année."""
    MOIS = ["Jan","Fév","Mar","Avr","Mai","Jun",
            "Jul","Aoû","Sep","Oct","Nov","Déc"]
    if jours >= 365:
        return "Non atteint"
    m = min(int(jours / 30.4), 11)
    return MOIS[m]


import io  # déplacé ici depuis les blocs inline


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    df   = load_data(FILE)
    pl   = build_pl(df)
    bal  = load_balance(FILE_BAL)
    mon  = load_monthly(FILE_MON)

    # SIDEBAR
    with st.sidebar:
        st.markdown("## Filtres")
        all_sites = sorted(pl["site"].unique())
        sites_sel = st.multiselect("Sites", all_sites, default=all_sites)
        st.markdown("---")
        vue = st.radio("Navigation", [
            "Vue d'ensemble", "Évolution mensuelle",
            "Comparaison sites", "Drill-down charges",
            "Point mort", "Tréso & BFR", "Détail comptable"
        ])
        st.markdown("---")
        st.caption(f"{len(df):,} lignes · {len(all_sites)} sites · Déc. 2025")

    if not sites_sel:
        st.warning("Sélectionne au moins un site.")
        return

    pl_f  = pl[pl["site"].isin(sites_sel)]
    df_f  = df[df["site"].isin(sites_sel)]
    bal_f = bal[bal["site"].isin(sites_sel)] if not bal.empty else pd.DataFrame()
    mon_f = mon[mon["site"].isin(sites_sel)] if not mon.empty else pd.DataFrame()

    # HEADER
    c_t, c_s = st.columns([3, 1])
    with c_t:
        st.markdown("# Dashboard P&L — Multi-sites")
    with c_s:
        st.markdown(
            '<p style="text-align:right;color:#7f8c8d;font-size:11px;margin-top:18px;">'
            'R2025 · Budget 2025 · N-1 2024 · Cumul fin décembre</p>',
            unsafe_allow_html=True)
    st.markdown('<hr style="margin:4px 0 16px;">', unsafe_allow_html=True)

    # KPIs globaux — toujours affichés sauf en Vue d'ensemble (remplacés par blocs enrichis)
    ca_tot   = pl_f["ca_r25"].sum()
    mbc_tot  = pl_f["mbc_r25"].sum()
    res_tot  = pl_f["res_r25"].sum()
    ecart_b  = pl_f["ecart_b"].sum()
    ecart_n1 = pl_f["ecart_n1"].sum()
    tx_mbc   = mbc_tot / ca_tot * 100 if ca_tot else 0
    nb_pos   = (pl_f["res_r25"] >= 0).sum()
    nb_neg   = (pl_f["res_r25"] < 0).sum()

    if vue != "Vue d'ensemble":
        k1,k2,k3,k4,k5,k6 = st.columns(6)
        with k1: st.metric("CA Réalisé 2024",  f"{ca_tot/1e6:.2f} M€")
        with k2: st.metric("MB Commerciale",   f"{mbc_tot/1e6:.2f} M€", delta=f"{tx_mbc:.1f}% du CA")
        with k3: st.metric("Résultat net",     f"{res_tot/1e6:.2f} M€")
        with k4: st.metric("Écart vs Budget",  fmt_k(ecart_b),  delta_color="normal" if ecart_b>=0 else "inverse")
        with k5: st.metric("Écart vs N-1",     fmt_k(ecart_n1), delta_color="normal" if ecart_n1>=0 else "inverse")
        with k6: st.metric("Sites rentables",  f"{nb_pos} / {nb_pos+nb_neg}",
                            delta=f"{nb_neg} en déficit", delta_color="inverse" if nb_neg>0 else "off")
        st.markdown('<hr style="margin:14px 0;">', unsafe_allow_html=True)

    # ══ DIRECTION GÉNÉRALE ════════════════════════════════════════════════════
    # ══ VUE D'ENSEMBLE ══════════════════════════════════════════════════
    if vue == "Vue d'ensemble":

        has_bal = not bal_f.empty
        has_mon = not mon_f.empty

        # ── BLOC 1 — SYNTHÈSE RÉSEAU ─────────────────────────────────────

        # ── LIGNE 1 : KPIs P&L réseau ─────────────────────────────────────────
        sh("Performance réseau — Compte de résultat")
        ca_tot    = pl_f["ca_r25"].sum()
        ca_n1     = pl_f["ca_r24"].sum()
        mbc_tot   = pl_f["mbc_r25"].sum()
        res_tot   = pl_f["res_r25"].sum()
        res_n1    = pl_f["res_r24"].sum()
        res_b     = pl_f["res_b25"].sum()
        tx_mbc    = mbc_tot / ca_tot * 100 if ca_tot else 0
        tx_res    = res_tot / ca_tot * 100 if ca_tot else 0
        evol_ca   = (ca_tot - ca_n1)  / abs(ca_n1)  * 100 if ca_n1  else 0
        evol_res  = (res_tot - res_n1) / abs(res_n1) * 100 if res_n1 else 0
        ecart_b   = res_tot - res_b
        nb_pos    = (pl_f["res_r25"] >= 0).sum()
        nb_tot    = len(pl_f)


        c1,c2,c3,c4,c5 = st.columns(5, gap="small")
        kpi(c1, "CA Réalisé 2024",
                 fmt_m(ca_tot), "N-1", fmt_m(ca_n1),
                 evol=evol_ca, rag=C_BLUE)
        kpi(c2, "MB Commerciale",
                 fmt_m(mbc_tot), "Taux", f"{tx_mbc:.1f}%",
                 rag=C_BLUE)
        kpi(c3, "Résultat net réseau",
                 fmt_m(res_tot), "Taux", f"{tx_res:.1f}%",
                 evol=evol_res,
                 rag=C_POS if tx_res >= 5 else (C_BUDGET if tx_res >= 0 else C_NEG))
        kpi(c4, "Écart vs Budget",
                 fmt_m(ecart_b), "Budget", fmt_m(res_b),
                 rag=C_POS if ecart_b >= 0 else C_NEG)
        kpi(c5, "Santé réseau",
                 f"{nb_pos} / {nb_tot} sites", "En déficit", f"{nb_tot-nb_pos}",
                 rag=C_POS if nb_pos/nb_tot >= 0.8 else C_BUDGET)

        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

        # ── LIGNE 2 : BFR + Trésorerie ────────────────────────────────────────
        if has_bal:
            sh("BFR & Trésorerie réseau")

            treso_tot = bal_f["tresorerie"].sum()
            treso_n1  = bal_f["tresorerie_n1"].sum()
            stock_tot = bal_f["stock_net"].sum()
            stock_n1  = bal_f["stock_n1"].sum()
            cre_tot   = bal_f["creances_net"].sum()
            cre_n1    = bal_f["creances_n1"].sum()
            det_tot   = bal_f["dettes_frs"].sum()
            det_n1    = bal_f["dettes_n1"].sum()
            bfr_tot   = bal_f["bfr"].sum()
            bfr_n1_tot= bal_f["bfr_n1"].sum()
            dso_moy   = bal_f["dso"].mean()
            dsi_moy   = bal_f["dsi"].mean()
            dpo_moy   = bal_f["dpo"].mean()
            dso_n1    = (bal_f["creances_n1"] / (bal_f["creances_net"] / bal_f["dso"].replace(0,1))).mean()
            dsi_n1    = (bal_f["stock_n1"]    / (bal_f["stock_net"]    / bal_f["dsi"].replace(0,1))).mean()
            dpo_n1    = (bal_f["dettes_n1"]   / (bal_f["dettes_frs"]   / bal_f["dpo"].replace(0,1))).mean()
            couv_moy  = treso_tot / bfr_tot * 100 if bfr_tot else 0

            b1,b2,b3,b4,b5,b6 = st.columns(6, gap="small")
            kpi(b1, "Trésorerie réseau",
                     fmt_m(treso_tot), "Couv. BFR", f"{couv_moy:.0f}%",
                     evol=(treso_tot-treso_n1)/abs(treso_n1)*100 if treso_n1 else None,
                     rag=C_POS if treso_tot >= 0 else C_NEG)
            kpi(b2, "Stock réseau",
                     fmt_m(stock_tot), "DSI moy.", f"{dsi_moy:.0f} j",
                     evol=-(dsi_moy - dsi_n1)/dsi_n1*100 if dsi_n1 else None,
                     rag=C_BUDGET if dsi_moy > 75 else C_BLUE)
            kpi(b3, "Créances clients",
                     fmt_m(cre_tot), "DSO moy.", f"{dso_moy:.0f} j",
                     evol=-(dso_moy - dso_n1)/dso_n1*100 if dso_n1 else None,
                     rag=C_BUDGET if dso_moy > 50 else C_BLUE)
            kpi(b4, "Dettes fourn.",
                     fmt_m(det_tot), "DPO moy.", f"{dpo_moy:.0f} j",
                     evol=(dpo_moy - dpo_n1)/dpo_n1*100 if dpo_n1 else None,
                     rag=C_POS if dpo_moy > 40 else C_BLUE)
            kpi(b5, "BFR réseau",
                     fmt_m(bfr_tot), "Vs tréso", fmt_m(treso_tot - bfr_tot),
                     evol=-(bfr_tot-bfr_n1_tot)/abs(bfr_n1_tot)*100 if bfr_n1_tot else None,
                     rag=C_POS if treso_tot >= bfr_tot else C_NEG)
            kpi(b6, "Sites à risque tréso",
                     f"{(bal_f['tresorerie'] < 0).sum()} / {len(bal_f)}",
                     "BFR > tréso",
                     f"{(bal_f['bfr'] > bal_f['tresorerie']).sum()}",
                     rag=C_POS if (bal_f['tresorerie'] < 0).sum() == 0 else C_NEG)

            st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

            # ── LIGNE 3 : Graphiques BFR ──────────────────────────────────────
            gcol1, gcol2 = st.columns(2, gap="medium")

            with gcol1:
                sh("Trésorerie & BFR par site")
                bal_s = bal_f.merge(pl_f[["site","res_r25"]], on="site").sort_values("tresorerie")
                fig_t = go.Figure()
                fig_t.add_bar(
                    x=bal_s["site"], y=bal_s["tresorerie"]/1000,
                    name="Trésorerie", marker_color=bar_colors(bal_s["tresorerie"]),
                    marker_line_width=0,
                )
                fig_t.add_scatter(
                    x=bal_s["site"], y=bal_s["bfr"]/1000,
                    name="BFR", mode="markers",
                    marker=dict(color=C_BUDGET, size=8, symbol="diamond",
                                line=dict(width=1.5, color="white")),
                )
                fig_t.add_hline(y=0, line_color="#bcd4e8", line_width=1.5)
                chart_layout(fig_t, height=320)
                fig_t.update_layout(yaxis_title="k€", barmode="group")
                st.plotly_chart(fig_t, use_container_width=True)

            with gcol2:
                sh("Délais de gestion par site (jours)")
                bal_s2 = bal_f.sort_values("dso", ascending=False)
                fig_d = go.Figure()
                fig_d.add_bar(x=bal_s2["site"], y=bal_s2["dso"],
                              name="DSO clients", marker_color=C_BLUE,
                              marker_line_width=0)
                fig_d.add_bar(x=bal_s2["site"], y=bal_s2["dsi"],
                              name="DSI stock", marker_color=C_STEEL,
                              marker_line_width=0, opacity=0.75)
                fig_d.add_bar(x=bal_s2["site"], y=bal_s2["dpo"],
                              name="DPO fourn.", marker_color=C_POS,
                              marker_line_width=0, opacity=0.65)
                # Cibles
                fig_d.add_hline(y=45, line_dash="dot", line_color=C_BUDGET,
                                line_width=1.2, opacity=0.6,
                                annotation_text="Cible DSO 45j",
                                annotation_font=dict(size=9, color=C_BUDGET),
                                annotation_position="top right")
                chart_layout(fig_d, height=320)
                fig_d.update_layout(barmode="group", yaxis_title="jours")
                st.plotly_chart(fig_d, use_container_width=True)

            st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

        # ── LIGNE 4 : Tableau réseau consolidé ────────────────────────────────
        sh("Tableau réseau consolidé")

        tbl_dg = pl_f[["site","ca_r25","tx_mbc_r25","mb_r25","ch_r25",
                        "res_r25","ecart_b","ecart_n1"]].copy()
        tbl_dg.columns = ["Site","CA R25","Tx MB%","MB Totale",
                          "Charges","Rés. R25","Écart B","Écart N-1"]

        if has_bal:
            bal_merge = bal_f[["site","tresorerie","bfr","dso","dsi","dpo"]].copy()
            bal_merge.columns = ["Site","Tréso","BFR","DSO","DSI","DPO"]
            tbl_dg = tbl_dg.merge(bal_merge, on="Site", how="left")

        # Formatage
        for c in ["CA R25","MB Totale","Charges","Rés. R25","Écart B","Écart N-1"]:
            tbl_dg[c] = tbl_dg[c].apply(fmt_k)
        tbl_dg["Tx MB%"] = tbl_dg["Tx MB%"].apply(lambda v: f"{v:.1f}%")
        if has_bal:
            tbl_dg["Tréso"] = tbl_dg["Tréso"].apply(fmt_k)
            tbl_dg["BFR"]   = tbl_dg["BFR"].apply(fmt_k)
            tbl_dg["DSO"]   = tbl_dg["DSO"].apply(lambda v: f"{v:.0f}j")
            tbl_dg["DSI"]   = tbl_dg["DSI"].apply(lambda v: f"{v:.0f}j")
            tbl_dg["DPO"]   = tbl_dg["DPO"].apply(lambda v: f"{v:.0f}j")


        styled = tbl_dg.set_index("Site").style.applymap(
            color_val, subset=["Rés. R25","Écart B","Écart N-1","Tréso"] if has_bal
                    else ["Rés. R25","Écart B","Écart N-1"])
        st.dataframe(styled, use_container_width=True,
                     height=min(800, len(tbl_dg)*36+44))

        # Export
        buf = io.BytesIO()
        tbl_dg.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            label="⬇ Exporter le tableau DG",
            data=buf.getvalue(),
            file_name="synthese_dg_r2024.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ══ VUE D'ENSEMBLE ════════════════════════════════════════════════════════
        st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)

        # ── BLOC 2 — DÉTAIL SITES ───────────────────────────────────────
        cl, cr = st.columns([3, 2], gap="medium")

        with cl:
            sh("Résultat par site — R2025 vs Budget")
            pl_s = pl_f.sort_values("res_r25")
            fig = go.Figure()
            fig.add_bar(
                x=pl_s["res_r25"]/1000, y=pl_s["site"], orientation="h",
                marker_color=bar_colors(pl_s["res_r25"]), marker_line_width=0,
                text=[fmt_k(v) for v in pl_s["res_r25"]],
                textposition="outside", textfont=dict(size=10, color=C_NAVY),
                name="Résultat R24",
            )
            fig.add_bar(
                x=pl_s["res_b25"]/1000, y=pl_s["site"], orientation="h",
                marker_color=C_BUDGET, marker_line_width=0, opacity=0.3,
                name="Budget B25",
            )
            fig.add_vline(x=0, line_color="#bcd4e8", line_width=1.5)
            chart_layout(fig, height=max(380, len(pl_s)*28+60))
            fig.update_layout(barmode="overlay", xaxis_title="k€")
            st.plotly_chart(fig, use_container_width=True)

        with cr:
            sh("Classement sites")
            st.markdown(
                '<p style="font-size:10px;color:#7f8c8d;text-align:right;margin:0 0 6px;">'
                'Résultat R24 · Écart Budget</p>', unsafe_allow_html=True)

            for _, row in pl_f.sort_values("res_r25", ascending=False).iterrows():
                c = C_POS if row["res_r25"] >= 0 else C_NEG
                ec = C_POS if row["ecart_b"] >= 0 else C_NEG
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:6px 10px;border-left:3px solid {c};background:#fff;'
                    f'margin-bottom:3px;border-radius:0 3px 3px 0;">'
                    f'<span style="font-size:12px;font-weight:500;color:{C_NAVY};flex:1">{row["site"]}</span>'
                    f'<span style="font-size:12px;font-weight:600;color:{c};min-width:80px;text-align:right">'
                    f'{fmt_k(row["res_r25"])}</span>'
                    f'<span style="font-size:10px;color:{ec};min-width:72px;text-align:right;padding-left:8px">'
                    f'{fmt_k(row["ecart_b"])}</span>'
                    f'</div>', unsafe_allow_html=True)

            st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
            sh("CA vs Résultat")
            pl_scatter = pl_f.copy()
            pl_scatter["ca_m"]  = pl_scatter["ca_r25"]  / 1e6
            pl_scatter["res_m"] = pl_scatter["res_r25"] / 1e6
            fig2 = px.scatter(
                pl_scatter, x="ca_m", y="res_m", text="site",
                color="res_m",
                color_continuous_scale=[[0,C_NEG],[0.5,"#ecf4fb"],[1,C_POS]],
                size=pl_scatter["ca_m"].abs().clip(lower=0.01), size_max=20,
            )
            fig2.update_traces(
                textposition="top center", textfont=dict(size=9, color=C_NAVY),
                marker=dict(line=dict(width=1.5, color="white")),
            )
            fig2.add_hline(y=0, line_dash="dot", line_color="#bcd4e8", line_width=1.5)
            chart_layout(fig2, height=260, legend=False)
            fig2.update_layout(coloraxis_showscale=False,
                               xaxis_title="CA (M€)", yaxis_title="Résultat (M€)")
            st.plotly_chart(fig2, use_container_width=True)

    # ══ ÉVOLUTION MENSUELLE ═══════════════════════════════════════════════════
    elif vue == "Évolution mensuelle":

        has_mon = not mon_f.empty

        if not has_mon:
            st.warning("Données mensuelles introuvables. Lance generate_monthly.py puis relance le dashboard.")
        else:
            MOIS_LABELS = ["Jan","Fév","Mar","Avr","Mai","Jun",
                           "Jul","Aoû","Sep","Oct","Nov","Déc"]

            # ── Sélecteur indicateur ──────────────────────────────────────────
            c1, c2, c3 = st.columns([2,2,3], gap="medium")
            with c1:
                indicateur = st.selectbox("Indicateur", [
                    "CA mensuel", "CA cumulé", "MB commerciale mensuelle",
                    "Résultat mensuel", "Résultat cumulé"
                ])
            with c2:
                granularite = st.selectbox("Granularité", [
                    "Réseau consolidé", "Par site (top 10)"
                ])

            col_map = {
                "CA mensuel":               ("ca_r25",       "ca_r24",       "ca_b25"),
                "CA cumulé":                ("ca_cumul_r25", "ca_cumul_r24", None),
                "MB commerciale mensuelle": ("mbc_r25",      None,           None),
                "Résultat mensuel":         ("res_r25",      None,           None),
                "Résultat cumulé":          ("res_cumul_r25","ca_cumul_r24", None),
            }
            col_r25, col_r24, col_b25 = col_map[indicateur]
            is_m = "M€" if "cumulé" in indicateur or "CA" in indicateur else "k€"

            # ── VUE RÉSEAU CONSOLIDÉ ──────────────────────────────────────────
            if granularite == "Réseau consolidé":
                reseau = mon_f.groupby("mois_num").agg(
                    r24=(col_r25, "sum"),
                    r23=(col_r24, "sum") if col_r24 else (col_r25, "sum"),
                    b24=(col_b25, "sum") if col_b25 else (col_r25, "sum"),
                ).reset_index()
                reseau["mois"] = reseau["mois_num"].apply(lambda x: MOIS_LABELS[x-1])

                div = 1e6 if is_m == "M€" else 1e3

                sh(f"{indicateur} — Réseau consolidé R2025 vs N-1")
                fig_m = go.Figure()
                fig_m.add_scatter(
                    x=reseau["mois"], y=reseau["r24"]/div,
                    name="R2025", mode="lines+markers",
                    line=dict(color=C_BLUE, width=2.5),
                    marker=dict(size=7, color=C_BLUE,
                                line=dict(width=1.5, color="white")),
                )
                fig_m.add_scatter(
                    x=reseau["mois"], y=reseau["r23"]/div,
                    name="N-1 R2024", mode="lines+markers",
                    line=dict(color=C_N1, width=1.5, dash="dot"),
                    marker=dict(size=5, color=C_N1),
                )
                if col_b25:
                    fig_m.add_scatter(
                        x=reseau["mois"], y=reseau["b24"]/div,
                        name="Budget", mode="lines",
                        line=dict(color=C_BUDGET, width=1.5, dash="dash"),
                    )
                fig_m.add_hline(y=0, line_color="#bcd4e8", line_width=1)
                chart_layout(fig_m, height=380)
                fig_m.update_layout(yaxis_title=is_m, xaxis_title="")
                st.plotly_chart(fig_m, use_container_width=True)

                # Barplot écart mensuel R24 vs N-1
                if col_r24:
                    sh("Écart mensuel R2025 vs N-1")
                    reseau["ecart"] = reseau["r24"] - reseau["r23"]
                    fig_e = go.Figure()
                    fig_e.add_bar(
                        x=reseau["mois"],
                        y=reseau["ecart"]/div,
                        marker_color=bar_colors(reseau["ecart"]),
                        marker_line_width=0,
                        text=[f'{"+".join([""])}{v/div:+.1f}' for v in reseau["ecart"]],
                        textposition="outside",
                        textfont=dict(size=10, color=C_NAVY),
                    )
                    fig_e.add_hline(y=0, line_color="#bcd4e8", line_width=1.5)
                    chart_layout(fig_e, height=280, legend=False)
                    fig_e.update_layout(yaxis_title=is_m)
                    st.plotly_chart(fig_e, use_container_width=True)

                # Tableau récap mensuel
                sh("Tableau mensuel consolidé")
                tbl_m = reseau[["mois","r24","r23"]].copy()
                tbl_m.columns = ["Mois", "R2025", "N-1 R2024"]
                tbl_m["Écart"] = reseau["r24"] - reseau["r23"]
                tbl_m["Écart %"] = (tbl_m["Écart"] / reseau["r23"].abs() * 100).round(1)
                for c in ["R2025","N-1 R2024","Écart"]:
                    fmt = fmt_m if is_m == "M€" else fmt_k
                    tbl_m[c] = tbl_m[c].apply(fmt)
                tbl_m["Écart %"] = tbl_m["Écart %"].apply(
                    lambda v: f'{"+" if v>=0 else ""}{v:.1f}%')

        
                st.dataframe(
                    tbl_m.set_index("Mois").style.applymap(
                        color_val, subset=["Écart","Écart %"]),
                    use_container_width=True, height=460)

            # ── VUE PAR SITE ──────────────────────────────────────────────────
            else:
                # Top 10 sites par CA annuel
                top_sites = pl_f.nlargest(10, "ca_r25")["site"].tolist()
                mon_top   = mon_f[mon_f["site"].isin(top_sites)]
                div = 1e3  # k€ pour vue par site

                sh(f"{indicateur} par site — Top 10 par CA")
                fig_s = go.Figure()
                colors_sites = [
                    C_NAVY, C_BLUE, C_STEEL,"#5dade2","#85c1e9",
                    "#aed6f1","#1e8449","#27ae60","#2ecc71","#82e0aa"
                ]
                for i, site in enumerate(top_sites):
                    site_data = mon_top[mon_top["site"] == site].sort_values("mois_num")
                    color = colors_sites[i % len(colors_sites)]
                    fig_s.add_scatter(
                        x=site_data["mois"].tolist(),
                        y=site_data[col_r25]/div,
                        name=site, mode="lines+markers",
                        line=dict(color=color, width=1.8),
                        marker=dict(size=5, color=color),
                    )
                fig_s.add_hline(y=0, line_color="#bcd4e8", line_width=1)
                chart_layout(fig_s, height=420)
                fig_s.update_layout(yaxis_title="k€", xaxis_title="",
                                    legend=dict(orientation="v", x=1.01, y=1,
                                                font=dict(size=10)))
                st.plotly_chart(fig_s, use_container_width=True)

                # Heatmap mensuel par site
                sh("Heatmap performance mensuelle (CA R2025 en k€)")
                pivot = mon_top.pivot(
                    index="site", columns="mois_num", values="ca_r25"
                ) / 1000
                pivot.columns = [MOIS_LABELS[m-1] for m in pivot.columns]
                pivot = pivot.loc[top_sites]

                fig_h = go.Figure(go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    colorscale=[[0,"#fde8e8"],[0.5,"#ecf4fb"],[1,"#d6eaf8"]],
                    colorbar=dict(title="k€", tickfont=dict(size=10)),
                    text=[[f"{v:.0f}" for v in row] for row in pivot.values],
                    texttemplate="%{text}",
                    textfont=dict(size=9, color=C_NAVY),
                ))
                chart_layout(fig_h, height=380, legend=False)
                fig_h.update_layout(
                    xaxis=dict(side="top"),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_h, use_container_width=True)

    # ══ COMPARAISON SITES ═════════════════════════════════════════════════════
    elif vue == "Comparaison sites":
        c1, c2 = st.columns([2,3], gap="medium")
        with c1:
            metric = st.selectbox("Indicateur", [
                "Résultat net","CA","MB commerciale","MB totale",
                "Taux MB commerciale (%)","Écart vs Budget","Écart vs N-1",
                "Seuil de rentabilité","Indice de sécurité (%)","Point mort (jours)",
            ])
        metric_map = {
            "Résultat net":            ("res_r25",    "res_b25",    "res_r24"),
            "CA":                      ("ca_r25",     "ca_b25",     "ca_r24"),
            "MB commerciale":          ("mbc_r25",    "mbc_b25",    "mbc_r24"),
            "MB totale":               ("mb_r25",     "mb_b25",     "mb_r24"),
            "Taux MB commerciale (%)": ("tx_mbc_r25", "tx_mbc_b25", "tx_mbc_r24"),
            "Écart vs Budget":         ("ecart_b",    None,          None),
            "Écart vs N-1":            ("ecart_n1",   None,          None),
            "Seuil de rentabilité":    ("seuil_r25",  None,          None),
            "Indice de sécurité (%)":  ("ind_secu",   None,          None),
            "Point mort (jours)":      ("pm_jours",   None,          None),
        }
        cols  = metric_map[metric]
        pl_s  = pl_f.sort_values(cols[0], ascending=False)
        is_pct = "%" in metric or metric == "Indice de sécurité (%)"
        is_days = metric == "Point mort (jours)"
        div  = 1 if (is_pct or is_days) else 1000
        sfx  = "%" if is_pct else " j" if is_days else " k€"
        delta_cols = cols[0] in ("res_r25","ecart_b","ecart_n1","marge_secu","ind_secu")

        sh(f"{metric} — R2025 / Budget / N-1")
        fig = go.Figure()
        fig.add_bar(x=pl_s["site"], y=pl_s[cols[0]]/div,
                    name="R2025", marker_color=bar_colors(pl_s[cols[0]]) if delta_cols else C_BLUE,
                    marker_line_width=0)
        if cols[1]:
            fig.add_bar(x=pl_s["site"], y=pl_s[cols[1]]/div,
                        name="Budget", marker_color=C_BUDGET, marker_line_width=0, opacity=0.6)
        if cols[2]:
            fig.add_bar(x=pl_s["site"], y=pl_s[cols[2]]/div,
                        name="N-1", marker_color=C_N1, marker_line_width=0, opacity=0.8)
        fig.add_hline(y=0, line_color="#bcd4e8", line_width=1.5)
        chart_layout(fig, height=400)
        fig.update_layout(barmode="group", yaxis_title=sfx)
        st.plotly_chart(fig, use_container_width=True)

        sh("Tableau P&L complet")
        tbl = pl_f[["site","ca_r25","mbc_r25","tx_mbc_r25","rfa_r25","stock_r25",
                     "mb_r25","ch_r25","res_r25","res_b25","res_r24","ecart_b","ecart_n1"]].copy()
        tbl.columns = ["Site","CA R25","MB Ciale","Tx MB%","RFA","Var. Stock",
                       "MB Totale","Charges","Rés. R25","Rés. B25","Rés. N-1","Écart B","Écart N-1"]
        for c in ["CA R25","MB Ciale","RFA","Var. Stock","MB Totale","Charges","Rés. R25","Rés. N-1"]:
            tbl[c] = tbl[c].apply(fmt_k)
        # Écart budget : N/A si budget absent
        tbl["Rés. B25"] = pl_f.apply(
            lambda r: fmt_k_ecart(r["res_b25"], r["res_b25"]) if r["res_b25"] != 0 else "N/A", axis=1).values
        tbl["Écart B"]  = pl_f.apply(
            lambda r: fmt_k_ecart(r["ecart_b"], r["res_b25"]), axis=1).values
        tbl["Écart N-1"]= pl_f.apply(
            lambda r: fmt_k_ecart(r["ecart_n1"], r["res_r24"]), axis=1).values
        tbl["Tx MB%"] = tbl["Tx MB%"].apply(lambda v: f"{v:.1f}%")


        st.dataframe(
            tbl.set_index("Site").style.applymap(
                color_val, subset=["Rés. R25","Rés. B25","Rés. N-1","Écart B","Écart N-1","MB Ciale","MB Totale"]),
            use_container_width=True, height=min(700, len(tbl)*36+42))

        # ── Export Excel ──────────────────────────────────────────────────────
        buf = io.BytesIO()
        tbl.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            label="⬇ Exporter le tableau P&L",
            data=buf.getvalue(),
            file_name="pl_multisite_r2024.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ══ DRILL-DOWN ════════════════════════════════════════════════════════════
    elif vue == "Drill-down charges":
        site_d  = st.selectbox("Site à analyser", sorted(sites_sel))
        ps      = pl_f[pl_f["site"] == site_d].iloc[0]
        df_site = df_f[df_f["site"] == site_d]

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.metric("CA R2025",       fmt_k(ps["ca_r25"]))
        with k2: st.metric("MB Commerciale", fmt_k(ps["mbc_r25"]), delta=f"{ps['tx_mbc_r25']:.1f}%")
        with k3: st.metric("Résultat R2025", fmt_k(ps["res_r25"]))
        with k4: st.metric("Écart Budget",   fmt_k(ps["ecart_b"]),
                            delta_color="normal" if ps["ecart_b"]>=0 else "inverse")

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        sh(f"Cascade P&L — {site_d}")

        labels   = ["CA","Achats march.","MB commerciale","RFA","Variation stock",
                    "Personnel","Loyers","Services ext.","Impôts & taxes",
                    "Dotations","Pertes clients","Autres charges","Résultat net"]
        raw_vals = [ps["ca_r25"],ps["ach_r25"],None,ps["rfa_r25"],ps["stock_r25"],
                    ps["pers_r25"],ps["loyer_r25"],ps["svc_r25"],ps["imp_r25"],
                    ps["dot_r25"],ps["perte_r25"],ps["aut_r25"],ps["res_r25"]]
        measures = ["absolute","relative","total","relative","relative",
                    "relative","relative","relative","relative",
                    "relative","relative","relative","total"]

        y_vals, t_vals = [], []
        for v, m in zip(raw_vals, measures):
            if m == "total" and v is None:
                y_vals.append(ps["mbc_r25"]/1000); t_vals.append(fmt_k(ps["mbc_r25"]))
            elif v is not None:
                y_vals.append(v/1000); t_vals.append(fmt_k(v))
            else:
                y_vals.append(0); t_vals.append("")

        fig_wf = go.Figure(go.Waterfall(
            orientation="v", measure=measures, x=labels, y=y_vals,
            connector=dict(line=dict(color="#dce8f5", width=1, dash="dot")),
            increasing=dict(marker_color=C_POS, marker_line_width=0),
            decreasing=dict(marker_color=C_NEG, marker_line_width=0),
            totals=dict(marker_color=C_BLUE, marker_line_width=0),
            text=t_vals, textposition="outside",
            textfont=dict(size=10, color=C_NAVY),
        ))
        fig_wf.add_vline(x=2.5, line_dash="dot", line_color=C_BUDGET, line_width=1.5,
                         opacity=0.6, annotation_text="↑ MB commerciale | Ajustements ↓",
                         annotation_position="top right",
                         annotation_font=dict(size=9, color=C_BUDGET))
        chart_layout(fig_wf, height=430, legend=False)
        fig_wf.update_layout(yaxis_title="k€")
        st.plotly_chart(fig_wf, use_container_width=True)

        st.markdown('<hr style="margin:18px 0;">', unsafe_allow_html=True)
        ca1, ca2 = st.columns(2, gap="medium")
        with ca1:
            sh("Répartition des charges")
            ch_v = {
                "Achats march.":   abs(ps["ach_r25"]),
                "RFA":       abs(ps["rfa_r25"]),
                "Var. stock":      abs(ps["stock_r25"]),
                "Personnel":       abs(ps["pers_r25"]),
                "Loyers":          abs(ps["loyer_r25"]),
                "Services ext.":   abs(ps["svc_r25"]),
                "Impôts & taxes":  abs(ps["imp_r25"]),
                "Dotations":       abs(ps["dot_r25"]),
                "Pertes clients":  abs(ps["perte_r25"]),
                "Autres":          abs(ps["aut_r25"]),
            }
            ch_v = {k: v for k,v in ch_v.items() if v > 100}
            fig_pie = px.pie(
                values=list(ch_v.values()), names=list(ch_v.keys()),
                color_discrete_sequence=[C_NAVY,C_BLUE,C_STEEL,"#5dade2",
                                         "#aed6f1","#85c1e9","#7f8c8d","#aab7b8"],
                hole=0.42,
            )
            fig_pie.update_traces(
                textinfo="percent+label", textfont=dict(size=10),
                marker=dict(line=dict(color="white", width=2)),
            )
            chart_layout(fig_pie, height=300, legend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with ca2:
            sh("R2025 / Budget / N-1")
            cats  = ["CA","MB ciale","MB totale","Résultat"]
            r24_v = [ps["ca_r25"], ps["mbc_r25"], ps["mb_r25"], ps["res_r25"]]
            b24_v = [ps["ca_b25"], ps["mbc_b25"], ps["mb_b25"], ps["res_b25"]]
            r23_v = [ps["ca_r24"], ps["mbc_r24"], ps["mb_r24"], ps["res_r24"]]
            fig_b = go.Figure()
            fig_b.add_bar(x=cats, y=[v/1000 for v in r24_v],
                          name="R2025", marker_color=C_BLUE, marker_line_width=0)
            fig_b.add_bar(x=cats, y=[v/1000 for v in b24_v],
                          name="Budget", marker_color=C_BUDGET, marker_line_width=0, opacity=0.65)
            fig_b.add_bar(x=cats, y=[v/1000 for v in r23_v],
                          name="N-1", marker_color=C_N1, marker_line_width=0, opacity=0.8)
            fig_b.add_hline(y=0, line_color="#bcd4e8", line_width=1.5)
            chart_layout(fig_b, height=300)
            fig_b.update_layout(barmode="group", yaxis_title="k€")
            st.plotly_chart(fig_b, use_container_width=True)

        sh("Top 15 postes de charges")
        ch_site = (
            df_site[df_site["categorie"] != "Produits"]
            .groupby(["libelle_compte","categorie"])["cumul_r25"].sum()
            .reset_index().query("cumul_r25 != 0")
            .sort_values("cumul_r25").head(15)
        )
        cat_c = {
            "Achats marchandises": C_NAVY, "RFA": C_BUDGET,
            "Variation de stock":  C_STEEL, "Charges personnel": "#2874a6",
            "Loyers & entretien":  "#1a5276", "Services extérieurs": "#5dade2",
            "Impôts & taxes":      "#7f8c8d", "Autres charges": "#aab7b8",
        }
        fig_h = px.bar(ch_site, x="cumul_r25", y="libelle_compte",
                       orientation="h", color="categorie", color_discrete_map=cat_c,
                       labels={"cumul_r25":"€","libelle_compte":""})
        fig_h.update_traces(marker_line_width=0)
        fig_h.add_vline(x=0, line_color="#bcd4e8", line_width=1.5)
        chart_layout(fig_h, height=max(320, len(ch_site)*28+60))
        st.plotly_chart(fig_h, use_container_width=True)

    # ══ POINT MORT ═══════════════════════════════════════════════════════════
    elif vue == "Point mort":

        site_d  = st.selectbox("Site à analyser", sorted(sites_sel), key="pm_site")
        ps      = pl_f[pl_f["site"] == site_d].iloc[0]
        df_site = df_f[df_f["site"] == site_d]

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.metric("CA R2025",       fmt_k(ps["ca_r25"]))
        with k2: st.metric("MB Commerciale", fmt_k(ps["mbc_r25"]), delta=f"{ps['tx_mbc_r25']:.1f}%")
        with k3: st.metric("Résultat R2025", fmt_k(ps["res_r25"]))
        with k4: st.metric("Taux MCV",       f"{ps['tx_mcv_r25']:.1f}%")
        st.markdown('<hr style="margin:14px 0;">', unsafe_allow_html=True)

        # ── POINT MORT ────────────────────────────────────────────────────────
        st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
        sh(f"Point mort — {site_d}")

        # KPIs point mort
        pm_k1, pm_k2, pm_k3, pm_k4, pm_k5 = st.columns(5, gap="small")
        kpi(pm_k1, "Charges fixes",
            fmt_k(abs(ps["ch_fixes_r25"])),
            "Personnel + loyers + impôts + dot.", "",
            rag=C_NAVY)
        kpi(pm_k2, "Taux MCV",
            f"{ps['tx_mcv_r25']:.1f}%",
            "MB ciale - ch. var. struct.", f"{fmt_k(ps['mcv_r25'])}",
            rag=C_BLUE)
        kpi(pm_k3, "Point mort CA",
            fmt_k(ps["pm_r25"]),
            "CA min. pour couvrir les fixes", "",
            rag=C_BUDGET if ps["pm_r25"] < ps["ca_r25"] else C_NEG)
        kpi(pm_k4, "Marge de sécurité",
            fmt_k(ps["ms_r25"]),
            "CA réalisé - Point mort", "",
            rag=C_POS if ps["ms_r25"] > 0 else C_NEG)
        kpi(pm_k5, "Taux de sécurité",
            f"{ps['tx_ms_r25']:.1f}%",
            "% du CA au-dessus du seuil", "",
            rag=C_POS if ps["tx_ms_r25"] > 15 else (C_BUDGET if ps["tx_ms_r25"] > 0 else C_NEG))

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # Graphique principal : jauge CA réalisé vs point mort
        pm_c1, pm_c2 = st.columns([3, 2], gap="medium")

        with pm_c1:
            sh("CA réalisé vs point mort")
            # Barplot horizontal avec 3 zones : point mort / marge de sécurité / CA
            fig_pm = go.Figure()

            # Zone point mort (charges fixes à couvrir)
            fig_pm.add_bar(
                y=[site_d], x=[ps["pm_r25"] / 1000],
                orientation="h", name="Point mort",
                marker_color=C_NEG, marker_line_width=0,
                text=[f"PM : {fmt_k(ps['pm_r25'])}"],
                textposition="inside", textfont=dict(size=11, color="white"),
            )
            # Zone marge de sécurité
            if ps["ms_r25"] > 0:
                fig_pm.add_bar(
                    y=[site_d], x=[ps["ms_r25"] / 1000],
                    orientation="h", name=f"Marge de sécurité ({ps['tx_ms_r25']:.1f}%)",
                    marker_color=C_POS, marker_line_width=0,
                    text=[fmt_k(ps["ms_r25"])],
                    textposition="inside", textfont=dict(size=11, color="white"),
                )
            else:
                # Déficit : site sous le point mort
                fig_pm.add_bar(
                    y=[site_d], x=[abs(ps["ms_r25"]) / 1000],
                    orientation="h", name=f"Déficit vs PM ({ps['tx_ms_r25']:.1f}%)",
                    marker_color=C_BUDGET, marker_line_width=0,
                    base=-abs(ps["ms_r25"]) / 1000,
                    text=[f"Déficit : {fmt_k(ps['ms_r25'])}"],
                    textposition="inside", textfont=dict(size=11, color="white"),
                )

            # Ligne CA réalisé
            fig_pm.add_vline(
                x=ps["ca_r25"] / 1000, line_color=C_BLUE, line_width=2.5, line_dash="dot",
                annotation_text=f"CA : {fmt_k(ps['ca_r25'])}",
                annotation_font=dict(size=10, color=C_BLUE),
                annotation_position="top right",
            )
            chart_layout(fig_pm, height=160, legend=True)
            fig_pm.update_layout(
                barmode="stack",
                xaxis_title="k€",
                yaxis=dict(showticklabels=False),
                margin=dict(t=40, b=30, l=8, r=8),
            )
            st.plotly_chart(fig_pm, use_container_width=True)

            # Décomposition charges fixes vs variables de structure
            sh("Décomposition : fixes vs variables de structure")
            CATS_FIXES = ["Charges personnel", "Loyers & entretien", "Impôts & taxes", "Dotations & provisions"]
            CATS_VAR   = ["Services extérieurs", "Pertes & litiges clients", "Autres charges"]

            ch_detail = []
            df_site_pm = df_f[df_f["site"] == site_d]
            for cat in CATS_FIXES:
                v = df_site_pm[df_site_pm["categorie"] == cat]["cumul_r25"].sum()
                if abs(v) > 10:
                    ch_detail.append({"Poste": cat, "Montant": v, "Type": "Fixe"})
            for cat in CATS_VAR:
                v = df_site_pm[df_site_pm["categorie"] == cat]["cumul_r25"].sum()
                if abs(v) > 10:
                    ch_detail.append({"Poste": cat, "Montant": v, "Type": "Variable struct."})

            df_ch = pd.DataFrame(ch_detail)
            if not df_ch.empty:
                fig_fv = px.bar(
                    df_ch, x="Montant", y="Poste", orientation="h",
                    color="Type",
                    color_discrete_map={"Fixe": C_NEG, "Variable struct.": C_STEEL},
                    labels={"Montant": "k€", "Poste": ""},
                )
                fig_fv.update_traces(
                    marker_line_width=0,
                    texttemplate="%{x:,.0f}",
                    textposition="outside",
                    textfont=dict(size=10, color=C_NAVY),
                )
                fig_fv.add_vline(x=0, line_color="#bcd4e8", line_width=1.5)
                chart_layout(fig_fv, height=max(260, len(df_ch)*32+60))
                fig_fv.update_layout(xaxis_title="€")
                st.plotly_chart(fig_fv, use_container_width=True)

        with pm_c2:
            sh("Sensibilité — impact d'une variation de CA")
            # Tableau d'impact : si CA varie de ±5%, ±10%, ±20%
            # Résultat = MCV × CA_new - Charges fixes
            cf_abs = abs(ps["ch_fixes_r25"])
            tx_mcv = ps["tx_mcv_r25"] / 100

            scenarios = []
            for delta in [-20, -15, -10, -5, 0, +5, +10, +15, +20]:
                ca_new  = ps["ca_r25"] * (1 + delta/100)
                res_new = ca_new * tx_mcv - cf_abs
                scenarios.append({
                    "Variation CA": f"{delta:+d}%",
                    "CA simulé":    fmt_k(ca_new),
                    "Résultat":     fmt_k(res_new),
                    "∆ Résultat":   fmt_k(res_new - ps["res_r25"]),
                })
            df_scen = pd.DataFrame(scenarios)

            # Coloration de la colonne Résultat
            styled_scen = df_scen.set_index("Variation CA").style.applymap(
                color_val, subset=["Résultat", "∆ Résultat"]
            ).apply(
                lambda row: [
                    "background:#fff9e6;font-weight:600;" if row.name == "0%" else ""
                ] * len(row), axis=1
            )
            st.dataframe(styled_scen, use_container_width=True, height=360)

            st.markdown(
                f'<div style="background:#f0f4f8;border-left:3px solid {C_BUDGET};'
                f'padding:10px 14px;border-radius:0 4px 4px 0;margin-top:8px;">'
                f'<div style="font-size:10px;font-weight:600;color:#5d7a8c;'
                f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Hypothèses</div>'
                f'<div style="font-size:11px;color:#2c3e50;line-height:1.6;">'
                f'Charges fixes considérées : Personnel + Loyers + Impôts & taxes + Dotations<br>'
                f'Charges variables de structure : Services ext. + Pertes & litiges + Autres<br>'
                f'Taux MCV = (CA − Achats − Ch. var. struct.) / CA = <b>{ps["tx_mcv_r25"]:.1f}%</b>'
                f'</div></div>',
                unsafe_allow_html=True
            )

        # ── VUE RÉSEAU : point mort tous sites ───────────────────────────────
        st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
        sh("Réseau — Point mort et marge de sécurité (tous sites)")

        pl_pm = pl_f[["site","ca_r25","pm_r25","ms_r25","tx_ms_r25","tx_mcv_r25"]].copy()
        pl_pm = pl_pm.sort_values("tx_ms_r25", ascending=True)

        fig_net = go.Figure()

        # Barre point mort (base)
        fig_net.add_bar(
            y=pl_pm["site"], x=pl_pm["pm_r25"]/1000,
            orientation="h", name="Point mort (charges fixes à couvrir)",
            marker_color=C_NEG, marker_line_width=0, opacity=0.85,
        )
        # Barre marge de sécurité (empilement)
        colors_ms = [C_POS if v >= 0 else C_BUDGET for v in pl_pm["ms_r25"]]
        fig_net.add_bar(
            y=pl_pm["site"], x=pl_pm["ms_r25"]/1000,
            orientation="h", name="Marge de sécurité",
            marker_color=colors_ms, marker_line_width=0, opacity=0.85,
            text=[f"{v:.1f}%" for v in pl_pm["tx_ms_r25"]],
            textposition="outside",
            textfont=dict(size=9, color=C_NAVY),
        )

        # Ligne CA réalisé en scatter
        fig_net.add_scatter(
            y=pl_pm["site"], x=pl_pm["ca_r25"]/1000,
            mode="markers", name="CA réalisé",
            marker=dict(color=C_BLUE, size=9, symbol="line-ns",
                        line=dict(width=2, color=C_BLUE)),
        )

        fig_net.add_vline(x=0, line_color="#bcd4e8", line_width=1)
        chart_layout(fig_net, height=max(420, len(pl_pm)*26+80))
        fig_net.update_layout(
            barmode="stack",
            xaxis_title="k€",
            legend=dict(orientation="h", y=-0.08, x=0,
                        font=dict(size=10, color="#5d7a8c"),
                        bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_net, use_container_width=True)

        # Tableau récap réseau point mort
        sh("Tableau réseau — Point mort")
        tbl_pm = pl_f[["site","ca_r25","ch_fixes_r25","tx_mcv_r25",
                        "pm_r25","ms_r25","tx_ms_r25","res_r25"]].copy()
        tbl_pm.columns = ["Site","CA R25","Ch. Fixes","Taux MCV",
                           "Point mort","Marge sécu.","Taux sécu.","Résultat"]
        for c in ["CA R25","Ch. Fixes","Point mort","Marge sécu.","Résultat"]:
            tbl_pm[c] = tbl_pm[c].apply(fmt_k)
        tbl_pm["Ch. Fixes"] = pl_f["ch_fixes_r25"].apply(lambda v: fmt_k(abs(v)))
        for c in ["Taux MCV","Taux sécu."]:
            tbl_pm[c] = pl_f["tx_mcv_r25" if c=="Taux MCV" else "tx_ms_r25"].apply(
                lambda v: f"{v:.1f}%")

        st.dataframe(
            tbl_pm.set_index("Site").style.applymap(
                color_val, subset=["Marge sécu.", "Résultat"]),
            use_container_width=True,
            height=min(700, len(tbl_pm)*36+44),
        )

        # Export
        buf_pm = io.BytesIO()
        tbl_pm.to_excel(buf_pm, index=False, engine="openpyxl")
        st.download_button(
            label="⬇ Exporter le tableau point mort",
            data=buf_pm.getvalue(),
            file_name="point_mort_r2024.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ══ TRÉSO & BFR ══════════════════════════════════════════════════════════
    elif vue == "Tréso & BFR":

        has_bal = not bal_f.empty
        has_mon = not mon_f.empty

        if not has_bal:
            st.warning("Données bilan introuvables. Lance generate_balance.py puis relance le dashboard.")
        else:
            MOIS_L = ["Jan","Fév","Mar","Avr","Mai","Jun",
                      "Jul","Aoû","Sep","Oct","Nov","Déc"]

            # Seuils d'alerte
            SEUIL_DSO   = 50   # jours
            SEUIL_DSI   = 80   # jours
            SEUIL_DPO   = 30   # jours (en-dessous = délai fournisseur trop court)

            # ── NIVEAU 1 — RÉSEAU ─────────────────────────────────────────────
            sh("Niveau 1 — Synthèse réseau")

            treso_tot  = bal_f["tresorerie"].sum()
            treso_n1   = bal_f["tresorerie_n1"].sum()
            bfr_tot    = bal_f["bfr"].sum()
            bfr_n1     = bal_f["bfr_n1"].sum()
            stock_tot  = bal_f["stock_net"].sum()
            cre_tot    = bal_f["creances_net"].sum()
            det_tot    = bal_f["dettes_frs"].sum()
            dso_moy    = bal_f["dso"].mean()
            dsi_moy    = bal_f["dsi"].mean()
            dpo_moy    = bal_f["dpo"].mean()
            couv       = treso_tot / bfr_tot * 100 if bfr_tot else 0
            nb_treso_neg = (bal_f["tresorerie"] < 0).sum()
            nb_dso_alert = (bal_f["dso"] > SEUIL_DSO).sum()
            nb_dsi_alert = (bal_f["dsi"] > SEUIL_DSI).sum()

            k1,k2,k3,k4,k5 = st.columns(5, gap="small")

            kpi(k1, "Trésorerie réseau", fmt_m(treso_tot),
                "vs N-1", fmt_m(treso_tot - treso_n1),
                rag=C_POS if treso_tot >= 0 else C_NEG)
            kpi(k2, "BFR réseau", fmt_m(bfr_tot),
                "Couverture", f"{couv:.0f}%",
                rag=C_POS if treso_tot >= bfr_tot else C_NEG)
            kpi(k3, "DSO moyen réseau", f"{dso_moy:.0f} j",
                "Alerte > 50j", f"{nb_dso_alert} sites",
                rag=C_NEG if dso_moy > SEUIL_DSO else C_BUDGET if dso_moy > 45 else C_POS)
            kpi(k4, "DSI moyen réseau", f"{dsi_moy:.0f} j",
                "Alerte > 80j", f"{nb_dsi_alert} sites",
                rag=C_NEG if dsi_moy > SEUIL_DSI else C_BUDGET if dsi_moy > 65 else C_POS)
            kpi(k5, "Sites à risque tréso", f"{nb_treso_neg} / {len(bal_f)}",
                "BFR > tréso", f"{(bal_f['bfr'] > bal_f['tresorerie']).sum()}",
                rag=C_POS if nb_treso_neg == 0 else C_NEG)

            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

            # Décomposition BFR réseau (waterfall)
            wf1, wf2 = st.columns(2, gap="medium")
            with wf1:
                sh("Décomposition BFR réseau")
                fig_bfr = go.Figure(go.Waterfall(
                    orientation="v",
                    measure=["absolute","absolute","absolute","total"],
                    x=["Stock net","Créances clients","- Dettes fourn.","BFR"],
                    y=[stock_tot/1e3, cre_tot/1e3, -det_tot/1e3, bfr_tot/1e3],
                    connector=dict(line=dict(color="#dce8f5", width=1, dash="dot")),
                    increasing=dict(marker_color=C_NEG, marker_line_width=0),
                    decreasing=dict(marker_color=C_POS, marker_line_width=0),
                    totals=dict(marker_color=C_BLUE, marker_line_width=0),
                    text=[fmt_k(v) for v in [stock_tot, cre_tot, -det_tot, bfr_tot]],
                    textposition="outside",
                    textfont=dict(size=10, color=C_NAVY),
                ))
                chart_layout(fig_bfr, height=320, legend=False)
                fig_bfr.update_layout(yaxis_title="k€")
                st.plotly_chart(fig_bfr, use_container_width=True)

            with wf2:
                sh("Évolution mensuelle tréso & BFR réseau")
                if has_mon:
                    mon_net = mon_f.groupby("mois_num").agg(
                        bfr=("bfr","sum"),
                        treso=("tresorerie","sum"),
                    ).reset_index()
                    mon_net["mois"] = mon_net["mois_num"].apply(lambda x: MOIS_L[x-1])
                    fig_ev = go.Figure()
                    fig_ev.add_scatter(
                        x=mon_net["mois"], y=mon_net["treso"]/1e3,
                        name="Trésorerie", mode="lines+markers",
                        line=dict(color=C_POS, width=2.5),
                        marker=dict(size=6, color=C_POS,
                                    line=dict(width=1.5, color="white")),
                        fill="tozeroy", fillcolor="rgba(30,132,73,0.07)",
                    )
                    fig_ev.add_scatter(
                        x=mon_net["mois"], y=mon_net["bfr"]/1e3,
                        name="BFR", mode="lines+markers",
                        line=dict(color=C_BUDGET, width=2, dash="dash"),
                        marker=dict(size=6, color=C_BUDGET,
                                    symbol="diamond",
                                    line=dict(width=1.5, color="white")),
                    )
                    fig_ev.add_hline(y=0, line_color="#bcd4e8", line_width=1)
                    chart_layout(fig_ev, height=320)
                    fig_ev.update_layout(yaxis_title="k€")
                    st.plotly_chart(fig_ev, use_container_width=True)
                else:
                    st.info("Lance generate_monthly.py pour activer l'évolution mensuelle.")

            st.markdown('<hr style="margin:16px 0;">', unsafe_allow_html=True)

            # ── NIVEAU 2 — COMPARAISON SITES ─────────────────────────────────
            sh("Niveau 2 — Comparaison sites")

            indicateur_bfr = st.selectbox(
                "Indicateur à comparer",
                ["Trésorerie", "BFR", "DSO (jours)", "DSI (jours)",
                 "DPO (jours)", "Stock net", "Créances nettes",
                 "Taux dépréciation stock (%)", "Taux créances douteuses (%)"],
                key="indic_bfr"
            )
            col_bfr_map = {
                "Trésorerie":                   ("tresorerie",     "tresorerie_n1"),
                "BFR":                           ("bfr",            "bfr_n1"),
                "DSO (jours)":                   ("dso",            "dso_n1" if "dso_n1" in bal_f.columns else None),
                "DSI (jours)":                   ("dsi",            None),
                "DPO (jours)":                   ("dpo",            None),
                "Stock net":                     ("stock_net",      "stock_n1"),
                "Créances nettes":               ("creances_net",   "creances_n1"),
                "Taux dépréciation stock (%)":   ("tx_depreciation",None),
                "Taux créances douteuses (%)":   ("tx_douteux",     None),
            }
            col_r, col_n1 = col_bfr_map[indicateur_bfr]
            is_days = "jours" in indicateur_bfr
            is_pct  = "%" in indicateur_bfr
            div_b   = 1 if (is_days or is_pct) else 1000
            sfx_b   = " j" if is_days else "%" if is_pct else " k€"

            bal_s = bal_f.sort_values(col_r, ascending=not is_days)

            # Seuil d'alerte sur les délais
            seuil_map = {"dso": SEUIL_DSO, "dsi": SEUIL_DSI, "dpo": SEUIL_DPO}
            seuil_val = seuil_map.get(col_r)

            fig_cmp = go.Figure()
            colors_r = []
            for v in bal_s[col_r]:
                if seuil_val and col_r == "dso" and v > seuil_val:
                    colors_r.append(C_NEG)
                elif seuil_val and col_r == "dsi" and v > seuil_val:
                    colors_r.append(C_BUDGET)
                elif col_r == "tresorerie":
                    colors_r.append(C_POS if v >= 0 else C_NEG)
                else:
                    colors_r.append(C_BLUE)

            fig_cmp.add_bar(
                x=bal_s["site"], y=bal_s[col_r]/div_b,
                name="R2025", marker_color=colors_r, marker_line_width=0,
            )
            if col_n1 and col_n1 in bal_f.columns:
                fig_cmp.add_bar(
                    x=bal_s["site"], y=bal_s[col_n1]/div_b,
                    name="N-1", marker_color=C_N1, marker_line_width=0, opacity=0.7,
                )
            if seuil_val:
                fig_cmp.add_hline(
                    y=seuil_val, line_dash="dot", line_color=C_NEG,
                    line_width=1.5, opacity=0.7,
                    annotation_text=f"Seuil alerte {seuil_val}{sfx_b}",
                    annotation_font=dict(size=9, color=C_NEG),
                    annotation_position="top right",
                )
            fig_cmp.add_hline(y=0, line_color="#bcd4e8", line_width=1)
            chart_layout(fig_cmp, height=340)
            fig_cmp.update_layout(barmode="group", yaxis_title=sfx_b)
            st.plotly_chart(fig_cmp, use_container_width=True)

            # Alertes automatiques
            sh("Alertes réseau")
            alertes = []
            for _, row in bal_f.iterrows():
                if row["tresorerie"] < 0:
                    alertes.append((C_NEG, "⚠ Tréso négative",
                                    row["site"], fmt_k(row["tresorerie"])))
                if row["dso"] > SEUIL_DSO:
                    alertes.append((C_NEG, f"⚠ DSO > {SEUIL_DSO}j",
                                    row["site"], f"{row['dso']:.0f}j"))
                if row["dsi"] > SEUIL_DSI:
                    alertes.append((C_BUDGET, f"⚠ DSI > {SEUIL_DSI}j",
                                    row["site"], f"{row['dsi']:.0f}j"))
                if row["bfr"] > row["tresorerie"] * 1.5:
                    alertes.append((C_BUDGET, "⚠ BFR > 1.5× tréso",
                                    row["site"], fmt_k(row["bfr"] - row["tresorerie"])))

            if alertes:
                cols_al = st.columns(min(len(alertes), 4), gap="small")
                for i, (color, label, site_al, val) in enumerate(alertes[:8]):
                    cols_al[i % 4].markdown(
                        f'<div style="background:#fff;border-left:4px solid {color};'
                        f'border:1px solid {"#f5c6c6" if color==C_NEG else "#fae8c0"};'
                        f'border-left:4px solid {color};padding:8px 12px;border-radius:0 4px 4px 0;">'
                        f'<div style="font-size:10px;font-weight:600;color:{color};">{label}</div>'
                        f'<div style="font-size:13px;font-weight:600;color:{C_NAVY};">{site_al}</div>'
                        f'<div style="font-size:11px;color:#7f8c8d;">{val}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("Aucune alerte — tous les indicateurs sont dans les seuils.")

            st.markdown('<hr style="margin:16px 0;">', unsafe_allow_html=True)

            # ── NIVEAU 3 — DRILL-DOWN SITE ────────────────────────────────────
            sh("Niveau 3 — Drill-down site")
            site_bfr = st.selectbox("Site à analyser", sorted(sites_sel), key="site_bfr")
            bs = bal_f[bal_f["site"] == site_bfr].iloc[0]

            # KPIs site
            k1,k2,k3,k4,k5,k6 = st.columns(6, gap="small")
            kpi(k1, "Trésorerie",    fmt_k(bs["tresorerie"]),
                "N-1", fmt_k(bs["tresorerie_n1"]),
                rag=C_POS if bs["tresorerie"] >= 0 else C_NEG)
            kpi(k2, "BFR",           fmt_k(bs["bfr"]),
                "N-1", fmt_k(bs["bfr_n1"]),
                rag=C_POS if bs["tresorerie"] >= bs["bfr"] else C_NEG)
            kpi(k3, "DSO clients",   f"{bs['dso']:.0f} j",
                "N-1", f"{bs.get('dso_n1', bs['dso']):.0f} j",
                rag=C_NEG if bs["dso"] > SEUIL_DSO else C_POS)
            kpi(k4, "DSI stock",     f"{bs['dsi']:.0f} j",
                "N-1", f"{bs['stock_n1']:,.0f} €",
                rag=C_NEG if bs["dsi"] > SEUIL_DSI else C_POS)
            kpi(k5, "DPO fourn.",    f"{bs['dpo']:.0f} j",
                "Taux douteux", f"{bs['tx_douteux']:.1f}%",
                rag=C_POS if bs["dpo"] > SEUIL_DPO else C_BUDGET)
            kpi(k6, "Couverture BFR",
                f"{bs['tresorerie']/bs['bfr']*100:.0f}%" if bs["bfr"] else "—",
                "Tx dépréc. stock", f"{bs['tx_depreciation']:.1f}%",
                rag=C_POS if bs["tresorerie"] >= bs["bfr"] else C_NEG)

            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

            da1, da2 = st.columns(2, gap="medium")

            with da1:
                sh(f"Décomposition BFR — {site_bfr}")
                # Waterfall BFR site
                fig_wbfr = go.Figure(go.Waterfall(
                    orientation="v",
                    measure=["absolute","absolute","absolute","total"],
                    x=["Stock net","Créances nettes","- Dettes fourn.","BFR"],
                    y=[bs["stock_net"]/1e3, bs["creances_net"]/1e3,
                       -bs["dettes_frs"]/1e3, bs["bfr"]/1e3],
                    connector=dict(line=dict(color="#dce8f5", width=1, dash="dot")),
                    increasing=dict(marker_color=C_NEG, marker_line_width=0),
                    decreasing=dict(marker_color=C_POS, marker_line_width=0),
                    totals=dict(marker_color=C_BLUE, marker_line_width=0),
                    text=[fmt_k(v) for v in [bs["stock_net"], bs["creances_net"],
                                              -bs["dettes_frs"], bs["bfr"]]],
                    textposition="outside",
                    textfont=dict(size=10, color=C_NAVY),
                ))
                # Tréso en ligne de référence
                fig_wbfr.add_hline(
                    y=bs["tresorerie"]/1e3, line_dash="dot",
                    line_color=C_POS, line_width=2, opacity=0.7,
                    annotation_text=f"Tréso : {fmt_k(bs['tresorerie'])}",
                    annotation_font=dict(size=9, color=C_POS),
                    annotation_position="top right",
                )
                chart_layout(fig_wbfr, height=340, legend=False)
                fig_wbfr.update_layout(yaxis_title="k€")
                st.plotly_chart(fig_wbfr, use_container_width=True)

            with da2:
                sh(f"Stock & Créances — {site_bfr}")
                # Comparaison brut vs net + indicateurs qualité
                cats  = ["Stock brut","Stock net","Créances brutes","Créances nettes"]
                vals  = [bs["stock_brut"], bs["stock_net"],
                         bs["creances_brut"], bs["creances_net"]]
                cols_b= [C_N1, C_BLUE, C_N1, C_BLUE]

                fig_qual = go.Figure()
                fig_qual.add_bar(
                    x=cats, y=[v/1e3 for v in vals],
                    marker_color=cols_b, marker_line_width=0,
                    text=[fmt_k(v) for v in vals],
                    textposition="outside",
                    textfont=dict(size=10, color=C_NAVY),
                )
                # Annotations taux
                fig_qual.add_annotation(
                    x=1, y=max(vals)/1e3*0.5,
                    text=f"Tx dépréc.<br>{bs['tx_depreciation']:.1f}%",
                    showarrow=False, font=dict(size=10, color=C_NEG),
                    bgcolor="white", bordercolor=C_NEG, borderwidth=1,
                )
                fig_qual.add_annotation(
                    x=3, y=max(vals)/1e3*0.5,
                    text=f"Tx douteux<br>{bs['tx_douteux']:.1f}%",
                    showarrow=False, font=dict(size=10, color=C_BUDGET),
                    bgcolor="white", bordercolor=C_BUDGET, borderwidth=1,
                )
                chart_layout(fig_qual, height=340, legend=False)
                fig_qual.update_layout(yaxis_title="k€")
                st.plotly_chart(fig_qual, use_container_width=True)

            # Évolution mensuelle tréso & BFR du site
            if has_mon:
                sh(f"Évolution mensuelle tréso & BFR — {site_bfr}")
                mon_site = mon_f[mon_f["site"] == site_bfr].sort_values("mois_num")
                fig_ms = go.Figure()
                fig_ms.add_scatter(
                    x=mon_site["mois"], y=mon_site["tresorerie"]/1e3,
                    name="Trésorerie", mode="lines+markers",
                    line=dict(color=C_POS, width=2.5),
                    marker=dict(size=7, color=C_POS,
                                line=dict(width=1.5, color="white")),
                    fill="tozeroy", fillcolor="rgba(30,132,73,0.07)",
                )
                fig_ms.add_scatter(
                    x=mon_site["mois"], y=mon_site["bfr"]/1e3,
                    name="BFR", mode="lines+markers",
                    line=dict(color=C_BUDGET, width=2, dash="dash"),
                    marker=dict(size=6, color=C_BUDGET, symbol="diamond",
                                line=dict(width=1.5, color="white")),
                )
                fig_ms.add_scatter(
                    x=mon_site["mois"], y=mon_site["stock"]/1e3,
                    name="Stock net", mode="lines",
                    line=dict(color=C_STEEL, width=1.5, dash="dot"),
                )
                fig_ms.add_scatter(
                    x=mon_site["mois"], y=mon_site["creances"]/1e3,
                    name="Créances", mode="lines",
                    line=dict(color=C_N1, width=1.5, dash="dot"),
                )
                fig_ms.add_hline(y=0, line_color="#bcd4e8", line_width=1)
                chart_layout(fig_ms, height=360)
                fig_ms.update_layout(yaxis_title="k€")
                st.plotly_chart(fig_ms, use_container_width=True)

            # Comparaison vs N-1 site
            sh(f"Comparaison R2025 vs N-1 — {site_bfr}")
            comp_labels = ["Tréso","BFR","Stock net","Créances nettes","Dettes fourn."]
            comp_r25 = [bs["tresorerie"], bs["bfr"], bs["stock_net"],
                        bs["creances_net"], bs["dettes_frs"]]
            comp_n1  = [bs["tresorerie_n1"], bs["bfr_n1"], bs["stock_n1"],
                        bs["creances_n1"], bs["dettes_n1"]]
            fig_n1 = go.Figure()
            fig_n1.add_bar(x=comp_labels, y=[v/1e3 for v in comp_r25],
                           name="R2025", marker_color=C_BLUE, marker_line_width=0)
            fig_n1.add_bar(x=comp_labels, y=[v/1e3 for v in comp_n1],
                           name="N-1", marker_color=C_N1, marker_line_width=0,
                           opacity=0.75)
            fig_n1.add_hline(y=0, line_color="#bcd4e8", line_width=1)
            chart_layout(fig_n1, height=300)
            fig_n1.update_layout(barmode="group", yaxis_title="k€")
            st.plotly_chart(fig_n1, use_container_width=True)

    # ══ DÉTAIL COMPTABLE ══════════════════════════════════════════════════════
    elif vue == "Détail comptable":
        c1, c2 = st.columns(2, gap="medium")
        with c1: site_det = st.selectbox("Site", sorted(sites_sel))
        with c2: cat_det  = st.selectbox("Catégorie", ["Toutes"] + sorted(df["categorie"].unique()))

        df_det = df_f[df_f["site"] == site_det].copy()
        if cat_det != "Toutes":
            df_det = df_det[df_det["categorie"] == cat_det]

        df_det = (
            df_det.groupby(["Compte","libelle_compte","categorie"])
            [["cumul_r25","cumul_b25","cumul_r24"]].sum().reset_index()
            .query("cumul_r25 != 0").sort_values("cumul_r25")
        )

        sh(f"Détail — {site_det}" + (f" · {cat_det}" if cat_det != "Toutes" else ""))
        df_show = df_det[["Compte","libelle_compte","categorie","cumul_r25","cumul_b25","cumul_r24"]].copy()
        df_show.columns = ["Compte","Libellé","Catégorie","Cumul R25","Cumul B24","Cumul N-1"]
        for c in ["Cumul R25","Cumul B24","Cumul N-1"]:
            df_show[c] = df_show[c].apply(fmt_k)


        st.dataframe(
            df_show.set_index("Compte").style.applymap(color_val, subset=["Cumul R25","Cumul B24","Cumul N-1"]),
            use_container_width=True, height=400)

        fig_det = px.bar(
            df_det.head(20), x="cumul_r25", y="libelle_compte",
            orientation="h", color="categorie",
            color_discrete_map={
                "Produits":"#1e8449","Achats marchandises":C_NAVY,"RFA":C_BUDGET,
                "Variation de stock":C_STEEL,"Charges personnel":"#2874a6",
                "Loyers & entretien":"#1a5276","Services extérieurs":"#5dade2",
                "Impôts & taxes":"#7f8c8d","Autres charges":"#aab7b8",
            },
            labels={"cumul_r25":"Cumul R24 (€)","libelle_compte":""},
        )
        fig_det.update_traces(marker_line_width=0)
        fig_det.add_vline(x=0, line_color="#bcd4e8", line_width=1.5)
        chart_layout(fig_det, height=460)
        st.plotly_chart(fig_det, use_container_width=True)


if __name__ == "__main__":
    main()
