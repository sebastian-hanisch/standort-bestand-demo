"""Szenario: Standortplanung mit Bestandskosten (Location-Inventory, Risk Pooling): welche Lager werden eröffnet, wenn jedes Lager neben Fixkosten und Transport auch einen Sicherheitsbestand hält,
der mit der bedienten Nachfrage nur mit der Wurzel wächst?

Alles Geometrische ist ganzzahlig und läuft über einen eigenen Zufallsgenerator (SplitMix64 auf Python-Ints, Kopie aus `ufl_scenario.py`) statt über `numpy.random`: numpy garantiert keine über Versionen
stabilen Zufallsströme, die CI installiert aber wöchentlich die neueste Version. Abstände sind ganzzahlig (Zehntel-Einheiten). Die Kosten (Transport, Sicherheitsbestand) sind Gleitkommazahlen aus reiner
Python-Arithmetik und `math.sqrt`; beides ist auf jeder Plattform bitgleich, also sind auch die Ergebnisse der Lokalsuche auf Windows und Linux dieselben.
"""

from dataclasses import dataclass
from math import isqrt

_MASK = (1 << 64) - 1
MAP_W = 100
FIXED_BASE = 175         # mittlere Fixkosten je Lager bei Fixkosten-Faktor 100 %
MU_MIN, MU_MAX = 5, 15   # mittlere Nachfrage je Kunde (Einheiten je Periode)


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def below(self, n):
        """Ganzzahl in 0..n-1 (die Modulo-Verzerrung bei n <= 101 liegt um 1e-17)."""
        return self.next() % n


def distance(a, b):
    """Euklidische Entfernung in Zehntel-Einheiten, ganzzahlig (abgerundet)."""
    return isqrt(100 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


@dataclass(frozen=True)
class Net:
    kind: str            # "map" (Zufallskarte); Tests bauen kleine Netze von Hand mit `_build("hand", ...)`
    site_names: tuple
    cust_names: tuple
    site_pos: tuple      # ((x, y), ...)
    cust_pos: tuple
    mu: tuple            # mittlere Nachfrage je Kunde (ganzzahlig)
    cv: int              # Variationskoeffizient der Nachfrage in Prozent (sigma_j = mu_j * cv / 100)
    f: tuple             # Fixkosten je Lager (ganzzahlig)
    d: tuple             # d[i][j]: Entfernung Lager i - Kunde j in Zehntel-Einheiten

    @property
    def m(self):
        return len(self.f)

    @property
    def n(self):
        return len(self.mu)

    @property
    def sigma(self):
        """Standardabweichung der Nachfrage je Kunde (reine Gleitkomma-Division, plattformgleich)."""
        return tuple(mu * self.cv / 100 for mu in self.mu)


def _names(prefix, count):
    return tuple(f"{prefix} {k + 1}" for k in range(count))


def _build(kind, sites, custs, mu, cv, f):
    d = tuple(tuple(distance(s, c) for c in custs) for s in sites)
    return Net(kind, _names("Lager", len(sites)), _names("Kunde", len(custs)), tuple(sites), tuple(custs), tuple(mu), cv, tuple(f), d)


def generate(n_sites, n_customers, cv, fixed_pct, seed):
    """Kandidaten und Kunden gleichverteilt auf einer Karte 0..99; Nachfrage 5..15; Fixkosten 60 bis 140 % von FIXED_BASE, skaliert mit `fixed_pct`.
    Die Zufallszüge hängen nicht von `cv` und `fixed_pct` ab: dieselbe Karte, andere Kosten."""
    rng = SplitMix64(seed)
    sites = tuple((rng.below(MAP_W), rng.below(MAP_W)) for _ in range(n_sites))
    custs = tuple((rng.below(MAP_W), rng.below(MAP_W)) for _ in range(n_customers))
    mu = tuple(MU_MIN + rng.below(MU_MAX - MU_MIN + 1) for _ in range(n_customers))
    base = tuple(60 + rng.below(81) for _ in range(n_sites))
    f = tuple(FIXED_BASE * b * fixed_pct // 10000 for b in base)
    return _build("map", sites, custs, mu, cv, f)
