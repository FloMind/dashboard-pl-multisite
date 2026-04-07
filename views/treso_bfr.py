"""views/treso_bfr.py — extrait fidèle du dashboard_pl.py original"""
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
