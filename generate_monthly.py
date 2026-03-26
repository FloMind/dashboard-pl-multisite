"""
Générateur de séries mensuelles — Dashboard P&L Multi-sites
Produit : data/sample_monthly.xlsx

Génère 12 mois de CA et résultat par site pour les graphiques d'évolution.
Cohérent avec sample_data.xlsx (même profils de sites, même totaux annuels).

Usage : python generate_monthly.py
Prérequis : data/sample_data.xlsx doit exister
"""

import pandas as pd
import numpy as np
from pathlib import Path

SEED = 42
np.random.seed(SEED)

CR_FILE     = "data/sample_data.xlsx"
BAL_FILE    = "data/sample_balance.xlsx"
OUTPUT_FILE = "data/sample_monthly.xlsx"

MOIS = ["Jan","Fév","Mar","Avr","Mai","Jun",
        "Jul","Aoû","Sep","Oct","Nov","Déc"]

# Saisonnalité typique distribution B2B (index 1.0 = moyenne mensuelle)
# Fort en mars/sept (rentrée chantiers), faible en août/janvier
SAISONNALITE = [0.82, 0.88, 1.08, 1.05, 1.04, 0.98,
                0.92, 0.72, 1.10, 1.05, 1.00, 0.96]


def load_pl_annuel(cr_path: str) -> pd.DataFrame:
    """Relit les grandes masses annuelles par site depuis le CR."""
    df = pd.read_excel(cr_path)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Libellé Centre de Coûts": "site",
        "CUMUL R 25":              "cumul_r25",
        "CUMUL B 25":              "cumul_b25",
        "CUMUL R 24":              "cumul_r24",
    })
    df["Compte"] = pd.to_numeric(df["Compte"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Compte", "site"])

    rows = []
    for site, grp in df.groupby("site"):
        s = grp["Compte"].astype(str)

        # Produits
        ca_r25 = grp[s.str.startswith("70")]["cumul_r25"].sum()
        ca_b25 = grp[s.str.startswith("70")]["cumul_b25"].sum()
        ca_r24 = grp[s.str.startswith("70")]["cumul_r24"].sum()

        # Achats
        ach_r25 = grp[s.str.startswith(("607","608","602","604","606","609"))]["cumul_r25"].sum()

        # Charges structure
        ch_r25 = grp[s.str.startswith(("64","61","62","63","65","66","67","68"))]["cumul_r25"].sum()

        # RFA et stock
        rfa_r25   = grp[grp["Compte"] == 609720]["cumul_r25"].sum()
        stock_r25 = grp[grp["Compte"] == 603700]["cumul_r25"].sum()

        res_r25 = ca_r25 + ach_r25 + ch_r25 + rfa_r25 + stock_r25
        mbc_r25 = ca_r25 + ach_r25

        rows.append({
            "site":     site,
            "ca_r25":   ca_r25,
            "ca_b25":   ca_b25,
            "ca_r24":   ca_r24,
            "mbc_r25":  mbc_r25,
            "res_r25":  res_r25,
        })
    return pd.DataFrame(rows)


def generate_monthly(pl: pd.DataFrame, bal: pd.DataFrame = None) -> pd.DataFrame:
    """
    Génère une série mensuelle réaliste pour chaque site.
    Si bal fourni : BFR et tréso mensuels générés de façon cohérente.
    """
    np.random.seed(SEED)
    rows = []

    for _, r in pl.iterrows():
        site    = r["site"]
        ca_ann  = r["ca_r25"]
        ca_b    = r["ca_b25"] if r["ca_b25"] != 0 else ca_ann * 0.97
        ca_n1   = r["ca_r24"] if r["ca_r24"] != 0 else ca_ann * 0.95
        mbc_ann = r["mbc_r25"]
        res_ann = r["res_r25"]

        tx_mbc = mbc_ann / ca_ann if ca_ann else 0.35
        tx_res = res_ann / ca_ann if ca_ann else 0.10

        # Données bilan de fin d'année pour ce site
        brow = None
        if bal is not None and len(bal) > 0:
            match = bal[bal["site"] == site]
            if len(match) > 0:
                brow = match.iloc[0]

        # Valeurs bilan annuelles (fin décembre = point d'ancrage)
        stock_ann   = float(brow["stock_net"])   if brow is not None else ca_ann * 0.10
        creances_ann= float(brow["creances_net"]) if brow is not None else ca_ann * 0.12
        dettes_ann  = float(brow["dettes_frs"])   if brow is not None else ca_ann * 0.08
        bfr_ann     = stock_ann + creances_ann - dettes_ann
        treso_ann   = float(brow["tresorerie"])   if brow is not None else bfr_ann * 0.3

        # Saisonnalité BFR — inverse du CA (stock monte quand ventes baissent)
        saison      = np.array(SAISONNALITE)
        saison_bfr  = 1.0 + (1.0 - saison) * 0.15  # BFR plus élevé en basse saison
        saison_bfr  = saison_bfr / saison_bfr[-1]    # ancré sur décembre = 1.0

        # Distribution mensuelle du CA
        bruit  = np.random.uniform(0.93, 1.07, 12)
        poids  = saison * bruit
        poids  = poids / poids.sum()
        ca_mensuel_r25 = poids * ca_ann

        bruit_b = np.random.uniform(0.96, 1.04, 12)
        poids_b = saison * bruit_b
        poids_b = poids_b / poids_b.sum()
        ca_mensuel_b25 = poids_b * ca_b

        bruit_n1 = np.random.uniform(0.92, 1.08, 12)
        poids_n1 = saison * bruit_n1
        poids_n1 = poids_n1 / poids_n1.sum()
        ca_mensuel_r24 = poids_n1 * ca_n1

        for m in range(12):
            tx_mbc_m = tx_mbc * np.random.uniform(0.95, 1.05)
            tx_res_m = tx_res * np.random.uniform(0.88, 1.12)

            ca_m   = ca_mensuel_r25[m]
            mbc_m  = ca_m * tx_mbc_m
            res_m  = ca_m * tx_res_m
            ca_b_m = ca_mensuel_b25[m]
            ca_n_m = ca_mensuel_r24[m]

            # BFR mensuel : ancré sur valeur annuelle × saisonnalité
            bfr_m   = bfr_ann  * saison_bfr[m] * np.random.uniform(0.97, 1.03)
            treso_m = treso_ann * np.random.uniform(0.88, 1.12)
            # Stock et créances mensuels cohérents avec BFR
            stock_m   = stock_ann    * saison_bfr[m] * np.random.uniform(0.96, 1.04)
            creances_m= creances_ann * saison[m]     * np.random.uniform(0.93, 1.07)
            dettes_m  = dettes_ann   * np.random.uniform(0.92, 1.08)

            rows.append({
                "site":        site,
                "mois_num":    m + 1,
                "mois":        MOIS[m],
                "ca_r25":      round(ca_m, 0),
                "ca_b25":      round(ca_b_m, 0),
                "ca_r24":      round(ca_n_m, 0),
                "mbc_r25":     round(mbc_m, 0),
                "res_r25":     round(res_m, 0),
                "bfr":         round(bfr_m, 0),
                "tresorerie":  round(treso_m, 0),
                "stock":       round(stock_m, 0),
                "creances":    round(creances_m, 0),
                "dettes":      round(dettes_m, 0),
            })

    df = pd.DataFrame(rows)

    # Cumulés progressifs par site
    df = df.sort_values(["site","mois_num"])
    df["ca_cumul_r25"]  = df.groupby("site")["ca_r25"].cumsum()
    df["mbc_cumul_r25"] = df.groupby("site")["mbc_r25"].cumsum()
    df["res_cumul_r25"] = df.groupby("site")["res_r25"].cumsum()
    df["ca_cumul_r24"]  = df.groupby("site")["ca_r24"].cumsum()

    return df.reset_index(drop=True)


def generate(output_path: str = OUTPUT_FILE):
    if not Path(CR_FILE).exists():
        print(f"Erreur : {CR_FILE} introuvable. Lance d'abord generate_data.py")
        return

    Path("data").mkdir(exist_ok=True)
    pl = load_pl_annuel(CR_FILE)

    # Charger le bilan si disponible
    bal = None
    if Path(BAL_FILE).exists():
        bal = pd.read_excel(BAL_FILE)
        print(f"Données bilan chargées : {len(bal)} sites")
    else:
        print(f"Attention : {BAL_FILE} introuvable — BFR/tréso générés sans ancrage bilan")

    df = generate_monthly(pl, bal)
    df.to_excel(output_path, index=False)

    print(f"Fichier généré : {output_path}")
    print(f"{len(df):,} lignes · {df['site'].nunique()} sites · 12 mois")
    print(f"Colonnes : {list(df.columns)}")

    # Vérification cohérence annuelle
    ca_ann    = df.groupby("site")["ca_r25"].sum()
    pl_check  = pl.set_index("site")["ca_r25"]
    ecart_max = ((ca_ann - pl_check) / pl_check.abs() * 100).abs().max()
    print(f"Cohérence annuelle (écart max CA) : {ecart_max:.2f}%")

    # Récap réseau BFR/tréso
    dec = df[df["mois_num"] == 12]
    print(f"BFR réseau déc    : {dec['bfr'].sum()/1e3:.0f} k€")
    print(f"Tréso réseau déc  : {dec['tresorerie'].sum()/1e3:.0f} k€")


if __name__ == "__main__":
    generate()
