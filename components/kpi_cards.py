"""
components/kpi_cards.py — Cartes KPI réutilisables
kpi(), sh(), rag_badge()
Identiques en signature au P&L dashboard pour cohérence visuelle.
"""

import streamlit as st
from core.constants import C_NAVY, C_BLUE, C_POS, C_NEG, C_WARN, C_N1


def kpi(
    col,
    label: str,
    valeur: str,
    sous_label: str,
    sous_val: str,
    evol: float = None,
    rag: str = None,
    big: bool = False,
) -> None:
    """
    Carte KPI avec border-top colorée selon RAG.
    evol  : float en % pour afficher la flèche (optionnel)
    rag   : couleur CSS de la border-top (défaut C_BLUE)
    """
    rag     = rag or C_BLUE
    fs_val  = "26px" if big else "20px"
    pad     = "16px 18px" if big else "12px 14px"
    mb      = "8px"  if big else "5px"

    fleche = ""
    evol_s = ""
    if evol is not None:
        fleche = "▲" if evol >= 0 else "▼"
        c      = C_POS if evol >= 0 else C_NEG
        evol_s = (
            f'<span style="font-size:11px;font-weight:600;color:{c};">'
            f'{fleche} {abs(evol):.1f}%</span>'
        )

    col.markdown(
        f'<div style="background:#fff;border:1px solid #dce8f5;'
        f'border-top:4px solid {rag};border-radius:4px;padding:{pad};">'
        f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.09em;color:#5d7a8c;margin-bottom:{mb};">{label}</div>'
        f'<div style="font-size:{fs_val};font-weight:600;color:{C_NAVY};'
        f'line-height:1.15;">{valeur}</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-top:{mb};">'
        f'<span style="font-size:11px;color:#7f8c8d;">'
        f'{sous_label} : {sous_val}</span>'
        f'{evol_s}</div></div>',
        unsafe_allow_html=True,
    )


def sh(label: str) -> None:
    """Section header — bandeau bleu marine avec label en majuscules."""
    st.markdown(
        f'<div style="background:#0d2b45;color:white;padding:7px 14px;'
        f'border-radius:3px;font-size:10px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">'
        f'{label}</div>',
        unsafe_allow_html=True,
    )


def rag_badge(label: str, valeur: str, rag: str = "vert") -> str:
    """Retourne le HTML d'un badge RAG inline."""
    colors = {
        "vert":   ("#e8f5e9", "#1e8449"),
        "orange": ("#fef9e7", "#d68910"),
        "rouge":  ("#fdecea", "#c0392b"),
    }
    bg, fg = colors.get(rag, colors["vert"])
    return (
        f'<span style="background:{bg};color:{fg};font-size:11px;'
        f'font-weight:600;padding:2px 8px;border-radius:4px;">'
        f'{label} {valeur}</span>'
    )


def alerte_card(col, color: str, label: str, site: str, valeur: str) -> None:
    """Carte d'alerte compacte (rouge ou orange)."""
    border_color = "#f5c6c6" if color == C_NEG else "#fae8c0"
    col.markdown(
        f'<div style="background:#fff;border:1px solid {border_color};'
        f'border-left:4px solid {color};padding:8px 12px;'
        f'border-radius:0 4px 4px 0;margin-bottom:4px;">'
        f'<div style="font-size:10px;font-weight:600;color:{color};">{label}</div>'
        f'<div style="font-size:13px;font-weight:600;color:#0d2b45;">{site}</div>'
        f'<div style="font-size:11px;color:#7f8c8d;">{valeur}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def benchmark_badge(valeur: float, benchmark: float, label_bench: str = "médiane secteur") -> str:
    """Badge comparaison vs benchmark — vert si au-dessus, rouge si en-dessous."""
    if benchmark and benchmark != 0:
        ecart = valeur - benchmark
        color = C_POS if ecart >= 0 else C_NEG
        sign  = "+" if ecart >= 0 else ""
        return (
            f'<span style="font-size:11px;color:{color};font-weight:500;">'
            f'{sign}{ecart:.1f}pp vs {label_bench}</span>'
        )
    return ""
