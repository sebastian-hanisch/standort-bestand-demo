"""Jede Zahl, die README und App nennen, ist hier belegt: Standardnetz und Presets (Seeds 4, 2, 200025), Verteilungen über 40 feste Netze (Seeds ab 100000), Wärmekarte über 10 feste Netze, Vergleich mit dem exakten Optimum.
Kosten sind Gleitkommazahlen (Vergleich mit Toleranz); gezählt werden nur Größen, die nicht davon abhängen, welche von mehreren gleich guten Lagermengen gewählt wird."""

import pytest

import lip_constants as C
import lip_evaluation as ev
import lip_exact as ex
import lip_heuristics as h

PCT = pytest.approx


def P(**kw):
    return ev.Params(**kw)


def _dist(**kw):
    return ev.distribution(P(**kw))["summary"]


@pytest.fixture(scope="module")
def standard():
    return ev.analyse(ev.Params())


@pytest.fixture(scope="module")
def dist_standard():
    return ev.distribution(ev.Params())


def test_standard_net_naive_against_joint(standard):
    """Standardnetz (12 Lager, 30 Kunden, Bestandsgewicht 40, Korrelation 0, Seed 4): naiv 6 Lager, 6 358; gemeinsam 3 Lager, 6 060; die naive Planung ist um 4,92 % teurer."""
    a = standard
    assert (len(a["naive"].open), len(a["joint"].open)) == (6, 3)
    assert (a["naive"].total, a["joint"].total) == (PCT(6358.3, abs=0.05), PCT(6060.2, abs=0.05)) and a["gap"] == PCT(4.918, abs=0.005)


def test_standard_net_cost_breakdown(standard):
    """Fixkosten 1 055 / 489, Transport 2 534 / 3 602, Bestand 2 769 / 1 970 (naiv / gemeinsam): weniger Lager sparen Fixkosten und Bestand, kosten Transport."""
    n, j = standard["naive"].costs, standard["joint"].costs
    assert (n["fixed"], n["transport"], n["stock"]) == (1055.0, PCT(2533.9, abs=0.05), PCT(2769.4, abs=0.05))
    assert (j["fixed"], j["transport"], j["stock"]) == (489.0, PCT(3601.6, abs=0.05), PCT(1969.6, abs=0.05))
    assert j["transport"] > n["transport"] and j["fixed"] < n["fixed"] and j["stock"] < n["stock"]


def test_reassignment_alone_closes_little_at_the_standard_net(standard):
    """Neuzuordnung allein (dieselben 6 Lager, Kunden mit echten Kosten neu verteilt): 6 348 statt 6 358, noch 4,74 % über der gemeinsamen Lösung - die Lagerwahl muss sich ändern."""
    a = standard
    assert a["reassign"].total == PCT(6347.7, abs=0.05) and a["gap_reassign"] == PCT(4.745, abs=0.005) and len(a["reassign"].open) == 6


def test_standard_net_series_over_the_stock_weight():
    """Bestandsgewicht 0 / 10 / 20 / 30 / 40 / 50 / 60 / 100: Lager der gemeinsamen Planung 6 / 6 / 5 / 4 / 3 / 3 / 2 / 2, Mehrkosten der naiven Planung 0 / 0 / 0,98 / 2,37 / 4,92 / 7,60 / 10,20 / 21,06 %; die naive Planung öffnet immer 6."""
    rows = {r["x"]: r for r in ev.hz_series(ev.Params())}
    assert [rows[x]["joint_sites"] for x in (0, 10, 20, 30, 40, 50, 60, 100)] == [6, 6, 5, 4, 3, 3, 2, 2] and all(r["naive_sites"] == 6 for r in rows.values())
    assert [rows[x]["gap"] for x in (0, 10, 20, 30, 40, 50, 60, 100)] == PCT([0.0, 0.0, 0.975, 2.365, 4.918, 7.600, 10.199, 21.061], abs=0.005)
    gaps = [rows[x]["gap"] for x in sorted(rows)]
    assert gaps == sorted(gaps)


