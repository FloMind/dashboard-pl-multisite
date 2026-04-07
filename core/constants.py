"""
core/constants.py — Constantes partagées dashboard P&L multi-sites
"""

# ── PALETTE ───────────────────────────────────────────────────────────────────
C_NAVY   = "#0d2b45"
C_BLUE   = "#1a5f8a"
C_STEEL  = "#2980b9"
C_ICE    = "#d6eaf8"
C_POS    = "#1e8449"
C_NEG    = "#c0392b"
C_BUDGET = "#d68910"
C_WARN   = "#d68910"
C_N1     = "#7f8c8d"
C_GRID   = "rgba(13,43,69,0.06)"
FONT     = "Inter, Segoe UI, Arial, sans-serif"

# Couleurs par version — P&L n'a pas de versions budgétaires
# mais charts.py partagé en a besoin
COLORS_VERSION = {
    "Budget":  "#d68910",
    "RF_T1":   "#8e44ad",
    "RF_T2":   "#e67e22",
    "RF_T3":   "#d35400",
    "Réalisé": "#0d2b45",
}

# ── FICHIERS DATA ─────────────────────────────────────────────────────────────
FILE_PL  = "data/sample_data.xlsx"
FILE_BAL = "data/sample_balance.xlsx"
FILE_MON = "data/sample_monthly.xlsx"

# ── MOIS ──────────────────────────────────────────────────────────────────────
MOIS_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
               "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

# ── SEUILS BFR ────────────────────────────────────────────────────────────────
SEUIL_DSO = 50   # jours
SEUIL_DSI = 80   # jours
SEUIL_DPO = 30   # jours (en-dessous = délai fournisseur trop court)

# ── CLASSIFICATION COMPTABLE ──────────────────────────────────────────────────
CATEGORIES_CHARGES = [
    "Charges personnel", "Loyers & entretien", "Services extérieurs",
    "Impôts & taxes", "Dotations & provisions",
    "Pertes & litiges clients", "Autres charges",
]

CAT_COLORS = {
    "Produits":              "#1e8449",
    "Achats marchandises":   C_NAVY,
    "RFA Siège":             C_BUDGET,
    "Variation de stock":    C_STEEL,
    "Charges personnel":     "#2874a6",
    "Loyers & entretien":    "#1a5276",
    "Services extérieurs":   "#5dade2",
    "Impôts & taxes":        "#7f8c8d",
    "Dotations & provisions":"#aab7b8",
    "Pertes & litiges clients": C_NEG,
    "Autres charges":        "#aab7b8",
}

# ── ONGLETS ───────────────────────────────────────────────────────────────────
ONGLETS = [
    "Vue d'ensemble",
    "Évolution mensuelle",
    "Comparaison sites",
    "Drill-down charges",
    "Point mort",
    "Tréso & BFR",
    "Détail comptable",
]
