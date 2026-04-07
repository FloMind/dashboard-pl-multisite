"""
core/loader.py — Chargement et cache des données P&L dashboard
Colonnes Excel source : CUMUL R 25, CUMUL B 25, CUMUL R 24
"""

import streamlit as st
import pandas as pd
from core.constants import FILE_PL, FILE_BAL, FILE_MON
from core.calculations import classe_compte, build_pl


@st.cache_data(show_spinner=False)
def _load_pl_raw() -> pd.DataFrame:
    df = pd.read_excel(FILE_PL)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Libellé Compte":           "libelle_compte",
        "Libellé Centre de Coûts":  "site",
        "MENSUEL R 25":             "mensuel_r25",
        "MENSUEL B 25":             "mensuel_b25",
        "MENSUEL R 24":             "mensuel_r24",
        "MENSUEL R 25 vs B 25":     "mensuel_ecart_b",
        "MENSUEL R 25 vs R 24":     "mensuel_ecart_n1",
        "CUMUL R 25":               "cumul_r25",
        "CUMUL B 25":               "cumul_b25",
        "CUMUL R 24":               "cumul_r24",
        "CUMUL R 25 vs B 25":       "cumul_ecart_b",
        "CUMUL R 25 vs R 24":       "cumul_ecart_n1",
        "BUDGET ANNUEL B 25":       "ap_b25",
        "REALISE ANNUEL R 24":      "ap_r24",
    })
    df["Compte"] = pd.to_numeric(df["Compte"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Compte", "site"])
    df["categorie"] = df["Compte"].apply(classe_compte)

    all_num = ["cumul_r25", "cumul_b25", "cumul_r24",
               "mensuel_r25", "mensuel_b25", "mensuel_r24",
               "ap_b25", "ap_r24"]
    num_cols = [c for c in all_num if c in df.columns]

    return (
        df.groupby(["Compte", "libelle_compte", "site", "categorie"])[num_cols]
        .sum().reset_index()
    )


@st.cache_data(show_spinner=False)
def _load_balance() -> pd.DataFrame:
    try:
        return pd.read_excel(FILE_BAL)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def _load_monthly() -> pd.DataFrame:
    try:
        return pd.read_excel(FILE_MON)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def _build_pl_cached(df: pd.DataFrame) -> pd.DataFrame:
    return build_pl(df)


def load_all() -> dict:
    if "data_pl" not in st.session_state:
        df  = _load_pl_raw()
        pl  = _build_pl_cached(df)
        bal = _load_balance()
        mon = _load_monthly()
        st.session_state["data_pl"] = {
            "df":  df, "pl":  pl, "bal": bal, "mon": mon,
            "all_sites": sorted(pl["site"].unique().tolist()),
        }
    return st.session_state["data_pl"]


def filter_data(data: dict, sites_sel: list) -> dict:
    sites_key = tuple(sorted(sites_sel))
    if st.session_state.get("pl_sites_key") != sites_key:
        pl  = data["pl"]
        df  = data["df"]
        bal = data["bal"]
        mon = data["mon"]
        st.session_state["data_pl_f"] = {
            "pl_f":  pl[pl["site"].isin(sites_sel)],
            "df_f":  df[df["site"].isin(sites_sel)],
            "bal_f": bal[bal["site"].isin(sites_sel)] if not bal.empty else pd.DataFrame(),
            "mon_f": mon[mon["site"].isin(sites_sel)] if not mon.empty else pd.DataFrame(),
        }
        st.session_state["pl_sites_key"] = sites_key
    return st.session_state["data_pl_f"]