def test_standard_net_series_over_the_correlation():
    """Bestandsgewicht 100: mit wachsender Korrelation öffnet die gemeinsame Planung mehr Lager, und die Mehrkosten der naiven Planung sinken auf 0 (Korrelation 100 %: beide Planungen fallen zusammen)."""
    rows = {r["x"]: r for r in ev.rho_series(ev.Params(hz=100))}
    assert rows[0]["gap"] == PCT(21.061, abs=0.005) and rows[100]["gap"] == PCT(0.0, abs=1e-6) and rows[100]["joint_sites"] == rows[100]["naive_sites"] == 6
    gaps = [rows[x]["gap"] for x in sorted(rows)]
    assert gaps == sorted(gaps, reverse=True) and rows[0]["joint_sites"] < rows[60]["joint_sites"] <= rows[100]["joint_sites"]


def test_two_starts_are_not_enough_at_the_standard_net():
    """Standardnetz, Bestandsgewicht 50: die Lokalsuche aus der naiven Lösung und aus 'alle offen' bleibt bei 6 858 stehen (4 Lager), mit den Ein-Lager-Starts endet sie bei 6 553 (3 Lager)."""
    net, mod = ev.build(ev.Params(hz=50))
    _v, nop = ex.solve_ufl(mod)
    two, _ = h.joint(mod, nop, singles=0)
    five, start = h.joint(mod, nop)
    assert (two.total, len(two.open)) == (PCT(6857.9, abs=0.05), 4) and (five.total, len(five.open)) == (PCT(6552.6, abs=0.05), 3) and start == "einzeln"


def test_distribution_over_40_nets(dist_standard):
    """40 feste Netze, sonst wie das Standardnetz: die naive Planung öffnet im Mittel 5,35 Lager, die gemeinsame 3,45; Mehrkosten im Mittel 4,60 % (Median 4,49 %, schlechtestes Netz 11,3 %), in 36 von 40 Netzen über 0,5 %; die Neuzuordnung
    allein schließt im Mittel 15 % dieser Mehrkosten (noch 3,89 % über der gemeinsamen Lösung); den besten Endpunkt lieferte der Start aus der naiven Lösung in 36 von 40 Netzen."""
    s = dist_standard["summary"]
    assert (s["naive_sites"], s["joint_sites"]) == (PCT(5.35), PCT(3.45)) and s["count"] == 40
    assert (s["gap_mean"], s["gap_median"], s["gap_max"]) == (PCT(4.603, abs=0.005), PCT(4.492, abs=0.005), PCT(11.32, abs=0.01)) and s["over_half"] == 36
    assert s["gap_reassign_mean"] == PCT(3.892, abs=0.005) and s["reassign_closed"] == PCT(0.1545, abs=0.0005) and s["start_naive"] == 36


@pytest.mark.parametrize("hz, mean, worst, naive_sites, joint_sites", [
    (5, 0.100, 1.19, 5.35, 5.025), (20, 1.47, 6.54, 5.35, 4.225), (40, 4.603, 11.32, 5.35, 3.45), (60, 8.415, 19.38, 5.35, 2.9), (100, 16.603, 32.19, 5.35, 1.9)])
def test_mean_extra_cost_by_stock_weight(hz, mean, worst, naive_sites, joint_sites):
    """Mehrkosten der naiven Planung über 40 Netze, Bestandsgewicht 5 / 20 / 40 / 60 / 100: Mittel 0,10 / 1,47 / 4,60 / 8,41 / 16,60 %, schlechtestes Netz 1,19 / 6,54 / 11,3 / 19,4 / 32,2 %;
    Lager der gemeinsamen Planung im Mittel 5,03 / 4,23 / 3,45 / 2,90 / 1,90 (naiv immer 5,35)."""
    s = _dist(hz=hz)
    assert s["gap_mean"] == PCT(mean, abs=0.005) and s["gap_max"] == PCT(worst, abs=0.01) and (s["naive_sites"], s["joint_sites"]) == (PCT(naive_sites), PCT(joint_sites))


