"""
Générateur de données bilan fictives — cohérentes avec le CR
Produit : data/sample_balance.xlsx

Dimensionnement à partir du CR :
  Stock       = achats × (DSI / 365)   DSI : 35-85 jours selon taille site
  Créances    = CA     × (DSO / 365)   DSO : 35-70 jours
  Dettes frs  = achats × (DPO / 365)   DPO : 28-55 jours
  Trésorerie  = corrélée au résultat + aléa conjoncturel
  BFR         = Stock + Créances - Dettes frs - Autres dettes CT

Usage : python generate_balance.py
        (nécessite data/sample_data.xlsx généré au préalable)
"""

import pandas as pd
import numpy as np
from pathlib import Path

SEED     = 42
np.random.seed(SEED)
INPUT_CR = "data/sample_data.xlsx"
OUTPUT   = "data/sample_balance.xlsx"


def load_cr_aggregates(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    ca = (df[df["Compte"].astype(str).str.startswith("70")]
          .groupby("Libellé Centre de Coûts")["CUMUL R 25"].sum().rename("ca"))
    ach = (df[df["Compte"] == 607000]
           .groupby("Libellé Centre de Coûts")["CUMUL R 25"].sum().abs().rename("achats"))
    res = (df.groupby("Libellé Centre de Coûts")["CUMUL R 25"].sum().rename("resultat"))
    pertes = (df[df["Compte"].astype(str).str.startswith(("654","658"))]
              .groupby("Libellé Centre de Coûts")["CUMUL R 25"].sum().abs().rename("pertes_clients"))
    return pd.concat([ca, ach, res, pertes], axis=1).fillna(0).reset_index().rename(
        columns={"Libellé Centre de Coûts": "site"})


def generate_balance(cr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in cr.iterrows():
        site    = row["site"]
        ca      = row["ca"]
        achats  = row["achats"]
        resultat= row["resultat"]
        pertes  = row["pertes_clients"]

        # Taille du site influence les ratios (grand = rotation plus rapide)
        tf = np.clip(ca / 2_000_000, 0.6, 1.4)

        dsi = np.random.uniform(35, 85) / tf
        dso = np.random.uniform(35, 70) / tf
        dpo = np.random.uniform(28, 55) * tf

        # ── Stock ─────────────────────────────────────────────────────────────
        stock_brut = achats * (dsi / 365)
        tx_depre   = np.random.uniform(0.02, 0.08)
        stock_net  = stock_brut * (1 - tx_depre)

        # ── Créances clients ──────────────────────────────────────────────────
        creances_brut = ca * (dso / 365)
        tx_douteux    = min(pertes / ca * 2, 0.10) + np.random.uniform(0.01, 0.04) if ca > 0 else 0.04
        creances_net  = creances_brut * (1 - tx_douteux)

        # ── Dettes fournisseurs ───────────────────────────────────────────────
        dettes_frs    = achats * (dpo / 365)
        autres_dettes = ca * np.random.uniform(0.03, 0.08)

        # ── Trésorerie ────────────────────────────────────────────────────────
        tresorerie = (resultat * np.random.uniform(0.4, 0.9)
                      + ca * np.random.uniform(-0.05, 0.08))

        # ── BFR ───────────────────────────────────────────────────────────────
        bfr     = stock_net + creances_net - dettes_frs - autres_dettes
        bfr_jca = (bfr / ca * 365) if ca > 0 else 0

        # ── Ratios calculés ───────────────────────────────────────────────────
        dsi_r = (stock_net  / achats * 365) if achats > 0 else 0
        dso_r = (creances_net / ca   * 365) if ca > 0 else 0
        dpo_r = (dettes_frs / achats * 365) if achats > 0 else 0

        # ── N-1 ───────────────────────────────────────────────────────────────
        vn = np.random.uniform(-0.12, 0.15)
        rows.append({
            "site":              site,
            "stock_brut":        round(stock_brut, 0),
            "stock_net":         round(stock_net, 0),
            "tx_depreciation":   round(tx_depre * 100, 1),
            "dsi":               round(dsi_r, 1),
            "stock_n1":          round(stock_net / (1 + vn * 0.5), 0),
            "creances_brut":     round(creances_brut, 0),
            "creances_net":      round(creances_net, 0),
            "tx_douteux":        round(tx_douteux * 100, 1),
            "dso":               round(dso_r, 1),
            "creances_n1":       round(creances_net / (1 + vn * 0.6), 0),
            "dettes_frs":        round(dettes_frs, 0),
            "autres_dettes":     round(autres_dettes, 0),
            "dpo":               round(dpo_r, 1),
            "dettes_n1":         round(dettes_frs / (1 + vn * 0.4), 0),
            "bfr":               round(bfr, 0),
            "bfr_jca":           round(bfr_jca, 1),
            "bfr_n1":            round((stock_net/(1+vn*0.5) + creances_net/(1+vn*0.6)
                                        - dettes_frs/(1+vn*0.4)
                                        - autres_dettes*(1+vn*0.3)), 0),
            "tresorerie":        round(tresorerie, 0),
            "tresorerie_n1":     round(tresorerie / (1 + vn * 0.8), 0),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    if not Path(INPUT_CR).exists():
        print(f"Erreur : {INPUT_CR} introuvable. Lance d'abord : python generate_data.py")
        exit(1)

    cr  = load_cr_aggregates(INPUT_CR)
    bal = generate_balance(cr)
    bal.to_excel(OUTPUT, index=False)

    print(f"Fichier généré : {OUTPUT}  ({len(bal)} sites)")
    totaux = {
        "Stock net":        bal["stock_net"].sum(),
        "Créances clients": bal["creances_net"].sum(),
        "Dettes frs":       bal["dettes_frs"].sum(),
        "BFR réseau":       bal["bfr"].sum(),
        "Trésorerie nette": bal["tresorerie"].sum(),
    }
    for k, v in totaux.items():
        print(f"  {k:<22} {v/1000:>8,.0f} k€")
    print(f"\n  DSI moyen : {bal['dsi'].mean():.1f} j  |  "
          f"DSO moyen : {bal['dso'].mean():.1f} j  |  "
          f"DPO moyen : {bal['dpo'].mean():.1f} j")
    print(f"  BFR moyen : {bal['bfr_jca'].mean():.1f} j de CA")
    print(f"  Tréso négative : {(bal['tresorerie']<0).sum()} sites  |  "
          f"BFR > 60j : {(bal['bfr_jca']>60).sum()} sites")
