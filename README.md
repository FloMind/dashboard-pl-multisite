# Dashboard P&L Multi-sites

**Outil de pilotage financier interactif pour réseaux de distribution multi-sites**  
Stack : Python · Streamlit · Plotly · Pandas

🔗 [Démo live](https://dashboard-pl-florent.streamlit.app) &nbsp;·&nbsp; [LinkedIn](https://linkedin.com/in/florent-cochet-3b3938138)

---

## Le problème adressé

Les directions régionales de réseaux de distribution (B2B, matériaux, négoce) pilotent typiquement 15 à 30 centres de profit simultanément. Le reporting mensuel repose souvent sur des exports ERP consolidés manuellement dans Excel, rendant difficiles :

- la comparaison rapide des performances site à site
- l'identification immédiate des sites en décrochage
- la distinction entre marge commerciale réelle et ajustements comptables (RFA, variation de stock)
- le calcul du point mort et de la marge de sécurité par site
- le suivi du BFR et de la trésorerie à l'échelle du réseau

Ce dashboard transforme un export comptable standard (compte de résultat par centre de coûts, format Sage/Cegid) en outil de pilotage interactif, consultable par tout profil — du directeur régional au contrôleur de gestion.

---

## Aperçu

![Dashboard P&L Multi-sites](https://raw.githubusercontent.com/FloMind/dashboard-pl-multisite/main/docs/screenshot.png)

---

## Fonctionnalités

### Vue d'ensemble
- 5 KPIs P&L réseau en M€ avec évolution vs N-1 (CA, MB commerciale, Résultat, Écart budget, Santé réseau)
- 6 KPIs BFR & Trésorerie réseau (Tréso, Stock, Créances, Dettes, BFR, Sites à risque)
- Cascade P&L réseau consolidée (waterfall 13 postes)
- Graphiques Tréso/BFR par site + délais DSO/DSI/DPO
- Tableau réseau consolidé avec export Excel

### Évolution mensuelle
- Indicateur sélectionnable : CA, CA cumulé, MB commerciale, Résultat, Résultat cumulé
- Vue réseau consolidé : courbe R2025 vs N-1 vs Budget + barplot écarts
- Vue par site top 10 : multi-courbes + heatmap mensuelle (sites × mois)

### Comparaison sites
- 10 indicateurs sélectionnables dont seuil de rentabilité et indice de sécurité
- Barplot groupé R2025 / Budget / N-1
- Tableau P&L complet avec export Excel

### Drill-down charges
- Cascade P&L site (waterfall 13 postes) : du CA au résultat net
- Séparation explicite MB commerciale / ajustements siège & stock
- Répartition des charges (donut) + comparaison R24/Budget/N-1
- Top 15 postes de charges par site

### Point mort *(onglet dédié)*
- Seuil de rentabilité, marge de sécurité, indice de sécurité, levier opérationnel
- Gauge CA réalisé vs point mort (zone rouge/verte)
- Décomposition charges fixes vs variables de structure
- Tableau de sensibilité : impact d'une variation de CA de ±5% à ±20% sur le résultat
- Vue réseau : classement de tous les sites par point mort (jours)

### Tréso & BFR (3 niveaux de lecture)
- **Réseau** : 5 KPIs + waterfall BFR + évolution mensuelle tréso/BFR
- **Sites** : 9 indicateurs comparables + seuils d'alerte DSO/DSI/DPO + bloc alertes RAG
- **Site** : 6 KPIs + waterfall BFR + stock brut/net + créances + évolution mensuelle vs N-1

### Détail comptable
- Tableau filtrable par site et catégorie de compte
- Top 20 postes en barplot horizontal coloré par catégorie

---

## Architecture de la marge brute

Ce dashboard distingue deux niveaux de marge, contrairement à la plupart des outils standards :

```
CA net (comptes 70x)
- Achats marchandises (607x, 608x, 602x, 604x, 606x)
= MARGE BRUTE COMMERCIALE   ← performance commerciale pure, comparable entre sites

+ RFA (609720)         ← remise de fin d'année allouée par le siège
+ Variation de stock (603700)← ajustement inventaire
= MARGE BRUTE TOTALE

- Charges de structure (64x, 61x, 62x, 63x, 65x, 68x...)
= RÉSULTAT NET
```

**Pourquoi cette distinction ?**  
La RFA et la variation de stock ne sont pas pilotables par le directeur de site. Les inclure dans la MB brouille la comparaison entre sites et génère des taux de marge aberrants sur les sites à faible CA. Séparer les deux niveaux permet des revues de performance plus pertinentes.

---

## Classification des comptes

| Catégorie | Comptes PCG |
|---|---|
| Produits | 70x, 72x, 75x–79x |
| Achats marchandises | 607x, 608x, 602x, 604x, 606x, 609x |
| RFA *(isolé)* | 609720 |
| Variation de stock *(isolé)* | 603700 |
| Charges personnel | 64x |
| Loyers & entretien | 61x |
| Services extérieurs | 62x |
| Impôts & taxes | 63x |
| Dotations & provisions | 681x, 686x, 687x |
| Pertes & litiges clients | 654x, 658x |
| Autres charges | reste 65x, 66x, 67x |

---

## Installation locale

### Prérequis
- Python 3.9+

```bash
# 1. Cloner le dépôt
git clone https://github.com/FloMind/dashboard-pl-multisite.git
cd dashboard-pl-multisite

# 2. Environnement virtuel
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Dépendances
pip install -r requirements.txt

# 4. Générer les données de démonstration
python generate_data.py
python generate_balance.py
python generate_monthly.py

# 5. Lancer
streamlit run dashboard_pl.py
```

→ Le navigateur s'ouvre sur `http://localhost:8501`

---

## Utilisation avec vos propres données

Le fichier Excel d'entrée doit contenir une feuille avec les colonnes suivantes :

| Colonne | Description | Exemple |
|---|---|---|
| `Compte` | Numéro de compte PCG | `607000` |
| `Libellé Compte` | Intitulé du compte | `ACHATS MARCHANDISES` |
| `Libellé Centre de Coûts` | Nom du site | `Site_01` |
| `MENSUEL R 25` | Réalisé mensuel 2024 | `-45 230` |
| `MENSUEL B 25` | Budget mensuel 2024 | `-48 000` |
| `MENSUEL R 25` | Réalisé mensuel 2023 | `-42 100` |
| `CUMUL R 25` | Cumul réalisé 2024 | `-542 760` |
| `CUMUL B 25` | Cumul budget 2024 | `-576 000` |
| `CUMUL R 25` | Cumul réalisé 2023 | `-505 200` |
| `BUDGET ANNUEL B 25` | Budget annuel 2024 | `-576 000` |
| `REALISE ANNUEL R 24` | Réalisé annuel 2023 | `-505 200` |

> **Convention de signe** : produits (70x) positifs, charges (6x) négatives — conforme à l'export Sage standard.

Modifier ensuite la variable `FILE` en tête de `dashboard_pl.py` :

```python
FILE     = "votre_fichier_cr.xlsx"
FILE_BAL = "votre_fichier_bilan.xlsx"    # optionnel
FILE_MON = "votre_fichier_mensuel.xlsx"  # optionnel
```

---

## Données de démonstration

Les données incluses dans `data/` sont **100% fictives**, générées par les scripts `generate_*.py`. Elles reproduisent la structure d'un réseau de distribution de 30 sites (~56 M€ CA) avec :

- Taux de marge hétérogènes (distribution B2B : 28–52%)
- Écarts budgétaires positifs et négatifs
- RFA variables selon les sites
- Charges de structure réalistes (personnel ~55–65% des charges fixes)
- Saisonnalité B2B (pic mars/septembre, creux août)
- 2 sites déficitaires sur 30 (cas réalistes)

---

## Structure du projet

```
dashboard-pl-multisite/
├── dashboard_pl.py          # App Streamlit principale (1 689 lignes)
├── generate_data.py         # Générateur CR fictif (30 sites, 56.6 M€)
├── generate_balance.py      # Générateur bilan fictif (DSO, DSI, DPO, BFR)
├── generate_monthly.py      # Générateur séries mensuelles (12 mois × 30 sites)
├── requirements.txt
├── .gitignore
├── README.md
└── data/
    ├── sample_data.xlsx     # CR fictif
    ├── sample_balance.xlsx  # Bilan fictif
    └── sample_monthly.xlsx  # Séries mensuelles fictives
```

---

## Stack technique

| Composant | Version min | Rôle |
|---|---|---|
| [Streamlit](https://streamlit.io) | 1.32 | Interface web interactive |
| [Pandas](https://pandas.pydata.org) | 2.0 | Chargement, agrégation, calculs |
| [Plotly](https://plotly.com/python/) | 5.18 | Graphiques interactifs |
| [openpyxl](https://openpyxl.readthedocs.io) | 3.1 | Lecture/écriture Excel |

---

## Auteur

**Florent Cochet** — Contrôleur de gestion & Data  
13 ans de pilotage de réseaux de distribution multi-sites (négoce B2B)  
Certification Data Scientist — Mines Paris PSL (2025)

[LinkedIn](https://linkedin.com/in/florent-cochet-3b3938138) · [GitHub](https://github.com/FloMind)

---

## Licence

MIT — libre d'utilisation, modification et distribution.
