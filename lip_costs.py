"""Kostenmodell: Fixkosten + Transport + Sicherheitsbestand je geöffnetem Lager.

Ein Lager, das die Kundenmenge S bedient, hält einen Sicherheitsbestand, der der Standardabweichung seiner Gesamtnachfrage folgt:
    Bestandskosten(S) = hz * sqrt((1 - rho) * sum(sigma_j^2) + rho * (sum sigma_j)^2)
(Gleichkorrelation rho zwischen den Kunden). Bei rho = 0 wächst der Bestand nur mit der Wurzel der Kundenzahl (Risk Pooling: ein großes Lager braucht weniger Bestand als viele kleine),
bei rho = 1 wächst er linear (Summe der Einzelbestände: kein Vorteil durch Bündeln). Transport: Nachfrage * Entfernung * Satz. Alle Größen sind Gleitkommazahlen aus reiner Python-Arithmetik.
"""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class Econ:
    t: int = 50          # Transportsatz in Hundertstel je Nachfrageeinheit und Karteneinheit (50 = 0,50)
    hz: int = 60         # Bestandsgewicht: Kosten je Einheit Standardabweichung der Lagernachfrage (Sicherheitsfaktor mal Haltekosten)
    rho: int = 0         # Korrelation der Kundennachfragen in Prozent


class Model:
    """Kosten eines Netzes bei gegebenem `Econ`: Transportkostenmatrix, Sortierung der Lager je Kunde nach Entfernung, Kosten eines Lagers aus seinen Summen."""

    def __init__(self, net, econ):
        self.net, self.econ = net, econ
        self.m, self.n = net.m, net.n
        self.hz = float(econ.hz)
        self.rho = econ.rho / 100
        sig = net.sigma
        self.sig = sig
        self.sig2 = tuple(s * s for s in sig)
        self.f = tuple(float(x) for x in net.f)
        # Transport von Lager i zu Kunde j; ganzzahlige Zehntel-Entfernung, daher bis auf die Division durch 1000 exakt
        self.tc = tuple(tuple(net.mu[j] * net.d[i][j] * econ.t / 1000 for j in range(self.n)) for i in range(self.m))
        # Lager je Kunde aufsteigend nach Entfernung, Gleichstand: kleinster Index
        self.near = tuple(tuple(sorted(range(self.m), key=lambda i, j=j: (net.d[i][j], i))) for j in range(self.n))

    def stock(self, s2, s1):
        """Bestandskosten eines Lagers, dessen Kunden die Summe der Varianzen `s2` und die Summe der Standardabweichungen `s1` haben."""
        return self.hz * sqrt(max(0.0, (1 - self.rho) * s2 + self.rho * s1 * s1))

    def nearest(self, allowed):
        """Zuordnung jedes Kunden zum nächsten erlaubten Lager (`allowed`: Menge oder Liste von Lagerindizes)."""
        ok = [False] * self.m
        for i in allowed:
            ok[i] = True
        return [next(i for i in self.near[j] if ok[i]) for j in range(self.n)]

    def evaluate(self, open_set, assign):
        """Kostenaufteilung: Fixkosten der geöffneten Lager (auch leerer), Transport, Bestand; `assign[j]` muss ein geöffnetes Lager sein."""
        s2 = {i: 0.0 for i in open_set}
        s1 = {i: 0.0 for i in open_set}
        transport = 0.0
        for j, i in enumerate(assign):
            s2[i] += self.sig2[j]
            s1[i] += self.sig[j]
            transport += self.tc[i][j]
        fixed = sum(self.f[i] for i in open_set)
        stock = sum(self.stock(s2[i], s1[i]) for i in open_set)
        return {"fixed": fixed, "transport": transport, "stock": stock, "total": fixed + transport + stock}

    def load(self, open_set, assign):
        """Bediente Nachfrage und Standardabweichung der Lagernachfrage je Lager (für Anzeige und Tests)."""
        out = {}
        for i in open_set:
            members = [j for j, a in enumerate(assign) if a == i]
            s2 = sum(self.sig2[j] for j in members)
            s1 = sum(self.sig[j] for j in members)
            out[i] = {"customers": len(members), "mu": sum(self.net.mu[j] for j in members), "sd": sqrt((1 - self.rho) * s2 + self.rho * s1 * s1)}
        return out