@pytest.mark.parametrize("rho, mean, worst, joint_sites", [(20, 4.024, 9.66, 3.1), (40, 1.452, 4.64, 3.75), (60, 0.482, 2.33, 4.225), (80, 0.096, 0.83, 4.8)])
def test_mean_extra_cost_by_correlation(rho, mean, worst, joint_sites):
    """Bestandsgewicht 100, Korrelation 20 / 40 / 60 / 80 %: Mehrkosten der naiven Planung im Mittel 4,02 / 1,45 / 0,48 / 0,10 % (schlechtestes Netz 9,7 / 4,6 / 2,3 / 0,8 %), bei 0 % waren es 16,60 %."""
    s = _dist(hz=100, rho=rho)
    assert s["gap_mean"] == PCT(mean, abs=0.005) and s["gap_max"] == PCT(worst, abs=0.01) and s["joint_sites"] == PCT(joint_sites)


def test_no_pooling_effect_at_full_correlation_or_zero_stock_weight():
    """Korrelation 100 % (bei Bestandsgewicht 100) und Bestandsgewicht 0: in jedem der 40 Netze kosten naive und gemeinsame Planung dasselbe - der Bestand hängt dann nicht von der Zuordnung ab."""
    for kw in (dict(rho=100, hz=100), dict(hz=0)):
        rows = ev.distribution(P(**kw))["rows"]
        assert all(abs(r["naive"] - r["joint"]) < 1e-6 for r in rows), kw


@pytest.mark.parametrize("label, kw, mean, closed, naive_sites, joint_sites", [
    ("Schwankung 20", dict(cv=20), 1.003, 0.039, 5.35, 4.425),
    ("Schwankung 100", dict(cv=100), 12.343, 0.391, 5.35, 2.4),
    ("15 Kunden", dict(customers=15), 4.862, 0.231, 3.9, 2.5),
    ("60 Kunden", dict(customers=60), 4.597, 0.25, 7.325, 4.7),
    ("8 Kandidaten", dict(sites=8), 3.928, 0.176, 4.85, 3.3),
    ("20 Kandidaten", dict(sites=20), 5.658, 0.196, 5.975, 3.75),
    ("Transportsatz 20", dict(t=20), 10.856, 0.193, 3.725, 1.775),
    ("Transportsatz 100", dict(t=100), 2.515, 0.225, 6.725, 4.95),
    ("Fixkosten 50 %", dict(fixed=50), 6.761, 0.362, 6.725, 3.9),
    ("Fixkosten 200 %", dict(fixed=200), 3.221, 0.06, 4.1, 2.925),
])
def test_what_else_moves_the_effect(label, kw, mean, closed, naive_sites, joint_sites):
    """Ein Regler nach dem anderen (40 Netze, sonst Standard mit Mehrkosten 4,60 %): Schwankung 20 / 100 % 1,00 / 12,34 %; 15 / 60 Kunden 4,86 / 4,60 % (die Kundenzahl ändert kaum etwas); 8 / 20 Kandidaten 3,93 / 5,66 %;
    Transportsatz 20 / 100 10,86 / 2,52 %; Fixkosten 50 / 200 % 6,76 / 3,22 %. Die Neuzuordnung allein schließt zwischen 4 % (Schwankung 20) und 39 % (Schwankung 100) der Mehrkosten."""
    s = _dist(**kw)
    assert s["gap_mean"] == PCT(mean, abs=0.005) and s["reassign_closed"] == PCT(closed, abs=0.0005) and (s["naive_sites"], s["joint_sites"]) == (PCT(naive_sites), PCT(joint_sites)), label


