"""
components/formatters.py — Fonctions de formatage partagées
fmt_k, fmt_m, fmt_pct, color_val, pm_mois_label
"""

from core.constants import C_POS, C_NEG


def fmt_k(v: float, dec: int = 0) -> str:
    """Formate en k€. Retourne '—' si valeur négligeable."""
    if v is None:
        return "—"
    k = v / 1000
    if abs(k) < 0.05:
        return "—"
    return f"{'+' if k > 0 else ''}{k:,.{dec}f} k€".replace(",", " ")


def fmt_m(v: float, dec: int = 1) -> str:
    """Formate en M€ pour les agrégats réseau."""
    if v is None:
        return "—"
    m = v / 1_000_000
    if abs(m) < 0.005:
        return "—"
    return f"{'+' if m > 0 else ''}{m:,.{dec}f} M€".replace(",", " ")


def fmt_k_ecart(v: float, ref: float, dec: int = 0) -> str:
    """Écart vs référence : affiche N/A si référence absente."""
    if ref == 0:
        return "N/A"
    return fmt_k(v, dec)


def fmt_pct(v: float, dec: int = 1, signed: bool = False) -> str:
    """Formate un pourcentage."""
    if v is None:
        return "—"
    prefix = "+" if signed and v > 0 else ""
    return f"{prefix}{v:.{dec}f}%"


def fmt_jours(v: float) -> str:
    """Formate un délai en jours."""
    if v is None:
        return "—"
    return f"{v:.0f} j"


def color_val(v) -> str:
    """Couleur CSS pour une valeur k€, M€ ou % — vert si positif, rouge si négatif."""
    try:
        n = float(
            str(v)
            .replace(" k€", "").replace(" M€", "").replace("%", "")
            .replace("+", "").replace(" ", "").replace(",", ".")
            .replace("—", "0")
        )
        if n > 0:
            return f"color:{C_POS};font-weight:500"
        if n < 0:
            return f"color:{C_NEG};font-weight:500"
    except Exception:
        pass
    return ""


def pm_mois_label(jours: float) -> str:
    """Convertit un nombre de jours en mois approximatif."""
    MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
            "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    if jours is None or jours >= 365:
        return "Non atteint"
    m = min(int(jours / 30.4), 11)
    return MOIS[m]


def rag_color(rag: str) -> str:
    """Retourne la couleur CSS selon le signal RAG."""
    return {
        "vert":   C_POS,
        "orange": "#d68910",
        "rouge":  C_NEG,
    }.get(rag, C_NEG)


def fmt_ecart_pct(valeur: float, reference: float, dec: int = 1) -> str:
    """Calcule et formate l'écart % entre valeur et référence."""
    if not reference or reference == 0:
        return "N/A"
    ecart = (valeur - reference) / abs(reference) * 100
    prefix = "+" if ecart > 0 else ""
    return f"{prefix}{ecart:.{dec}f}%"
