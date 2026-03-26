"""
Générateur de données fictives — Dashboard P&L Multi-sites
Produit : data/sample_data.xlsx

Les données générées reproduisent la structure d'un export comptable
de réseau de distribution B2B (24 sites, comptes PCG standards).
Aucune donnée réelle n'est utilisée.

Usage : python generate_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── PARAMÈTRES ──────────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)

SITES = [
    "Site_01", "Site_02", "Site_03", "Site_04", "Site_05", "Site_06",
    "Site_07", "Site_08", "Site_09", "Site_10", "Site_11", "Site_12",
    "Site_13", "Site_14", "Site_15", "Site_16", "Site_17", "Site_18",
    "Site_19", "Site_20", "Site_21", "Site_22", "Site_23", "Site_24",
    "Site_25", "Site_26", "Site_27", "Site_28", "Site_29", "Site_30",
]

# Plan de comptes simplifié — structure Distribution B2B
COMPTES = [
    # Produits
    (707100, "VENTES MARCHANDISES CA GROS"),
    (707200, "VENTES MARCHANDISES CA DETAIL"),
    (709700, "RRR ACCORDES"),
    (709799, "REMISES PROGRAMME FIDELITE"),
    # Achats
    (607000, "ACHATS MARCHANDISES"),
    (607610, "FLUX INTERNES POINTS DE VENTE"),
    (607611, "FLUX INTERNES POINTS DE VENTE"),
    (609720, "REMISES FOURNISSEURS SIEGE"),   # RFA — isolé
    (603700, "VARIATION STOCK MARCHANDISES"), # Stock — isolé
    # Personnel
    (641100, "SALAIRES APPOINTEMENTS"),
    (641200, "PROV CONGES PAYES"),
    (645100, "URSSAF"),
    (645200, "MUTUELLES ET PREVOYANCES"),
    (645300, "CAISSES DE RETRAITES"),
    # Loyers & entretien
    (613200, "LOCATIONS IMMOBILIERES"),
    (615200, "ENTRETIEN BIENS IMMOBILIERS"),
    (616000, "ASSURANCES MULTIRISQUES"),
    # Services extérieurs
    (622600, "HONORAIRES AUTRES"),
    (625100, "VOYAGE ET DEPLACEMENT"),
    (626200, "TELEPHONE PORTABLE"),
    (626210, "TELEPHONE"),
    # Énergie (606x → Achats marchandises dans le dashboard)
    (606100, "ELECTRICITE"),
    (606103, "GAZ"),
    # Impôts & taxes
    (635110, "CFE"),
    (633400, "EFFORT DE CONSTRUCTION"),
    (633500, "TAXE APPRENTISSAGE"),
    # Autres
    (658000, "CHARGES DIVERSES GESTION COURANTE"),
    (671200, "AMENDES PENALITES"),
]


def generate_site_profile(site_idx: int) -> dict:
    """Génère un profil financier réaliste pour un site."""
    # CA annuel entre 0.8M et 3.5M€ selon taille du site
    ca_base = np.random.uniform(800_000, 3_500_000)

    # Taux de marge brute commerciale : 28-52% (distribution B2B)
    tx_mbc = np.random.uniform(0.28, 0.52)

    # Charges de structure / CA : 15-38%
    # En distribution B2B, les charges fixes sont un levier clé
    # Sites rentables quand tx_mbc > tx_charges (ce qui arrive ~60% du temps)
    tx_charges = np.random.uniform(0.15, 0.38)

    # Croissance vs N-1 : -10% à +15%
    croissance = np.random.uniform(-0.10, 0.15)

    # Écart réalisé vs budget : -8% à +8%
    ecart_budget = np.random.uniform(-0.08, 0.08)

    # RFA : 5-15% du CA achats
    tx_rfa = np.random.uniform(0.05, 0.15)

    return {
        "ca_base": ca_base,
        "tx_mbc": tx_mbc,
        "tx_charges": tx_charges,
        "croissance": croissance,
        "ecart_budget": ecart_budget,
        "tx_rfa": tx_rfa,
    }


def build_rows(site: str, profile: dict) -> list:
    """Construit les lignes du compte de résultat pour un site."""
    rows = []
    ca   = profile["ca_base"]
    tx   = profile["tx_mbc"]
    crop = profile["croissance"]
    eb   = profile["ecart_budget"]
    rfa  = profile["tx_rfa"]
    txch = profile["tx_charges"]

    # ── CA réalisé ───────────────────────────────────────────────────────────
    ca_gros   = ca * 0.75
    ca_detail = ca * 0.25
    rrr       = ca * np.random.uniform(0.015, 0.04)
    remises   = ca * np.random.uniform(0.005, 0.02)

    # ── Budget CA : réalisé / (1 + écart budget) ──────────────────────────────
    # eb > 0 = réalisé > budget (surperformance)
    # eb < 0 = réalisé < budget (sous-performance)
    ca_budget_gros   = ca_gros   / (1 + eb)
    ca_budget_detail = ca_detail / (1 + eb)
    rrr_budget       = rrr       / (1 + eb * 0.5)  # RRR varie moins que le CA

    # ── Achats réalisés ───────────────────────────────────────────────────────
    achats_bruts   = ca * (1 - tx)
    achats_budget  = (ca_budget_gros + ca_budget_detail) * (1 - tx * np.random.uniform(0.98, 1.02))
    flux_inter_deb = ca * np.random.uniform(0.01, 0.05)
    flux_inter_cre = ca * np.random.uniform(0.01, 0.05)
    rfa_montant    = achats_bruts * rfa
    var_stock      = ca * np.random.uniform(-0.02, 0.04)

    # ── Charges de structure ──────────────────────────────────────────────────
    charges_tot   = ca * txch
    charges_bud   = charges_tot / (1 + eb * 0.3)  # charges moins sensibles à l'activité
    # Charges fixes : écart budget indépendant du CA (dérive propre)
    drift = np.random.uniform(-0.05, 0.08)         # dépassement budgétaire charges fixes

    pers_r   = 0.60;  loyer_r  = 0.18
    svc_r    = 0.10;  imp_r    = 0.06;  aut_r = 0.06

    # ── N-1 ───────────────────────────────────────────────────────────────────
    ca_n1      = ca / (1 + crop)
    achats_n1  = achats_bruts / (1 + crop * 0.8)
    charges_n1 = charges_tot  / (1 + crop * 0.3)

    def add(compte, libelle, cumul_r25, cumul_b25=0, cumul_r24=0, ap_b25=0):
        """Ajoute une ligne. Mensuel = cumul/12 avec bruit réaliste."""
        noise_r = np.random.uniform(0.80, 1.20)
        noise_b = np.random.uniform(0.88, 1.12)
        noise_n = np.random.uniform(0.82, 1.18)
        m_r25 = (cumul_r25 / 12) * noise_r
        m_b25 = (cumul_b25 / 12) * noise_b if cumul_b25 else 0
        m_r24 = (cumul_r24 / 12) * noise_n if cumul_r24 else 0
        rows.append({
            "Compte":                   compte,
            "Libellé Compte":           libelle,
            "Libellé Centre de Coûts":  site,
            "MENSUEL R 25":             round(m_r25, 2),
            "MENSUEL B 25":             round(m_b25, 2),
            "MENSUEL R 24":             round(m_r24, 2),
            "MENSUEL R 25 vs B 25":     round(m_r25 - m_b25, 2),
            "MENSUEL R 25 vs R 24":     round(m_r25 - m_r24, 2),
            "CUMUL R 25":               round(cumul_r25, 2),
            "CUMUL B 25":               round(cumul_b25, 2),
            "CUMUL R 24":               round(cumul_r24, 2),
            "CUMUL R 25 vs B 25":       round(cumul_r25 - cumul_b25, 2),
            "CUMUL R 25 vs R 24":       round(cumul_r25 - cumul_r24, 2),
            "BUDGET ANNUEL B 25":        round(ap_b25, 2),
            "REALISE ANNUEL R 24":        round(cumul_r24, 2),   # N-1 = réalisé complet
        })

    # ── Produits ──────────────────────────────────────────────────────────────
    add(707100, "VENTES MARCHANDISES CA GROS",
        ca_gros, ca_budget_gros, ca_n1*0.75,
        ap_b25=ca_budget_gros)
    add(707200, "VENTES MARCHANDISES CA DETAIL",
        ca_detail, ca_budget_detail, ca_n1*0.25,
        ap_b25=ca_budget_detail)
    add(709700, "RRR ACCORDES",
        -rrr, -rrr_budget, -rrr/(1+crop),
        ap_b25=-rrr_budget)
    add(709799, "REMISES PROGRAMME FIDELITE",
        -remises, 0, -remises/(1+crop))

    # ── Achats marchandises ───────────────────────────────────────────────────
    # Budget achats = budget CA × (1 - tx_marge) avec légère variation
    add(607000, "ACHATS MARCHANDISES",
        -achats_bruts, -achats_budget, -achats_n1,
        ap_b25=-achats_budget)
    # Flux inter-sites : pas de budget (mouvements internes)
    add(607610, "FLUX INTERNES POINTS DE VENTE",
        -flux_inter_deb, 0, -flux_inter_deb/(1+crop))
    add(607611, "FLUX INTERNES POINTS DE VENTE",
        flux_inter_cre, 0, flux_inter_cre/(1+crop))
    # RFA : pas de budget (allouée par le siège)
    add(609720, "REMISES FOURNISSEURS SIEGE",
        rfa_montant, 0, rfa_montant/(1+crop))
    # Variation de stock : pas de budget
    add(603700, "VARIATION STOCK MARCHANDISES",
        var_stock, 0, -var_stock * np.random.uniform(0.5, 1.5))

    # ── Énergie (charges semi-variables) ──────────────────────────────────────
    energie   = charges_tot * 0.04
    energie_b = energie * (1 + drift * 0.5)   # légère dérive énergie
    energie_n = charges_n1 * 0.04
    add(606100, "ELECTRICITE",
        -energie*0.7, -energie_b*0.7, -energie_n*0.7, ap_b25=-energie_b*0.7)
    add(606103, "GAZ",
        -energie*0.3, -energie_b*0.3, -energie_n*0.3, ap_b25=-energie_b*0.3)

    # ── Personnel (charges fixes — budget indépendant du CA) ──────────────────
    pers   = charges_tot * pers_r
    pers_b = charges_bud  * pers_r * (1 + drift)   # dérive masse salariale
    pers_n = charges_n1   * pers_r
    add(641100, "SALAIRES APPOINTEMENTS",
        -pers*0.55, -pers_b*0.55, -pers_n*0.55, ap_b25=-pers_b*0.55)
    add(641200, "PROV CONGES PAYES",
        -pers*0.09, -pers_b*0.09, -pers_n*0.09, ap_b25=-pers_b*0.09)
    add(645100, "URSSAF",
        -pers*0.20, -pers_b*0.20, -pers_n*0.20, ap_b25=-pers_b*0.20)
    add(645200, "MUTUELLES ET PREVOYANCES",
        -pers*0.06, -pers_b*0.06, -pers_n*0.06, ap_b25=-pers_b*0.06)
    add(645300, "CAISSES DE RETRAITES",
        -pers*0.10, -pers_b*0.10, -pers_n*0.10, ap_b25=-pers_b*0.10)

    # ── Loyers & entretien (quasi fixes) ──────────────────────────────────────
    loyer   = charges_tot  * loyer_r
    loyer_b = charges_bud  * loyer_r * (1 + drift * 0.3)
    loyer_n = charges_n1   * loyer_r
    add(613200, "LOCATIONS IMMOBILIERES",
        -loyer*0.75, -loyer_b*0.75, -loyer_n*0.75, ap_b25=-loyer_b*0.75)
    add(615200, "ENTRETIEN BIENS IMMOBILIERS",
        -loyer*0.15, -loyer_b*0.15, -loyer_n*0.15, ap_b25=-loyer_b*0.15)
    add(616000, "ASSURANCES MULTIRISQUES",
        -loyer*0.10, -loyer_b*0.10, -loyer_n*0.10, ap_b25=-loyer_b*0.10)

    # ── Services extérieurs (semi-variables) ──────────────────────────────────
    svc   = charges_tot * svc_r
    svc_b = charges_bud * svc_r * (1 + drift * 0.6)
    svc_n = charges_n1  * svc_r
    add(622600, "HONORAIRES AUTRES",
        -svc*0.25, -svc_b*0.25, -svc_n*0.25, ap_b25=-svc_b*0.25)
    add(625100, "VOYAGE ET DEPLACEMENT",
        -svc*0.35, -svc_b*0.35, -svc_n*0.35, ap_b25=-svc_b*0.35)
    add(626200, "TELEPHONE PORTABLE",
        -svc*0.20, -svc_b*0.20, -svc_n*0.20, ap_b25=-svc_b*0.20)
    add(626210, "TELEPHONE",
        -svc*0.20, -svc_b*0.20, -svc_n*0.20, ap_b25=-svc_b*0.20)

    # ── Impôts & taxes (fixes) ────────────────────────────────────────────────
    imp   = charges_tot * imp_r
    imp_b = charges_bud * imp_r
    imp_n = charges_n1  * imp_r
    add(635110, "CFE",
        -imp*0.60, -imp_b*0.60, -imp_n*0.60, ap_b25=-imp_b*0.60)
    add(633400, "EFFORT DE CONSTRUCTION",
        -imp*0.25, -imp_b*0.25, -imp_n*0.25, ap_b25=-imp_b*0.25)
    add(633500, "TAXE APPRENTISSAGE",
        -imp*0.15, -imp_b*0.15, -imp_n*0.15, ap_b25=-imp_b*0.15)

    # ── Autres charges ────────────────────────────────────────────────────────
    aut   = charges_tot * aut_r
    aut_b = charges_bud * aut_r * (1 + drift * 0.8)
    aut_n = charges_n1  * aut_r
    add(658000, "CHARGES DIVERSES GESTION COURANTE",
        -aut*0.80, -aut_b*0.80, -aut_n*0.80, ap_b25=-aut_b*0.80)
    add(671200, "AMENDES PENALITES",
        -aut*0.20, 0, 0)

    return rows


def generate(output_path: str = "data/sample_data.xlsx"):
    Path("data").mkdir(exist_ok=True)
    all_rows = []
    for i, site in enumerate(SITES):
        profile = generate_site_profile(i)
        all_rows.extend(build_rows(site, profile))

    df = pd.DataFrame(all_rows)

    # ── Rééquilibrage flux inter-sites ────────────────────────────────────────
    # En cumul annuel complet, les débits (607610) et crédits (607611)
    # doivent s'équilibrer au niveau du réseau (ce que le site A envoie,
    # le site B reçoit). On force l'égalité en ajustant les crédits.
    total_deb = df[df["Compte"] == 607610]["CUMUL R 25"].sum()  # négatif
    total_cre = df[df["Compte"] == 607611]["CUMUL R 25"].sum()  # positif
    ecart = total_deb + total_cre  # devrait être 0

    if abs(ecart) > 1:
        # Facteur correctif appliqué uniformément aux lignes 607611
        mask_611 = df["Compte"] == 607611
        nb_611   = mask_611.sum()
        correction_par_ligne = -ecart / nb_611

        for col in ["CUMUL R 25", "CUMUL R 25 vs B 25", "CUMUL R 25 vs R 24"]:
            df.loc[mask_611, col] = df.loc[mask_611, col] + correction_par_ligne

        # Mensuel ajusté en proportion
        for col in ["MENSUEL R 25", "MENSUEL R 25 vs B 25", "MENSUEL R 25 vs R 24"]:
            df.loc[mask_611, col] = df.loc[mask_611, col] + correction_par_ligne / 12

    # Ordre des colonnes conforme à l'export Sage attendu
    cols = [
        "Compte", "Libellé Compte", "Libellé Centre de Coûts",
        "MENSUEL R 25", "MENSUEL B 25", "MENSUEL R 24",
        "MENSUEL R 25 vs B 25", "MENSUEL R 25 vs R 24",
        "CUMUL R 25", "CUMUL B 25", "CUMUL R 24",
        "CUMUL R 25 vs B 25", "CUMUL R 25 vs R 24",
        "BUDGET ANNUEL B 25", "REALISE ANNUEL R 24",
    ]
    df = df[cols]

    df.to_excel(output_path, index=False)
    print(f"Fichier généré : {output_path}")
    print(f"{len(df):,} lignes · {len(SITES)} sites · {len(df['Compte'].unique())} comptes uniques")

    # Récapitulatif
    ca_total = df[df["Compte"].astype(str).str.startswith("70")]["CUMUL R 25"].sum()
    print(f"CA total fictif : {ca_total/1e6:.1f} M€")


if __name__ == "__main__":
    generate()