def test_heatmap_over_10_nets():
    """Wärmekarte (10 feste Netze), Bestandsgewicht 5 / 20 / 40 / 60 / 100, Korrelation 0 / 20 / 60 / 100 %: Mehrkosten 0,04 / 0,69 / 2,52 / 5,54 / 14,13 % bei Korrelation 0 (bei 5: höchstens 0,04 %), bei Korrelation 100 % überall 0."""
    hm = ev.heatmap(ev.Params())
    assert hm["hz"] == C.HEAT_HZ and hm["rho"] == C.HEAT_RHO
    assert [row[0] for row in hm["grid"]] == PCT([0.04, 0.689, 2.516, 5.535, 14.132], abs=0.005)
    assert all(abs(row[3]) < 1e-6 for row in hm["grid"]) and max(hm["grid"][0]) < 0.05
    assert all(row[0] > row[1] > row[2] >= row[3] for row in hm["grid"][1:])


PRESET_ROWS = [
    # Name, Lager naiv, gesamt naiv, Lager gemeinsam, gesamt gemeinsam, Mehrkosten in %
    ("🗺️ Standardnetz", 6, 6358.3, 3, 6060.2, 4.918),
    ("🏭 Wenige große Lager", 6, 10512.3, 2, 8683.5, 21.061),
    ("🔗 Korrelierte Nachfrage", 6, 17672.6, 6, 17672.2, 0.002),
    ("💤 Bestand kaum relevant", 6, 3935.1, 6, 3935.1, 0.0),
    ("🎲 Stark schwankende Nachfrage", 6, 9127.6, 2, 7855.5, 16.193),
    ("🚚 Billiger Transport", 4, 4185.2, 1, 3623.6, 15.498),
    ("🧮 Kleinnetz mit exaktem Optimum", 3, 3012.2, 2, 2808.8, 7.242),
    ("🧲 Ein Start reicht nicht", 3, 4894.1, 1, 4459.5, 9.746),
]


@pytest.mark.parametrize("name, sites_naive, total_naive, sites_joint, total_joint, gap", PRESET_ROWS)
def test_preset_help_numbers(name, sites_naive, total_naive, sites_joint, total_joint, gap):
    """Zahlen der Preset-Hilfetexte: Lager und Gesamtkosten der naiven und der gemeinsamen Planung und die Mehrkosten der naiven Planung."""
    a = ev.analyse(ev.Params(**C.PRESETS[name]))
    assert (len(a["naive"].open), len(a["joint"].open)) == (sites_naive, sites_joint)
    assert (a["naive"].total, a["joint"].total) == (PCT(total_naive, abs=0.05), PCT(total_joint, abs=0.05)) and a["gap"] == PCT(gap, abs=0.005)


def test_preset_stock_shares():
    """Wenige große Lager: die naive Planung zahlt 6 923 Bestand von 10 512; Bestand kaum relevant: 346 von 3 935."""
    a = ev.analyse(ev.Params(**C.PRESETS["🏭 Wenige große Lager"]))
    assert a["naive"].costs["stock"] == PCT(6923.4, abs=0.05) and a["naive"].total == PCT(10512.3, abs=0.05)
    b = ev.analyse(ev.Params(**C.PRESETS["💤 Bestand kaum relevant"]))
    assert b["naive"].costs["stock"] == PCT(346.2, abs=0.05) and b["naive"].total == PCT(3935.1, abs=0.05)


def test_preset_small_net_exact():
    """Kleinnetz (6 Lager, 10 Kunden, Seed 2): das exakte Optimum 2 808,8 mit 2 Lagern; die Lokalsuche trifft es, die naive Planung ist 7,24 % darüber."""
    r = ev.exact_compare(ev.Params(**C.PRESETS["🧮 Kleinnetz mit exaktem Optimum"]))
    assert r["opt"] == PCT(2808.8, abs=0.05) and len(r["opt_sites"]) == 2 and abs(r["gap_joint"]) < 1e-4 and r["gap_naive"] == PCT(7.242, abs=0.005)


