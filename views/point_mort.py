"""views/point_mort.py — extrait fidèle du dashboard_pl.py original"""
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
        styled_scen = df_scen.set_index("Variation CA").style.map(
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
        tbl_pm.set_index("Site").style.map(
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
