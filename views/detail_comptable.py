"""views/detail_comptable.py — extrait fidèle du dashboard_pl.py original"""
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.constants import (C_NAVY, C_BLUE, C_STEEL, C_ICE, C_POS, C_NEG,
                             C_BUDGET, C_N1, C_GRID, FONT, COLORS_VERSION,
                             C_WARN, MOIS_LABELS, CAT_COLORS)
from components.kpi_cards import kpi, sh
from components.charts import chart_layout, bar_colors
from components.formatters import fmt_k, fmt_m, fmt_k_ecart, color_val


def render(pl_f, df_f, bal_f, mon_f):
    sites_sel = sorted(pl_f["site"].unique())
    c1, c2 = st.columns(2, gap="medium")
    with c1: site_det = st.selectbox("Site", sorted(sites_sel))
    with c2: cat_det  = st.selectbox("Catégorie", ["Toutes"] + sorted(df_f["categorie"].unique()))

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
    df_show.columns = ["Compte","Libellé","Catégorie","Cumul R25","Cumul B25","Cumul N-1"]
    for c in ["Cumul R25","Cumul B25","Cumul N-1"]:
        df_show[c] = df_show[c].apply(fmt_k)


    st.dataframe(
        df_show.set_index("Compte").style.applymap(color_val, subset=["Cumul R25","Cumul B25","Cumul N-1"]),
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
        labels={"cumul_r25":"Cumul R25 (€)","libelle_compte":""},
    )
    fig_det.update_traces(marker_line_width=0)
    fig_det.add_vline(x=0, line_color="#bcd4e8", line_width=1.5)
    chart_layout(fig_det, height=460)
    st.plotly_chart(fig_det, use_container_width=True)


if __name__ == "__main__":
    main()

