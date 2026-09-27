"""Exakte Rechnung: das Standortproblem ohne Bestand (MILP) und die Mengenpartitionierung mit Bestand gegen Brute Force auf Kleinstnetzen; Grenzen."""

import pytest

import lip_costs as cs
import lip_evaluation as ev
import lip_exact as ex
import lip_scenario as sc
from helpers import tiny


@pytest.mark.parametrize("seed", range(6))
def test_ufl_milp_equals_brute_force_without_stock(seed):
    net = sc.generate(4, 6, 50, 100, seed)
    mod = cs.Model(net, cs.Econ(50, 0, 0))                                      # hz = 0: keine Bestandskosten
    value, open_set = ex.solve_ufl(mod)
    best, _count = ex.brute_force(mod)
    assert value == pytest.approx(best, abs=1e-6) and mod.evaluate(open_set, mod.nearest(open_set))["total"] == pytest.approx(value, abs=1e-6)


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("hz, rho", [(40, 0), (100, 20), (100, 60)])
def test_set_partitioning_equals_brute_force_with_stock(seed, hz, rho):
    _net, mod = tiny(seed, m=3, n=6, hz=hz, rho=rho)
    value, open_set, assign = ex.solve_setpart(mod)
    best, _count = ex.brute_force(mod)
    assert value == pytest.approx(best, abs=1e-6)
    assert mod.evaluate(open_set, assign)["total"] == pytest.approx(value, abs=1e-6)


def test_set_partitioning_refuses_large_nets():
    _net, mod = tiny(1, m=3, n=13)
    with pytest.raises(ValueError):
        ex.solve_setpart(mod)


def test_exact_is_never_worse_than_the_heuristics():
    for seed in range(4):
        r = ev.exact_compare(ev.Params(sites=4, customers=8, hz=100, rho=20, seed=seed))
        assert r["opt"] <= r["joint"] + 1e-6 <= r["naive"] + 1e-6 and r["gap_joint"] >= -1e-6 and r["opt"] <= r["two_starts"] + 1e-6


def test_exact_allowed_follows_the_limits():
    assert ev.exact_allowed(ev.Params(sites=6, customers=10)) and not ev.exact_allowed(ev.Params(sites=7, customers=10)) and not ev.exact_allowed(ev.Params(sites=6, customers=11))
