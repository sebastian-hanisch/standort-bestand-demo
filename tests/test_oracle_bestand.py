"""Orakel-Test: Kosten über die Kovarianzmatrix (statt der Wurzelformel), Lokaloptimalität von Kundenzügen und Lagermengen-Suche über volle Neubewertung, Optimum per Brute Force über alle Zuordnungen."""

import itertools
import math
import random

import numpy as np
import pytest

import lip_costs as cs
import lip_exact as ex
import lip_heuristics as h
import lip_scenario as sc


def _net(rng, m, n, grid):
    sites = [(rng.randint(0, grid), rng.randint(0, grid)) for _ in range(m)]
    custs = [(rng.randint(0, grid), rng.randint(0, grid)) for _ in range(n)]
    return sc._build("hand", sites, custs, [rng.randint(1, 15) for _ in range(n)], rng.choice([10, 50, 100]), [rng.randint(10, 300) for _ in range(m)])


def _cost(net, econ, assign):
    """Gesamtkosten unabhängig: Bestand aus der Kovarianzmatrix (Gleichkorrelation), Transport aus exakter Entfernung in Karteneinheiten."""
    total = 0.0
    for i in set(assign):
        mem = [j for j, a in enumerate(assign) if a == i]
        sig = np.array([net.mu[j] * net.cv / 100 for j in mem])
        corr = np.full((len(mem), len(mem)), econ.rho / 100)
        np.fill_diagonal(corr, 1.0)
        total += net.f[i] + econ.hz * math.sqrt(float(sig @ corr @ sig))
        total += sum(net.mu[j] * (math.isqrt(100 * ((net.site_pos[i][0] - net.cust_pos[j][0]) ** 2 + (net.site_pos[i][1] - net.cust_pos[j][1]) ** 2)) / 10) * econ.t / 100 for j in mem)
    return total


@pytest.mark.parametrize("seed", range(12))
def test_costs_equal_covariance_formula_and_search_results_are_locally_optimal(seed):
    rng = random.Random(seed)
    m, n = rng.randint(2, 4), rng.randint(3, 6)
    net = _net(rng, m, n, rng.choice([3, 10, 60]))
    econ = cs.Econ(rng.choice([10, 50, 150]), rng.choice([0, 40, 100]), rng.choice([0, 20, 80, 100]))
    mod = cs.Model(net, econ)
    best = min(_cost(net, econ, a) for a in itertools.product(range(m), repeat=n))
    for assign in itertools.islice(itertools.product(range(m), repeat=n), 0, None, 7):
        assert mod.evaluate(tuple(sorted(set(assign))), assign)["total"] == pytest.approx(_cost(net, econ, assign), rel=1e-9)
    assert ex.brute_force(mod)[0] == pytest.approx(best)
    assert ex.solve_setpart(mod)[0] == pytest.approx(best, rel=1e-9)
    _v, naive_open = ex.solve_ufl(mod)
    joint, _name = h.joint(mod, naive_open)
    assert joint.total >= best - 1e-9 and joint.total == pytest.approx(_cost(net, econ, joint.assign), rel=1e-9)
    asg, _e = h.descend(mod, range(m), mod.nearest(range(m)))
    cur = _cost(net, econ, asg)
    for j in range(n):
        for b in range(m):
            if b != asg[j]:
                a2 = list(asg)
                a2[j] = b
                assert _cost(net, econ, a2) >= cur - 1e-9
    ls = h.local_search(mod, naive_open)
    op = set(ls.open)
    for i in range(m):
        if op ^ {i}:
            assert h.solve_for(mod, op ^ {i}).total >= ls.total - 1e-8
