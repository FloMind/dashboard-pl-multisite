"""views/drill_down.py — extrait fidèle du dashboard_pl.py original"""
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