def test_preset_one_start_is_not_enough():
    """Preset 'Ein Start reicht nicht' (5 Lager, 8 Kunden, Bestandsgewicht 100, Korrelation 20 %, Seed 200025): das Optimum 4 459,5 öffnet 1 Lager; die Lokalsuche mit fünf Starts trifft es, mit zwei Starts (naiv, alle offen) endet sie
    4,76 % darüber bei 2 Lagern (4 672), die naive Planung 9,75 % darüber (3 Lager)."""
    r = ev.exact_compare(ev.Params(**C.PRESETS["🧲 Ein Start reicht nicht"]))
    assert r["opt"] == PCT(4459.5, abs=0.05) and len(r["opt_sites"]) == 1 and abs(r["gap_joint"]) < 1e-4
    assert r["gap_two"] == PCT(4.760, abs=0.005) and r["two_starts"] == PCT(4672.0, abs=0.5) and r["gap_naive"] == PCT(9.746, abs=0.005)


@pytest.mark.parametrize("hz, rho, exact5, exact2, worst5, worst2", [(40, 0, 39, 39, 0.039, 0.04), (100, 0, 40, 40, 0.0, 0.0), (100, 20, 40, 39, 0.0, 2.06)])
def test_local_search_against_the_exact_optimum_on_small_nets(hz, rho, exact5, exact2, worst5, worst2):
    """Kleinnetze (5 Lager, 8 Kunden, je 40 feste Netze; Bestandsgewicht 40 / 100 / 100, Korrelation 0 / 0 / 20 %): die Lokalsuche mit fünf Starts trifft das exakte Optimum in 39 / 40 / 40 Netzen (schlechtestes Netz 0,04 % darüber),
    mit zwei Starts in 39 / 40 / 39 (schlechtestes Netz 0,04 / 0,00 / 2,06 % darüber); zusammen 119 von 120 mit fünf Starts."""
    g5, g2 = [], []
    for s in C.SWEEP_SEEDS:
        r = ev.exact_compare(ev.Params(sites=5, customers=8, hz=hz, rho=rho, seed=s))
        g5.append(r["gap_joint"])
        g2.append(r["gap_two"])
    assert sum(g < 1e-4 for g in g5) == exact5 and sum(g < 1e-4 for g in g2) == exact2 and max(g2) == PCT(worst2, abs=0.005) and max(g5) == PCT(worst5, abs=0.005) and min(g5 + g2) > -1e-4


@pytest.mark.parametrize("hz, rho, mean_gain, worse, worst", [(40, 0, 0.121, 4, 3.01), (100, 0, 0.194, 5, 3.45), (100, 20, 0.053, 3, 1.57)])
def test_two_starts_against_five_starts_on_the_standard_size(hz, rho, mean_gain, worse, worst):
    """Standardgröße (12 Lager, 30 Kunden, 40 Netze), Bestandsgewicht 40 / 100 / 100, Korrelation 0 / 0 / 20 %: zwei Starts liegen im Mittel 0,12 / 0,19 / 0,05 % über fünf Starts, in 4 / 5 / 3 Netzen schlechter (bis 3,0 / 3,5 / 1,6 %)."""
    gains, n_worse = [], 0
    for seed in C.SWEEP_SEEDS:
        net, mod = ev.build(ev.Params(hz=hz, rho=rho), seed)
        _v, nop = ex.solve_ufl(mod)
        two, _ = h.joint(mod, nop, singles=0)
        five, _ = h.joint(mod, nop)
        gains.append(100 * (two.total - five.total) / five.total)
        n_worse += two.total > five.total + 1e-9
    assert sum(gains) / len(gains) == PCT(mean_gain, abs=0.005) and n_worse == worse and max(gains) == PCT(worst, abs=0.01) and min(gains) > -1e-9
