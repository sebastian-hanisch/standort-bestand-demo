"""Gemeinsame Hilfen der Tests: kleine Netze von Hand und kleine Zufallsnetze für Brute-Force-Vergleiche."""

import lip_costs as cs
import lip_scenario as sc


def hand(sites, custs, mu, f, cv=50, t=100, hz=10, rho=0):
    """Netz aus Positionen von Hand (Kosten: `t` = 100 ist Satz 1,0) und passendes Kostenmodell."""
    net = sc._build("hand", sites, custs, mu, cv, f)
    return net, cs.Model(net, cs.Econ(t, hz, rho))


def tiny(seed, m=3, n=6, hz=40, rho=0, t=50, cv=50, fixed=100):
    net = sc.generate(m, n, cv, fixed, seed)
    return net, cs.Model(net, cs.Econ(t, hz, rho))
