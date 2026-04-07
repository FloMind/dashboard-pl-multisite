"""views/comparaison_sites.py — extrait fidèle du dashboard_pl.py original"""
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
        tbl.set_index("Site").style.map(
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
