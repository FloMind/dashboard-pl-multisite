"""
core/calculations.py — Calculs P&L et point mort
Extrait fidèlement du dashboard_pl.py original.
Colonnes : cumul_r25 (réalisé), cumul_b25 (budget), cumul_r24 (N-1)
"""

import pandas as pd

CATEGORIES_CHARGES = [
    "Charges personnel", "Loyers & entretien", "Services extérieurs",
    "Impôts & taxes", "Dotations & provisions",
    "Pertes & litiges clients", "Autres charges",
]


def classe_compte(compte: int) -> str:
    s = str(compte)
    c = int(s)
    if s.startswith("70") or s.startswith("72") or s.startswith("75") or \
       s.startswith("76") or s.startswith("77") or s.startswith("78") or \
       s.startswith("79"):
        return "Produits"
    if c == 609720:
        return "RFA"
    if c == 603700:
        return "Variation de stock"
    if s.startswith("607") or s.startswith("608") or s.startswith("602") or \
       s.startswith("604") or s.startswith("606") or s.startswith("609"):
        return "Achats marchandises"
    if s.startswith("64"):
        return "Charges personnel"
    if s.startswith("61"):
        return "Loyers & entretien"
    if s.startswith("62"):
        return "Services extérieurs"
    if s.startswith("63"):
        return "Impôts & taxes"
    if s.startswith("681") or s.startswith("686") or s.startswith("687"):
        return "Dotations & provisions"
    if s.startswith("654") or s.startswith("6581") or s.startswith("6582") or \
       c in (658005, 658000, 651600):
        return "Pertes & litiges clients"
    return "Autres charges"


def build_pl(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for site, grp in df.groupby("site"):

        def ch_sum(g, c):
            return g[g["categorie"] == c]["cumul_r25"].sum() if "cumul_r25" in g.columns else 0.0
        def ch_sum_b(g, c):
            return g[g["categorie"] == c]["cumul_b25"].sum() if "cumul_b25" in g.columns else 0.0
        def ch_sum_n(g, c):
            return g[g["categorie"] == c]["cumul_r24"].sum() if "cumul_r24" in g.columns else 0.0

        prod  = grp[grp["categorie"] == "Produits"]
        ach   = grp[grp["categorie"] == "Achats marchandises"]
        rfa   = grp[grp["categorie"] == "RFA"]
        stock = grp[grp["categorie"] == "Variation de stock"]

        def col(df_, c): return df_[c].sum() if c in df_.columns else 0.0

        ca_r25, ca_b25, ca_r24 = col(prod,"cumul_r25"), col(prod,"cumul_b25"), col(prod,"cumul_r24")
        ach_r25, ach_b25, ach_r24 = col(ach,"cumul_r25"), col(ach,"cumul_b25"), col(ach,"cumul_r24")
        rfa_r25, rfa_r24 = col(rfa,"cumul_r25"), col(rfa,"cumul_r24")
        stock_r25, stock_r24 = col(stock,"cumul_r25"), col(stock,"cumul_r24")

        mbc_r25, mbc_b25, mbc_r24 = ca_r25+ach_r25, ca_b25+ach_b25, ca_r24+ach_r24
        mb_r25 = mbc_r25 + rfa_r25 + stock_r25
        mb_b25 = mbc_b25
        mb_r24 = mbc_r24 + rfa_r24 + stock_r24

        cats_ch = ["Charges personnel","Loyers & entretien","Services extérieurs",
                   "Impôts & taxes","Dotations & provisions","Pertes & litiges clients","Autres charges"]
        ch_r25 = sum(ch_sum(grp, c)   for c in cats_ch)
        ch_b25 = sum(ch_sum_b(grp, c) for c in cats_ch)
        ch_r24 = sum(ch_sum_n(grp, c) for c in cats_ch)

        res_r25, res_b25, res_r24 = mb_r25+ch_r25, mb_b25+ch_b25, mb_r24+ch_r24
        tx_mbc_r25 = mbc_r25/ca_r25*100 if ca_r25 else 0
        tx_mbc_b25 = mbc_b25/ca_b25*100 if ca_b25 else 0
        tx_mbc_r24 = mbc_r24/ca_r24*100 if ca_r24 else 0

        # Point mort (logique originale)
        ch_fixes_r25      = sum(ch_sum(grp, c) for c in ["Charges personnel","Loyers & entretien","Impôts & taxes","Dotations & provisions"])
        ch_var_struct_r25 = sum(ch_sum(grp, c) for c in ["Services extérieurs","Pertes & litiges clients","Autres charges"])
        mcv_r25    = ca_r25 + ach_r25 + ch_var_struct_r25
        tx_mcv_r25 = mcv_r25 / ca_r25 * 100 if ca_r25 else 0
        pm_r25     = abs(ch_fixes_r25) / (tx_mcv_r25/100) if tx_mcv_r25 else 0
        ms_r25     = ca_r25 - pm_r25
        tx_ms_r25  = ms_r25 / ca_r25 * 100 if ca_r25 else 0
        pm_jours   = pm_r25 / ca_r25 * 365 if ca_r25 > 0 else 999
        levier_op  = mcv_r25 / res_r25 if res_r25 and res_r25 != 0 else 0

        rows.append(dict(
            site=site,
            ca_r25=ca_r25,   ca_b25=ca_b25,   ca_r24=ca_r24,
            ach_r25=ach_r25, ach_b25=ach_b25,  ach_r24=ach_r24,
            rfa_r25=rfa_r25, rfa_r24=rfa_r24,
            stock_r25=stock_r25, stock_r24=stock_r24,
            mbc_r25=mbc_r25, mbc_b25=mbc_b25,  mbc_r24=mbc_r24,
            tx_mbc_r25=tx_mbc_r25, tx_mbc_b25=tx_mbc_b25, tx_mbc_r24=tx_mbc_r24,
            mb_r25=mb_r25,   mb_b25=mb_b25,    mb_r24=mb_r24,
            pers_r25=ch_sum(grp,"Charges personnel"),
            loyer_r25=ch_sum(grp,"Loyers & entretien"),
            svc_r25=ch_sum(grp,"Services extérieurs"),
            imp_r25=ch_sum(grp,"Impôts & taxes"),
            dot_r25=ch_sum(grp,"Dotations & provisions"),
            perte_r25=ch_sum(grp,"Pertes & litiges clients"),
            aut_r25=ch_sum(grp,"Autres charges"),
            ch_r25=ch_r25, ch_b25=ch_b25, ch_r24=ch_r24,
            res_r25=res_r25, res_b25=res_b25, res_r24=res_r24,
            ecart_b=res_r25-res_b25, ecart_n1=res_r25-res_r24,
            ch_fixes_r25=ch_fixes_r25, ch_var_struct_r25=ch_var_struct_r25,
            mcv_r25=mcv_r25, tx_mcv_r25=tx_mcv_r25,
            pm_r25=pm_r25, ms_r25=ms_r25, tx_ms_r25=tx_ms_r25,
            pm_jours=pm_jours, levier_op=levier_op,
            seuil_r25=pm_r25, marge_secu=ms_r25, ind_secu=tx_ms_r25,
            charges_fixes=abs(ch_fixes_r25),
        ))

    return pd.DataFrame(rows).sort_values("res_r25", ascending=False)
