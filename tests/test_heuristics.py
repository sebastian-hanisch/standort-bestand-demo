"""Verfahren: Kundenzüge, Lokalsuche und gemeinsame Optimierung - Kosten sinken nie, Zwischenergebnisse stimmen mit einer Vollrechnung überein, Grenzfälle."""

import pytest

import lip_evaluation as ev
import lip_exact as ex
import lip_heuristics as h
from helpers import tiny


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("hz, rho", [(40, 0), (100, 20), (100, 0)])
def test_descend_never_raises_the_cost_and_ends_without_an_improving_customer_move(seed, hz, rho):
    _net, mod = tiny(seed, m=5, n=12, hz=hz, rho=rho)
    allowed = list(range(mod.m))
    start = mod.nearest(allowed)
    assign, _ = h.descend(mod, allowed, start)
    used = h.used_sites(assign)
    total = mod.evaluate(used, assign)["total"]
    assert total <= mod.evaluate(h.used_sites(start), start)["total"] + 1e-9
    for j in range(mod.n):                                   # kein Einzelzug verbessert die Gesamtkosten mehr (Vollrechnung, nicht die inkrementelle)
        for b in allowed:
            if b == assign[j]:
                continue
            trial = list(assign)
            trial[j] = b
            assert mod.evaluate(h.used_sites(trial), trial)["total"] >= total - 1e-7


@pytest.mark.parametrize("seed", range(6))
def test_local_search_moves_each_lower_the_cost_and_end_at_the_reported_total(seed):
    _net, mod = tiny(seed, m=6, n=14, hz=60)
    _v, nop = ex.solve_ufl(mod)
    sol = h.local_search(mod, nop)
    totals = [t for _k, _i, t in sol.moves]
    assert totals == sorted(totals, reverse=True) and (not totals or totals[-1] == pytest.approx(sol.total))
    assert sol.costs == mod.evaluate(sol.open, sol.assign) and set(sol.assign) == set(sol.open)
    assert sol.total <= h.naive(mod, nop).total + 1e-9


@pytest.mark.parametrize("seed", range(6))
def test_joint_is_never_worse_than_naive_or_the_reassignment_alone(seed):
    _net, mod = tiny(seed, m=6, n=14, hz=80)
    _v, nop = ex.solve_ufl(mod)
    joint, start = h.joint(mod, nop)
    assert joint.total <= h.reassign_only(mod, nop).total + 1e-9 <= h.naive(mod, nop).total + 2e-9
    assert start in ("naiv", "alle", "einzeln") and joint.evals > 0


def test_more_starts_never_hurt():
    for seed in range(8):
        _net, mod = tiny(seed, m=8, n=16, hz=100, rho=20)
        _v, nop = ex.solve_ufl(mod)
        assert h.joint(mod, nop)[0].total <= h.joint(mod, nop, singles=0)[0].total + 1e-9


@pytest.mark.parametrize("kwargs", [dict(hz=0), dict(rho=100, hz=100)])
def test_without_a_pooling_effect_joint_and_naive_planning_coincide(kwargs):
    """hz = 0: kein Bestand. rho = 1: der Bestand ist die Summe der Einzelbestände, unabhängig von der Zuordnung - eine Konstante."""
    for seed in range(8):
        _net, mod = tiny(seed, m=6, n=14, **kwargs)
        _v, nop = ex.solve_ufl(mod)
        assert h.joint(mod, nop)[0].total == pytest.approx(h.naive(mod, nop).total, abs=1e-7)


def test_naive_uses_the_nearest_site_and_its_costs_are_the_real_ones():
    _net, mod = tiny(3, m=5, n=10, hz=50)
    sol = h.naive(mod, (0, 2))
    assert list(sol.assign) == mod.nearest((0, 2)) and sol.costs == mod.evaluate(sol.open, sol.assign)


def test_solve_for_charges_only_sites_that_actually_serve_customers():
    _net, mod = tiny(2, m=6, n=10, hz=80)
    sol = h.solve_for(mod, range(mod.m))
    assert set(sol.open) == set(sol.assign) and len(sol.open) < mod.m


def test_single_customer_and_single_site_edge_cases():
    _net, mod = tiny(1, m=1, n=5, hz=60)
    sol, _ = h.joint(mod, (0,))
    assert sol.open == (0,) and set(sol.assign) == {0}
    _net, mod = tiny(1, m=4, n=1, hz=60)
    _v, nop = ex.solve_ufl(mod)
    assert len(h.joint(mod, nop)[0].open) == 1


def test_analyse_is_deterministic():
    p = ev.Params(sites=8, customers=16)
    a, b = ev.analyse(p), ev.analyse(p)
    assert (a["naive"], a["joint"], a["reassign"]) == (b["naive"], b["joint"], b["reassign"])
