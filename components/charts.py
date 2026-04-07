"""
components/charts.py — Fonctions graphiques partagées
chart_layout, bar_colors, waterfall, couleurs par version
"""

import plotly.graph_objects as go
from core.constants import (
    C_NAVY, C_BLUE, C_STEEL, C_ICE,
    C_POS, C_NEG, C_WARN, C_N1, C_GRID,
    FONT,
)

# Couleurs par version — non utilisées dans le P&L dashboard
COLORS_VERSION = {}


def chart_layout(
    fig: go.Figure,
    height: int = 380,
    title: str = "",
    legend: bool = True,
    yaxis_title: str = "",
    xaxis_title: str = "",
) -> go.Figure:
    """Applique le style corporate à un graphique Plotly."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=12, family=FONT, color=C_NAVY),
            x=0, y=0.98,
        ),
        height=height,
        font=dict(family=FONT, size=11, color="#2c3e50"),
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=36 if title else 14, b=28, l=8, r=8),
        showlegend=legend,
        legend=dict(
            orientation="h", y=-0.18, x=0,
            font=dict(size=10, color="#5d7a8c"),
            bgcolor="rgba(0,0,0,0)",
        ),
        yaxis_title=yaxis_title,
        xaxis_title=xaxis_title,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=C_GRID, gridwidth=1,
        zeroline=False, linecolor="#dce8f5",
        tickfont=dict(size=10, color="#5d7a8c"),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=C_GRID, gridwidth=1,
        zeroline=True, zerolinecolor="#bcd4e8", zerolinewidth=1.5,
        tickfont=dict(size=10, color="#5d7a8c"),
    )
    return fig


def bar_colors(series) -> list:
    """Couleur verte/rouge selon signe des valeurs."""
    return [C_POS if v >= 0 else C_NEG for v in series]


def version_color(version: str) -> str:
    """Couleur associée à une version budgétaire."""
    return COLORS_VERSION.get(version, C_BLUE)


def make_waterfall(
    labels: list,
    values: list,
    measures: list,
    title: str = "",
    height: int = 430,
    yaxis_title: str = "k€",
    text_values: list = None,
) -> go.Figure:
    """
    Crée un waterfall chart standard.
    measures : liste de "absolute" | "relative" | "total"
    """
    from components.formatters import fmt_k
    text = text_values or [fmt_k(v) for v in values]

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=[v / 1000 for v in values],
        connector=dict(line=dict(color="#dce8f5", width=1, dash="dot")),
        increasing=dict(marker_color=C_POS, marker_line_width=0),
        decreasing=dict(marker_color=C_NEG, marker_line_width=0),
        totals=dict(marker_color=C_BLUE, marker_line_width=0),
        text=text,
        textposition="outside",
        textfont=dict(size=10, color=C_NAVY),
    ))
    chart_layout(fig, height=height, title=title, legend=False,
                 yaxis_title=yaxis_title)
    return fig


def make_sig_waterfall(sig_row: dict, site: str = "") -> go.Figure:
    """
    Waterfall SIG standard : CA → Marge com → MB totale → EBE → REX → RCAI → Résultat net.
    sig_row : dict ou Series avec les colonnes SIG.
    """
    from components.formatters import fmt_k

    labels   = ["CA", "- Achats", "Marge com.", "+ RFA/Stock",
                 "MB totale", "- Ch. struct.", "EBE/EBITDA",
                 "- Dotations", "REX/EBIT", "+/- Fin.", "RCAI",
                 "- IS", "Résultat net"]
    measures = ["absolute", "relative", "total", "relative",
                "total", "relative", "total",
                "relative", "total", "relative", "total",
                "relative", "total"]

    ca      = sig_row.get("ca", 0)
    achats  = sig_row.get("achats", 0)          # négatif
    rfa_vs  = sig_row.get("rfa", 0) + sig_row.get("var_stock", 0)
    ch_str  = (sig_row.get("pers", 0) + sig_row.get("loyers", 0) +
               sig_row.get("services", 0) + sig_row.get("energie", 0) +
               sig_row.get("imp_taxes", 0))     # négatif
    dot     = sig_row.get("dotations", 0)       # négatif
    fin_net = sig_row.get("prod_fin", 0) + sig_row.get("ch_fin", 0)
    is_     = sig_row.get("is", 0)              # négatif

    marge_com = sig_row.get("marge_commerciale", ca + achats)
    mb_tot    = sig_row.get("mb_totale", marge_com + rfa_vs)
    ebe       = sig_row.get("ebe", mb_tot + ch_str)
    rex       = sig_row.get("rex", ebe + dot)
    rcai      = sig_row.get("rcai", rex + fin_net)
    res_net   = sig_row.get("resultat_net", rcai + is_)

    raw = [ca, achats, marge_com, rfa_vs,
           mb_tot, ch_str, ebe,
           dot, rex, fin_net, rcai,
           is_, res_net]

    text = [fmt_k(v) for v in raw]

    return make_waterfall(labels, raw, measures,
                          title=f"Cascade SIG{' — ' + site if site else ''}",
                          height=480)


def make_version_lines(
    df_monthly,
    kpi: str,
    versions: list,
    mois_col: str = "mois_label",
    div: float = 1000,
    height: int = 380,
    yaxis_title: str = "k€",
) -> go.Figure:
    """
    Courbes multi-versions pour un KPI mensuel.
    df_monthly : agrégé réseau (groupby mois_num)
    """
    fig = go.Figure()
    for version in versions:
        color = version_color(version)
        dash  = "dot" if version == "Budget" else (
                "dash" if version.startswith("RF") else "solid")
        width = 2.5 if version == "Réalisé" else 1.8

        vdata = df_monthly[df_monthly["version"] == version] if "version" in df_monthly.columns \
                else df_monthly

        fig.add_scatter(
            x=vdata[mois_col] if mois_col in vdata.columns else vdata.index,
            y=vdata[kpi] / div,
            name=version,
            mode="lines+markers",
            line=dict(color=color, width=width, dash=dash),
            marker=dict(size=6, color=color,
                        line=dict(width=1.5, color="white")),
        )

    fig.add_hline(y=0, line_color="#bcd4e8", line_width=1)
    chart_layout(fig, height=height, yaxis_title=yaxis_title)
    return fig
