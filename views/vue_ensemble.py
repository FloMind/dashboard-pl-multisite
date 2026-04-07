"""views/vue_ensemble.py - extrait fidèle du dashboard_pl.py original"""
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
    kpi(c1, "CA Réalisé 2025",
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


    subset = ["Rés. R25","Écart B","Écart N-1","Tréso"] if has_bal \
              else ["Rés. R25","Écart B","Écart N-1"]
    try:
        # Pandas 2.1+
        styled = tbl_dg.set_index("Site").style.map(color_val, subset=subset)
    except AttributeError:
        # Pandas < 2.1
        styled = tbl_dg.set_index("Site").style.map(color_val, subset=subset)
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
            name="Résultat R25",
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
