"""Auswertungen: eine Analyse für das eingestellte Netz, Reihen über das Bestandsgewicht und die Korrelation, Verteilung über 40 feste Netze, Wärmekarte, Vergleich mit dem exakten Optimum (Kleinnetz)."""

import statistics
from dataclasses import dataclass

import lip_constants as C
import lip_costs as cs
import lip_exact as ex
import lip_heuristics as h
import lip_scenario as sc


@dataclass(frozen=True)
class Params:
    sites: int = C.DEFAULT_SITES
    customers: int = C.DEFAULT_CUST
    cv: int = C.DEFAULT_CV
    fixed: int = C.DEFAULT_FIXED
    t: int = C.DEFAULT_T
    hz: int = C.DEFAULT_HZ
    rho: int = C.DEFAULT_RHO
    seed: int = C.DEFAULT_SEED

    def econ(self):
        return cs.Econ(self.t, self.hz, self.rho)


def gap_pct(value, base):
    """Mehrkosten von `value` gegenüber `base` in Prozent."""
    return 100 * (value - base) / base


def build(params, seed=None):
    net = sc.generate(params.sites, params.customers, params.cv, params.fixed, params.seed if seed is None else seed)
    return net, cs.Model(net, params.econ())


def _solve_all(mod):
    """Naive Lösung (Standortproblem ohne Bestand, bewertet mit den echten Kosten), Neuzuordnung allein, gemeinsame Optimierung."""
    ufl_value, naive_open = ex.solve_ufl(mod)
    naive = h.naive(mod, naive_open)
    reassign = h.reassign_only(mod, naive_open)
    joint, start = h.joint(mod, naive_open)
    return {"ufl_value": ufl_value, "naive_open": naive_open, "naive": naive, "reassign": reassign, "joint": joint, "start": start}


def analyse(params):
    net, mod = build(params)
    out = _solve_all(mod)
    out.update(net=net, mod=mod)
    out["gap"] = gap_pct(out["naive"].total, out["joint"].total)
    out["gap_reassign"] = gap_pct(out["reassign"].total, out["joint"].total)
    return out


def try_open(mod, chosen):
    """Kosten, wenn genau `chosen` geöffnet werden darf (Kunden bestmöglich zugeordnet; ein Lager ohne Kunden wird nicht bezahlt)."""
    return h.solve_for(mod, chosen)


def hz_series(params, grid=C.HZ_GRID):
    """Für das eingestellte Netz: naive und gemeinsame Lösung über das Bestandsgewicht (die naive Lagerwahl hängt vom Bestand nicht ab)."""
    net, mod0 = build(params)
    _v, naive_open = ex.solve_ufl(mod0)
    rows = []
    for hz in grid:
        mod = cs.Model(net, cs.Econ(params.t, hz, params.rho))
        naive = h.naive(mod, naive_open)
        joint, _ = h.joint(mod, naive_open)
        rows.append({"x": hz, "naive_sites": len(naive.open), "joint_sites": len(joint.open), "gap": gap_pct(naive.total, joint.total), "naive": naive.total, "joint": joint.total})
    return rows


def rho_series(params, grid=C.RHO_GRID):
    net, mod0 = build(params)
    _v, naive_open = ex.solve_ufl(mod0)
    rows = []
    for rho in grid:
        mod = cs.Model(net, cs.Econ(params.t, params.hz, rho))
        naive = h.naive(mod, naive_open)
        joint, _ = h.joint(mod, naive_open)
        rows.append({"x": rho, "naive_sites": len(naive.open), "joint_sites": len(joint.open), "gap": gap_pct(naive.total, joint.total), "naive": naive.total, "joint": joint.total})
    return rows


def one_net(params, seed):
    net, mod = build(params, seed)
    r = _solve_all(mod)
    return {"seed": seed, "naive": r["naive"].total, "reassign": r["reassign"].total, "joint": r["joint"].total, "naive_sites": len(r["naive"].open), "joint_sites": len(r["joint"].open),
            "gap": gap_pct(r["naive"].total, r["joint"].total), "gap_reassign": gap_pct(r["reassign"].total, r["joint"].total), "start": r["start"]}


def distribution(params, seeds=C.SWEEP_SEEDS):
    """Verteilung der Mehrkosten der naiven Lösung über feste Netze (gleiche Regler, andere Karten)."""
    rows = [one_net(params, s) for s in seeds]
    gaps = [r["gap"] for r in rows]
    gaps_r = [r["gap_reassign"] for r in rows]
    return {"rows": rows, "summary": summarize(rows), "gaps": gaps, "gaps_reassign": gaps_r}


def summarize(rows):
    gaps = [r["gap"] for r in rows]
    gaps_r = [r["gap_reassign"] for r in rows]
    mean = statistics.fmean(gaps)
    return {"count": len(rows), "gap_mean": mean, "gap_median": statistics.median(gaps), "gap_max": max(gaps), "gap_min": min(gaps), "over_half": sum(1 for g in gaps if g > 0.5),
            "gap_reassign_mean": statistics.fmean(gaps_r), "reassign_closed": 1 - statistics.fmean(gaps_r) / mean if mean > 1e-9 else None,
            "naive_sites": statistics.fmean(r["naive_sites"] for r in rows), "joint_sites": statistics.fmean(r["joint_sites"] for r in rows),
            "start_naive": sum(1 for r in rows if r["start"] == "naiv")}


def heatmap(params, hz_grid=C.HEAT_HZ, rho_grid=C.HEAT_RHO, seeds=C.HEAT_SEEDS):
    """Mittlere Mehrkosten der naiven Lösung je (Bestandsgewicht, Korrelation) über feste Netze. Die naive Lagerwahl hängt nur von den Netzen ab, wird also je Netz einmal gerechnet."""
    nets = []
    for s in seeds:
        net, mod = build(params, s)
        _v, naive_open = ex.solve_ufl(mod)
        nets.append((net, naive_open))
    grid = []
    for hz in hz_grid:
        row = []
        for rho in rho_grid:
            gaps = []
            for net, naive_open in nets:
                mod = cs.Model(net, cs.Econ(params.t, hz, rho))
                naive = h.naive(mod, naive_open)
                joint, _ = h.joint(mod, naive_open)
                gaps.append(gap_pct(naive.total, joint.total))
            row.append(statistics.fmean(gaps))
        grid.append(row)
    return {"hz": tuple(hz_grid), "rho": tuple(rho_grid), "grid": grid}


def exact_allowed(params):
    return params.customers <= C.EXACT_MAX_CUSTOMERS and params.sites <= C.EXACT_MAX_SITES


def exact_compare(params):
    """Kleinnetz: das Optimum mit Bestandskosten (Mengenpartitionierung) gegen die gemeinsame Lokalsuche und die naive Lösung."""
    a = analyse(params)
    opt, opt_sites, _assign = ex.solve_setpart(a["mod"])
    two, _ = h.joint(a["mod"], a["naive_open"], singles=0)
    return {"opt": opt, "opt_sites": opt_sites, "joint": a["joint"].total, "two_starts": two.total, "naive": a["naive"].total, "gap_joint": gap_pct(a["joint"].total, opt),
            "gap_two": gap_pct(two.total, opt), "gap_naive": gap_pct(a["naive"].total, opt), "a": a}
