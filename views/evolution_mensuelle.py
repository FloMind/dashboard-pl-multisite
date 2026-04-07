"""views/evolution_mensuelle.py — extrait fidèle du dashboard_pl.py original"""
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
