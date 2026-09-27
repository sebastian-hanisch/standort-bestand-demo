"""Verfahren: Neuzuordnung der Kunden mit echten Kosten, Lokalsuche über die Lagerauswahl (Öffnen, Schließen, Tausch) und die naive Lösung (Standortproblem ohne Bestand) als Vergleich.

Die Kosten eines Lagers sind nicht mehr die Summe seiner Kundenkosten: der Sicherheitsbestand hängt von allen seinen Kunden zugleich ab (konkav). Ein Kunde, der zu einem Lager wechselt, verändert deshalb die Kosten
aller seiner Nachbarn. Zuordnung und Lagerwahl lassen sich nicht mehr getrennt lösen; die Lokalsuche behandelt beides zusammen.
"""

from dataclasses import dataclass

EPS = 1e-9


@dataclass(frozen=True)
class Solution:
    open: tuple          # geöffnete Lager (aufsteigend)
    assign: tuple        # Lager je Kunde
    costs: dict          # {"fixed", "transport", "stock", "total"}
    moves: tuple = ()    # Züge der Lokalsuche: (Art, Lager, Gesamtkosten danach)
    evals: int = 0       # bewertete Nachbarn

    @property
    def total(self):
        return self.costs["total"]


def used_sites(assign):
    return tuple(sorted(set(assign)))


def _sums(mod, members):
    return sum(mod.sig2[j] for j in members), sum(mod.sig[j] for j in members)


def descend(mod, allowed, assign):
    """Kundenzüge: ein Kunde wechselt in ein erlaubtes Lager, wenn die Gesamtkosten sinken (bester Zug je Kunde, Gleichstand: kleinster Lagerindex), bis kein Zug mehr hilft.
    Ein Lager ohne Kunden zahlt keine Fixkosten und zählt nicht als geöffnet; ein Wechsel in ein leeres erlaubtes Lager kostet dessen Fixkosten. Gibt (Zuordnung, Anzahl Zugbewertungen) zurück."""
    m, n = mod.m, mod.n
    allowed = sorted(allowed)
    assign = list(assign)
    members = {i: [] for i in range(m)}
    for j, i in enumerate(assign):
        members[i].append(j)
    s2 = [0.0] * m
    s1 = [0.0] * m
    cur = [0.0] * m                    # Bestandskosten je Lager (nur bei Änderung neu gerechnet)
    for i in range(m):
        s2[i], s1[i] = _sums(mod, members[i])
        cur[i] = mod.stock(s2[i], s1[i])
    evals = 0
    improved = True
    while improved:
        improved = False
        for j in range(n):
            a = assign[j]
            if len(members[a]) == 1:
                saving = mod.f[a] + cur[a] + mod.tc[a][j]
            else:
                saving = cur[a] - mod.stock(s2[a] - mod.sig2[j], s1[a] - mod.sig[j]) + mod.tc[a][j]
            best_delta, best_b = -EPS, a
            for b in allowed:
                if b == a:
                    continue
                evals += 1
                if members[b]:
                    add = mod.stock(s2[b] + mod.sig2[j], s1[b] + mod.sig[j]) - cur[b]
                else:
                    add = mod.f[b] + mod.stock(mod.sig2[j], mod.sig[j])
                delta = add + mod.tc[b][j] - saving
                if delta < best_delta:
                    best_delta, best_b = delta, b
            if best_b != a:
                members[a].remove(j)
                members[best_b].append(j)
                members[best_b].sort()
                assign[j] = best_b
                s2[a], s1[a] = _sums(mod, members[a])
                s2[best_b], s1[best_b] = _sums(mod, members[best_b])
                cur[a] = mod.stock(s2[a], s1[a])
                cur[best_b] = mod.stock(s2[best_b], s1[best_b])
                improved = True
    return assign, evals


def solve_for(mod, allowed):
    """Beste Zuordnung zu einer erlaubten Lagermenge (Start: nächstes Lager, dann Kundenzüge); die geöffneten Lager sind die genutzten."""
    assign, evals = descend(mod, allowed, mod.nearest(allowed))
    op = used_sites(assign)
    return Solution(op, tuple(assign), mod.evaluate(op, assign), (), evals)


def reassign_only(mod, open_set):
    """Naive Lagerwahl, aber bestandsbewusste Zuordnung (Zwischenstufe: wie viel der Lücke steckt in der Zuordnung, wie viel in der Lagerwahl?)."""
    return solve_for(mod, open_set)


def naive(mod, open_set):
    """Die Lösung des Standortproblems ohne Bestand (`open_set`) mit dem Kunden zum nächsten Lager, bewertet mit den echten Kosten."""
    assign = mod.nearest(open_set)
    op = used_sites(assign)
    return Solution(op, tuple(assign), mod.evaluate(op, assign))


def local_search(mod, start_open):
    """Lokalsuche über die Lagermenge: Öffnen oder Schließen eines Lagers, dann Tausch eines geöffneten gegen ein geschlossenes; jede Kandidatenmenge bekommt ihre beste Zuordnung (`solve_for`).
    Erste Verbesserung in fester Reihenfolge (Lagerindex), bis kein Nachbar besser ist. Gleichstände werden nie getauscht (nur echte Verbesserung um mehr als 1e-9)."""
    cur = solve_for(mod, start_open)
    evals = cur.evals
    moves = []
    op = set(cur.open)
    improved = True
    while improved:
        improved = False
        for i in range(mod.m):
            cand = op ^ {i}
            if not cand:
                continue
            sol = solve_for(mod, cand)
            evals += sol.evals
            if sol.total < cur.total - EPS:
                moves.append(("Schließen" if i in op else "Öffnen", i, sol.total))
                cur, op, improved = sol, set(sol.open), True
        if improved:
            continue
        for a in sorted(op):
            for b in range(mod.m):
                if b in op:
                    continue
                sol = solve_for(mod, (op - {a}) | {b})
                evals += sol.evals
                if sol.total < cur.total - EPS:
                    moves.append(("Tausch", (a, b), sol.total))
                    cur, op, improved = sol, set(sol.open), True
                    break
            if improved:
                break
    return Solution(cur.open, cur.assign, cur.costs, tuple(moves), evals)


SINGLE_STARTS = 3       # so viele beste Ein-Lager-Lösungen dienen zusätzlich als Startpunkt


def joint(mod, naive_open, singles=SINGLE_STARTS):
    """Gemeinsame Optimierung: Lokalsuche aus der naiven Lösung, aus 'alle Lager offen' und aus den besten Ein-Lager-Lösungen; die beste zählt (Gleichstand: der frühere Start).
    Die letzten Starts sind nötig: aus der naiven Lösung und aus 'alle offen' bleibt die Suche oft in einer Lagermenge stehen, die von einer viel kleineren Lösung übertroffen wird (Tausch und Schließen gleichzeitig
    führen nicht über Einzelzüge). `singles=0` lässt die Ein-Lager-Starts weg (nur naive Lösung und alle offen). Gibt (Lösung, Startname) zurück; `evals` der Lösung zählt die bewerteten Nachbarn aller Starts."""
    best_singles = sorted(range(mod.m), key=lambda i: (solve_for(mod, [i]).total, i))[:singles] if singles else []
    starts = [("naiv", naive_open), ("alle", range(mod.m))] + [("einzeln", [i]) for i in best_singles]
    best, name, evals = None, None, 0
    for label, start in starts:
        sol = local_search(mod, start)
        evals += sol.evals
        if best is None or sol.total < best.total - EPS:
            best, name = sol, label
    return Solution(best.open, best.assign, best.costs, best.moves, evals), name
