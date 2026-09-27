# Standort + Bestand – warum wenige große Lager billiger sind, als die Standortplanung denkt – Streamlit-Demo

Viertes Stück der **Standortplanungs-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von [standortplanung-demo](https://github.com/sebastian-hanisch/standortplanung-demo) (Standortproblem ohne Kapazität):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Modell – **Standortplanung mit Bestandskosten (Location-Inventory, Risk Pooling)** – an einem wachsenden Beispiel.
Die klassische Standortplanung wählt Lager nach **Fixkosten plus Transport**. Jedes Lager hält aber auch **Sicherheitsbestand** gegen schwankende Nachfrage, und der wächst nicht mit der Zahl der Kunden, sondern nur mit ihrer **Wurzel**: ein großes Lager braucht weniger Bestand als viele kleine, die zusammen dasselbe bedienen.
Wer die Lager ohne Bestand plant und den Bestand nachträglich einrechnet, öffnet zu viele. Die Demo misst, **wie viel** das kostet, was die **gemeinsame Planung** (Lokalsuche über die Lagerwahl, für kleine Netze gegen das exakte Optimum geprüft) daran ändert – und wann der Effekt **verschwindet**: bei **korrelierter Nachfrage** hilft Bündeln nicht, bei kleinen Bestandskosten ist er unwichtig.

**Einordnung in die Reihe (die Kanten des Graphen):** Kind von `standortplanung-demo` (dasselbe Standortgerüst, dazu ein konkaver Bestandsterm je Lager); Nachbar der [kapazitierten Standortplanung](https://github.com/sebastian-hanisch/kapazitierte-standortplanung-demo) (Kapazität statt Bestandsrisiko) und von [p-center-demo](https://github.com/sebastian-hanisch/p-center-demo) (andere Zielfunktion).
Zu den Bestands-Demos des Portfolios: [forecast-inventory-demo](https://github.com/sebastian-hanisch/forecast-inventory-demo) schließt Risk Pooling ausdrücklich aus (ein Artikel je Lager) – dieses Stück ist die Standortsicht darauf; `bullwhip-demo` rechnet die Lieferkette, `inventory-routing-demo` die Fahrkosten.
```
standortplanung-demo (UFL, Wurzel: Fixkosten + Transport)                               [gebaut]
  ├─ kapazitierte-standortplanung-demo (Kapazität + Single-Sourcing, Lagrange)           [gebaut]
  ├─ p-center-demo (Maximum statt Summe: Farthest-first, exakt per Überdeckung)          [gebaut]
  ├─ standort-bestand-demo (Bestandskosten je Lager, Risk Pooling)                       [dieses Stück]
  ├─ p-Hub-Median                                                                        [geplant]
  └─ Wettbewerbsstandort                                                                 [geplant]
```

## Modell

Ein Lager, das die Kunden $S$ bedient, kostet: Fixkosten + Transport (Nachfrage mal Entfernung mal Satz) + Bestandskosten `hz · sqrt((1 − ρ) · Σσ² + ρ · (Σσ)²)` (Standardabweichung der Lagernachfrage, Gleichkorrelation ρ, Gewicht `hz` = Sicherheitsfaktor mal Haltekosten).
Bei ρ = 0 gleichen sich die Schwankungen der Kunden aus (Wurzel: Risk Pooling), bei ρ = 1 ist der Bestand die Summe der Einzelbestände und hängt nicht mehr von der Zuordnung ab. Verglichen werden vier Lösungen: **naiv** (das Standortproblem ohne Bestand exakt gelöst, mit den echten Kosten bewertet), **naiv mit Neuzuordnung** (dieselben Lager, die Kunden mit den echten Kosten neu verteilt), **gemeinsam** (Lokalsuche über die Lagermenge mit fünf Starts) und – für Kleinnetze – das **exakte Optimum** (Mengenpartitionierung).

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` belegt: Standardnetz und Beispielnetze über ihre Seeds, Verteilungen über 40 feste Netze (Seeds ab 100000), die Wärmekarte über 10 feste Netze, Kleinnetze gegen das exakte Optimum. Standard: 12 Kandidaten-Lager, 30 Kunden (mittlere Nachfrage 5 bis 15), Schwankung 50 %, Bestandsgewicht 40, Korrelation 0, Transportsatz 0,50, Seed 4.
Abstände sind ganzzahlig (Zehntel-Einheiten), Kosten Gleitkommazahlen aus reiner Python-Arithmetik; Zufallsstrom und Lokalsuche sind auf allen Plattformen dieselben. Nur der exakte Wert kommt aus einem Löser (Vergleich mit Toleranz); nie gezählt wird, welche von mehreren gleich guten Lagermengen er liefert.

**Standardnetz.** Die naive Planung öffnet **6** Lager und kostet **6 358**, die gemeinsame öffnet **3** und kostet **6 060**: die naive ist **4,92 %** teurer. Weniger Lager sparen Fixkosten (1 055 → 489) und Bestand (2 769 → 1 970) und kosten Transport (2 534 → 3 602).
**Über das Bestandsgewicht** (gleiches Netz): bei 0 / 10 / 20 / 30 / 40 / 50 / 60 / 100 öffnet die gemeinsame Planung 6 / 6 / 5 / 4 / 3 / 3 / 2 / 2 Lager, die Mehrkosten der naiven Planung (sie öffnet immer 6) sind 0 / 0 / 0,98 / 2,37 / 4,92 / 7,60 / 10,20 / **21,06 %**.

**Über 40 Netze** (Standard): die naive Planung öffnet im Mittel 5,35 Lager, die gemeinsame 3,45; Mehrkosten im Mittel **4,60 %** (Median 4,49 %, schlechtestes Netz 11,3 %), in 36 von 40 Netzen über 0,5 %. Je Bestandsgewicht 5 / 20 / 40 / 60 / 100: Mittel **0,10 / 1,47 / 4,60 / 8,41 / 16,60 %**, schlechtestes Netz 1,19 / 6,54 / 11,3 / 19,4 / 32,2 %; Lager der gemeinsamen Planung 5,03 / 4,23 / 3,45 / 2,90 / 1,90.

**Wo der Effekt verschwindet: Korrelation.** Bestandsgewicht 100, Korrelation 0 / 20 / 40 / 60 / 80 / 100 %: Mehrkosten im Mittel **16,60 / 4,02 / 1,45 / 0,48 / 0,10 / 0,00 %** (schlechtestes Netz 32,2 / 9,7 / 4,6 / 2,3 / 0,8 / 0,0 %), Lager der gemeinsamen Planung 1,90 / 3,10 / 3,75 / 4,23 / 4,80 / 5,35. Bei 100 % Korrelation und bei Bestandsgewicht 0 kosten naive und gemeinsame Planung in **jedem** der 40 Netze dasselbe.
Die Wärmekarte (10 feste Netze) zeigt beide Achsen: bei Korrelation 0 Mehrkosten 0,04 / 0,69 / 2,52 / 5,54 / 14,13 % für Bestandsgewicht 5 / 20 / 40 / 60 / 100, bei Korrelation 100 % überall 0.

**Was sonst den Effekt bewegt** (40 Netze, je ein Regler geändert, Standard 4,60 %): **Schwankung** 20 / 100 % → 1,00 / **12,34 %**; **Transportsatz** 0,20 / 1,00 → **10,86** / 2,52 % (billiger Transport nimmt dem Bündeln sein Gegengewicht); **Fixkosten** 50 / 200 % → 6,76 / 3,22 %; **Kandidaten** 8 / 20 → 3,93 / 5,66 %; **Kundenzahl** 15 / 60 → 4,86 / 4,60 % (praktisch unverändert).

**Die Neuzuordnung allein reicht nicht.** Die naive Lagermenge mit den echten Kosten neu zugeordnet (Kunden ziehen einzeln um) schließt im Mittel nur **15 %** der Mehrkosten (noch 3,89 % über der gemeinsamen Lösung); im Standardnetz kostet sie 6 348 statt 6 358. Bei starker Schwankung (100 %) sind es 39 %, bei Fixkosten 50 % 36 %, bei Schwankung 20 % nur 4 %. Erst die andere **Lagerwahl** holt den Rest.

**Die Lokalsuche und das exakte Optimum.** Kleinnetze (5 Lager, 8 Kunden, je 40 feste Netze; Bestandsgewicht 40 / 100 / 100, Korrelation 0 / 0 / 20 %): die Lokalsuche mit fünf Starts trifft das exakte Optimum (Mengenpartitionierung, HiGHS) in 39 / 40 / 40 Netzen, in **119 von 120**, im schlechtesten 0,04 % darüber.
Mit nur **zwei Starts** (naive Lösung und „alle Lager offen“) sind es 39 / 40 / 39 mit bis zu **2,06 %** darüber. Im Beispiel *Ein Start reicht nicht* (5 Lager, 8 Kunden, Bestandsgewicht 100, Korrelation 20 %, Seed 200025) öffnet das Optimum **1** Lager (4 459,5); zwei Starts enden bei 4 672 (2 Lager, 4,76 % darüber), die naive Planung 9,75 % darüber: der Sprung auf ein einzelnes anderes Lager ist mit Öffnen, Schließen und Tauschen nicht zu erreichen.
Auch im Standardnetz wirkt das: bei Bestandsgewicht 50 bleiben zwei Starts bei 6 858 (4 Lager), mit den Ein-Lager-Starts endet die Suche bei 6 553 (3 Lager). Über 40 Standardnetze liegen zwei Starts im Mittel 0,12 % (Bestandsgewicht 40), 0,19 % (100) bzw. 0,05 % (100, Korrelation 20 %) über fünf Starts, in 4 / 5 / 3 Netzen schlechter (bis 3,0 / 3,5 / 1,6 %).

**Voreinstellungen.** *Wenige große Lager* (Bestandsgewicht 100): naiv 6 Lager (10 512, davon 6 923 Bestand), gemeinsam 2 (8 683), 21,06 %. *Korrelierte Nachfrage* (Bestandsgewicht 100, Korrelation 80 %): beide 6 Lager, Unterschied 0,002 %. *Bestand kaum relevant* (Bestandsgewicht 5): Bestand 346 von 3 935, beide Planungen identisch.
*Stark schwankende Nachfrage* (100 %): 6 → 2 Lager, 16,19 %. *Billiger Transport* (0,20): 4 → 1 Lager, 15,50 %. *Kleinnetz mit exaktem Optimum* (6 Lager, 10 Kunden, Seed 2): das Optimum 2 808,8 mit 2 Lagern, die Lokalsuche trifft es, die naive Planung ist 7,24 % darüber.

## Was nicht funktioniert hat / Vorab-Hypothesen

Vor dem Bau standen mehrere Vermutungen im Plan (Modellprüfung der Erweiterung E3). Gemessen:

- **„Wer die Standortplanung ohne Bestand macht, liegt ungefähr richtig“ – nur bei kleinem Bestand.** Bestandsgewicht 5: 0,10 %; Standard 4,60 %; Bestandsgewicht 100: 16,60 % im Mittel, 32,2 % im schlechtesten Netz. Ob die Vereinfachung trägt, entscheidet das Gewicht des Bestands gegen Fixkosten und Transport.
- **„Risk Pooling gilt immer“ – widerlegt.** Bei Korrelation 100 % (und bei 80 % nur noch 0,10 %) verschwindet der Vorteil des Bündelns: der Bestand ist dann die Summe der Einzelbestände, unabhängig von der Zuordnung.
- **„Es genügt, die Kunden bestandsbewusst neu zuzuordnen“ – widerlegt.** Das schließt im Mittel 15 % der Mehrkosten; die Lagerwahl selbst muss neu entschieden werden.
- **„Mehr Kunden bedeuten mehr Pooling-Vorteil“ – widerlegt.** 15 / 30 / 60 Kunden: 4,86 / 4,60 / 4,60 %: die Kundenzahl ändert die relative Mehrbelastung kaum; entscheidend sind Schwankung, Transportsatz, Fixkosten und Bestandsgewicht.
- **„Die naheliegende Lokalsuche findet das Optimum“ – nur mit mehr als den zwei naheliegenden Starts.** Aus der naiven Lösung und aus „alle offen“ bleibt sie in einer Lagermenge stehen, die eine kleinere, aber weit entfernte Lösung übertrifft (bis 2,06 % in Kleinnetzen, bis 3,5 % in Netzen der Standardgröße); mit den drei besten Ein-Lager-Starts trifft sie das Optimum in 119 von 120 Kleinnetzen.
- **Nicht gebaut/nicht gemessen:** Zyklusbestand (∝ √Σμ, wirkt vermutlich in dieselbe Richtung), Servicegrad-Definition, Lieferzeiteffekt, Mehr-Artikel-Sortimente – siehe Grenzen.
- **Bestätigt:** die Wurzel-Konkavität macht wenige große Lager billiger, als die Standortplanung ohne Bestand annimmt; der Effekt wächst mit Bestandsgewicht, Schwankung und billigem Transport und schwindet mit Korrelation und Fixkosten.

## Grenzen (was die Demo nicht zeigt)

Gleichkorrelation (alle Kundenpaare gleich), nur Sicherheitsbestand (Zyklusbestand, Servicegrad-Definition und Lieferzeit stecken im einen Gewicht bzw. fehlen), ein Artikel und eine Periode, keine Kapazitäten, Luftlinie mit auf Zehntel abgerundeten Abständen, erzeugte Netze mit erfundenen Kosten – die Aussagen gelten für diese Modellwelt, nicht für ein bestimmtes Unternehmen.
Die Lokalsuche ist eine Heuristik; nur für Kleinnetze (bis 10 Kunden und 6 Lager) prüft die Demo sie gegen das exakte Optimum. Die Einheit „bewertete Nachbarn“ ist eine Zählung, keine Uhr.

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Naiv gegen gemeinsam, Selbst probieren, Reihen über Bestandsgewicht und Korrelation, Verteilung über 40 Netze, Wärmekarte, Exakt-Vergleich |
| `lip_scenario.py` | Netze (Zufallskarte), SplitMix64-Zufallsstrom (Kopie aus den Vorgängern) |
| `lip_costs.py` | Kostenmodell: Fixkosten, Transport, Bestand (konkav), Zuordnung zum nächsten Lager |
| `lip_heuristics.py` | Kundenzüge (Neuzuordnung), Lokalsuche über die Lagermenge, gemeinsame Optimierung mit fünf Starts |
| `lip_exact.py` | HiGHS: Standortproblem ohne Bestand (MILP), Mengenpartitionierung mit Bestand, Brute Force |
| `lip_evaluation.py`, `lip_visualization.py` | Analyse, Reihen, Verteilungen, Wärmekarte, Exakt-Vergleich; Karte, Kostenbalken, Reihen |
| `lip_presets.py`, `lip_constants.py` | Presets, Permalink, Regler-Grenzen, feste Seeds |
| `tests/` | 163 Tests: Szenario, Kostenformel von Hand, Kundenzüge und Lokalsuche (keine Verbesserung nach dem Ende), Exakt gegen Brute Force, Presets, Zahlen (`test_claims.py`), App |

Lokal starten: `pip install -r requirements.txt`, dann `streamlit run app.py`; Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests`.
