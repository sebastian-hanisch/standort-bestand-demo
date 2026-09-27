"""Exakte Rechnung (HiGHS über scipy): das Standortproblem ohne Bestand (naive Lösung) und, für kleine Netze, das Optimum MIT Bestandskosten per Mengenpartitionierung.

Mit Bestandskosten ist das Problem nicht mehr linear in der Zuordnung: die Kosten eines Lagers hängen von der ganzen Kundenmenge ab (konkave Wurzel). Für kleine Netze lässt sich jede Kundenteilmenge S je Lager als eigene Spalte
schreiben (Kosten = Fixkosten + Transport + Bestand von S), jeder Kunde wird genau einmal überdeckt, jedes Lager höchstens einmal genutzt: das ist eine Mengenpartitionierung mit m * 2^n Spalten (nur für n <= 12 gedacht).
"""

from itertools import product
from math import sqrt

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

EPS = 1e-6
SETPART_MAX_CUSTOMERS = 11
SETPART_MAX_SITES = 6


def solve_ufl(mod):
    """Das Standortproblem ohne Bestand (nur Fixkosten + Transport), exakt: (Wert, geöffnete Lager). Aus dieser Lösung entsteht die 'naive' Planung."""
    m, n = mod.m, mod.n
    nv = m + m * n
    cost = np.concatenate([np.array(mod.f), np.array(mod.tc).ravel()])
    rows, cols, vals, lo, hi = [], [], [], [], []
    r = 0
    for j in range(n):
        for i in range(m):
            rows.append(r); cols.append(m + i * n + j); vals.append(1.0)
        lo.append(1.0); hi.append(1.0); r += 1
    for i in range(m):
        for j in range(n):
            rows += [r, r]; cols += [m + i * n + j, i]; vals += [1.0, -1.0]
            lo.append(-np.inf); hi.append(0.0); r += 1
    a = coo_matrix((vals, (rows, cols)), shape=(r, nv)).tocsr()
    res = milp(cost, constraints=LinearConstraint(a, np.array(lo), np.array(hi)), integrality=np.concatenate([np.ones(m), np.zeros(m * n)]), bounds=Bounds(0, 1),
               options={"time_limit": 60, "mip_rel_gap": 0.0})
    if res.status != 0:
        raise RuntimeError("MILP nicht optimal gelöst: " + str(res.message))
    open_set = tuple(i for i in range(m) if res.x[i] > 0.5)
    return float(res.fun), open_set


def _site_cost(mod, i, members):
    s2 = sum(mod.sig2[j] for j in members)
    s1 = sum(mod.sig[j] for j in members)
    return mod.f[i] + sum(mod.tc[i][j] for j in members) + mod.stock(s2, s1)


def solve_setpart(mod):
    """Optimum mit Bestandskosten per Mengenpartitionierung: (Wert, geöffnete Lager, Zuordnung). Nur für kleine Netze (n <= 12); die Auswahl bei mehreren Optima ist nicht eindeutig, nur der Wert ist es."""
    m, n = mod.m, mod.n
    if n > 12:
        raise ValueError("Mengenpartitionierung nur bis 12 Kunden")
    cols_mask, cols_site, costs = [], [], []
    for i in range(m):
        for mask in range(1, 1 << n):
            members = [j for j in range(n) if mask >> j & 1]
            cols_mask.append(mask)
            cols_site.append(i)
            costs.append(_site_cost(mod, i, members))
    k = len(costs)
    rows, cols, vals = [], [], []
    for c, (mask, i) in enumerate(zip(cols_mask, cols_site)):
        for j in range(n):
            if mask >> j & 1:
                rows.append(j); cols.append(c); vals.append(1.0)
        rows.append(n + i); cols.append(c); vals.append(1.0)
    a = coo_matrix((vals, (rows, cols)), shape=(n + m, k)).tocsr()
    lo = np.concatenate([np.ones(n), np.zeros(m)])
    hi = np.concatenate([np.ones(n), np.ones(m)])
    res = milp(np.array(costs), constraints=LinearConstraint(a, lo, hi), integrality=np.ones(k), bounds=Bounds(0, 1), options={"time_limit": 120, "mip_rel_gap": 0.0})
    if res.status != 0:
        raise RuntimeError("MILP nicht optimal gelöst: " + str(res.message))
    assign = [None] * n
    for c in range(k):
        if res.x[c] > 0.5:
            for j in range(n):
                if cols_mask[c] >> j & 1:
                    assign[j] = cols_site[c]
    return float(res.fun), tuple(sorted(set(assign))), tuple(assign)


def brute_force(mod):
    """Alle Zuordnungen (m^n, nur für Kleinstnetze): (Optimalwert, Anzahl optimaler Zuordnungen)."""
    best, count = None, 0
    for assign in product(range(mod.m), repeat=mod.n):
        op = tuple(sorted(set(assign)))
        v = mod.evaluate(op, assign)["total"]
        if best is None or v < best - 1e-9:
            best, count = v, 1
        elif abs(v - best) <= 1e-9:
            count += 1
    return best, count
