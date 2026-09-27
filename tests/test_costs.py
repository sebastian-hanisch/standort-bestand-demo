"""Kostenmodell: Formel von Hand nachgerechnet, Grenzfälle Korrelation 0 und 1, Zuordnung zum nächsten Lager, Aufteilung der Kosten."""

import math

import pytest

import lip_costs as cs
from helpers import hand


def test_stock_formula_at_the_correlation_limits():
    net, mod = hand([(0, 0)], [(10, 0), (0, 10)], [10, 10], [100], cv=50, hz=10, rho=0)
    s2, s1 = sum(mod.sig2), sum(mod.sig)
    assert (s2, s1) == (50.0, 10.0)
    assert mod.stock(s2, s1) == pytest.approx(10 * math.sqrt(50))                   # rho = 0: Wurzel aus der Summe der Varianzen
    mod1 = cs.Model(net, cs.Econ(100, 10, 100))
    assert mod1.stock(s2, s1) == pytest.approx(10 * 10)                              # rho = 1: Summe der Standardabweichungen
    mod_half = cs.Model(net, cs.Econ(100, 10, 50))
    assert mod_half.stock(s2, s1) == pytest.approx(10 * math.sqrt(0.5 * 50 + 0.5 * 100))


def test_pooling_makes_one_big_stock_cheaper_than_two_small_ones():
    _net, mod = hand([(0, 0)], [(1, 1), (2, 2)], [10, 10], [0], cv=50, hz=10, rho=0)
    assert mod.stock(mod.sig2[0], mod.sig[0]) * 2 > mod.stock(sum(mod.sig2), sum(mod.sig))
    assert mod.stock(mod.sig2[0], mod.sig[0]) * 2 == pytest.approx(2 * 10 * 5)
    assert mod.stock(sum(mod.sig2), sum(mod.sig)) == pytest.approx(10 * math.sqrt(50))


def test_evaluate_splits_fixed_transport_and_stock():
    net, mod = hand([(0, 0), (50, 0)], [(10, 0), (40, 0)], [10, 20], [100, 200], cv=50, t=100, hz=10, rho=0)
    c = mod.evaluate((0, 1), [0, 1])
    assert c["fixed"] == 300 and c["transport"] == pytest.approx(100 + 200) and c["stock"] == pytest.approx(10 * 5 + 10 * 10)      # Zehntel-Abstand je 100, Satz 1,0
    assert c["total"] == pytest.approx(c["fixed"] + c["transport"] + c["stock"])


def test_open_site_without_customers_pays_only_its_fixed_cost():
    net, mod = hand([(0, 0), (50, 0)], [(10, 0)], [10], [100, 200])
    c = mod.evaluate((0, 1), [0])
    assert c["fixed"] == 300 and c["stock"] == pytest.approx(mod.stock(mod.sig2[0], mod.sig[0]))


def test_hz_zero_removes_the_stock_term_and_rho_one_makes_it_independent_of_the_assignment():
    net, mod0 = hand([(0, 0), (50, 0)], [(10, 0), (40, 0)], [10, 20], [100, 200], hz=0)
    assert mod0.evaluate((0, 1), [0, 1])["stock"] == 0.0
    mod1 = cs.Model(net, cs.Econ(100, 10, 100))
    assert mod1.evaluate((0, 1), [0, 1])["stock"] == pytest.approx(mod1.evaluate((0, 1), [1, 0])["stock"])
    assert mod1.evaluate((0, 1), [0, 1])["stock"] == pytest.approx(10 * sum(mod1.sig))


def test_nearest_picks_the_closest_allowed_site_and_the_lower_index_on_ties():
    net, mod = hand([(0, 0), (20, 0), (10, 0)], [(10, 0), (0, 0), (30, 0)], [10, 10, 10], [1, 1, 1])
    assert mod.nearest([0, 1, 2]) == [2, 0, 1]
    assert mod.nearest([0, 1]) == [0, 0, 1]                # Kunde 0 liegt genau zwischen 0 und 1: Gleichstand geht an Lager 0


def test_transport_is_demand_times_distance_times_rate():
    net, mod = hand([(0, 0)], [(30, 40)], [10], [0], t=50)
    assert mod.tc[0][0] == pytest.approx(10 * 500 * 50 / 1000)                          # Zehntel-Abstand 500


def test_load_reports_customers_demand_and_standard_deviation():
    net, mod = hand([(0, 0)], [(1, 0), (2, 0)], [10, 30], [0], cv=50, rho=0)
    ld = mod.load((0,), [0, 0])
    assert ld[0]["customers"] == 2 and ld[0]["mu"] == 40 and ld[0]["sd"] == pytest.approx(math.sqrt(25 + 225))
