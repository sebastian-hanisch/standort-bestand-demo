"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Standort + Bestand: warum wenige große Lager billiger sind, als die Standortplanung denkt"."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------
SITES_MIN, SITES_MAX, DEFAULT_SITES = 4, 20, 12
CUST_MIN, CUST_MAX, DEFAULT_CUST = 8, 60, 30
CV_MIN, CV_MAX, DEFAULT_CV = 10, 100, 50
FIXED_MIN, FIXED_MAX, DEFAULT_FIXED = 50, 200, 100
T_MIN, T_MAX, DEFAULT_T = 10, 150, 50
HZ_MIN, HZ_MAX, DEFAULT_HZ = 0, 100, 40
RHO_MIN, RHO_MAX, DEFAULT_RHO = 0, 100, 0
DEFAULT_SEED = 4
SEED_MAX = 2_000_000_000
EXACT_MAX_CUSTOMERS, EXACT_MAX_SITES = 10, 6      # Mengenpartitionierung: 2^n Spalten je Lager

# --- feste Seed-Mengen (unabhängig vom Nutzer-Seed) ---------------------------------------------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
HEAT_SEEDS = DIST_SEEDS[:10]
HZ_GRID = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
RHO_GRID = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
HEAT_HZ = (5, 20, 40, 60, 100)
HEAT_RHO = (0, 20, 60, 100)

COLORS = {"naive": "#ff7f0e", "joint": "#2ca02c", "reassign": "#1f77b4", "site": "#7f8c8d", "closed": "#c7c7c7", "line": "#b0b0b0", "fixed": "#8c564b", "transport": "#1f77b4", "stock": "#d62728", "exact": "#111111"}

# --- Presets -----------------------------------------------------------------------------------------------------------------
_BASE = dict(sites=DEFAULT_SITES, customers=DEFAULT_CUST, cv=DEFAULT_CV, fixed=DEFAULT_FIXED, t=DEFAULT_T, hz=DEFAULT_HZ, rho=DEFAULT_RHO, seed=DEFAULT_SEED)
PRESETS = {
    "🗺️ Standardnetz": {**_BASE},
    "🏭 Wenige große Lager": {**_BASE, "hz": 100},
    "🔗 Korrelierte Nachfrage": {**_BASE, "hz": 100, "rho": 80},
    "💤 Bestand kaum relevant": {**_BASE, "hz": 5},
    "🎲 Stark schwankende Nachfrage": {**_BASE, "cv": 100},
    "🚚 Billiger Transport": {**_BASE, "t": 20},
    "🧮 Kleinnetz mit exaktem Optimum": {**_BASE, "sites": 6, "customers": 10, "seed": 2},
    "🧲 Ein Start reicht nicht": {**_BASE, "sites": 5, "customers": 8, "hz": 100, "rho": 20, "seed": 200025},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py belegt.
PRESET_HELP = {
    "🗺️ Standardnetz": "12 Kandidaten-Lager, 30 Kunden, Bestandsgewicht 40, keine Korrelation: die naive Planung öffnet 6 Lager und kostet 6 358, die gemeinsame öffnet 3 und kostet 6 060 - die naive ist 4,92 % teurer. Fixkosten und Bestand sinken (1 055 auf 489, 2 769 auf 1 970), der Transport steigt (2 534 auf 3 602).",
    "🏭 Wenige große Lager": "Bestandsgewicht 100: die naive Planung öffnet 6 Lager (10 512, davon 6 923 Bestand), die gemeinsame nur 2 (8 683) - 21,06 % Mehrkosten. Je teurer der Bestand, desto stärker lohnt sich das Bündeln.",
    "🔗 Korrelierte Nachfrage": "Bestandsgewicht 100, aber Korrelation 80 %: beide Planungen öffnen 6 Lager, der Unterschied liegt bei 0,002 %. Wenn alle Kunden gleichzeitig schwanken, gleicht sich nichts aus und Bündeln spart keinen Bestand.",
    "💤 Bestand kaum relevant": "Bestandsgewicht 5: der Bestand macht 346 von 3 935 aus; naive und gemeinsame Planung sind identisch (6 Lager). Ist der Bestand klein gegen Fixkosten und Transport, genügt die Standortplanung ohne Bestand.",
    "🎲 Stark schwankende Nachfrage": "Schwankung 100 % (statt 50 %): die naive Planung öffnet 6 Lager (9 128), die gemeinsame 2 (7 856) - 16,19 % Mehrkosten statt 4,92 %. Je unsicherer die Nachfrage, desto wertvoller das Bündeln.",
    "🚚 Billiger Transport": "Transportsatz 20 (statt 50): die naive Planung öffnet 4 Lager (4 185), die gemeinsame ein einziges (3 624) - 15,50 % Mehrkosten. Billiger Transport nimmt dem Bündeln sein Gegengewicht.",
    "🧮 Kleinnetz mit exaktem Optimum": "6 Kandidaten, 10 Kunden, Seed 2: das exakte Optimum (Knopf im Abschnitt 'Wie weit ist die Lokalsuche vom Optimum?') ist 2 808,8 mit 2 Lagern; die gemeinsame Lokalsuche trifft es, die naive Planung ist 7,24 % darüber.",
    "🧲 Ein Start reicht nicht": "5 Kandidaten, 8 Kunden, Bestandsgewicht 100, Korrelation 20 %: das Optimum öffnet 1 Lager (4 459,5). Die Lokalsuche mit fünf Starts trifft es; nur aus der naiven Lösung und aus 'alle offen' bliebe sie bei 4 672 (2 Lager, 4,76 % darüber), die naive Planung liegt 9,75 % darüber. Der Exakt-Knopf zeigt den Vergleich.",
}
