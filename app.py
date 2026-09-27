"""Standort + Bestand - warum wenige große Lager billiger sind, als die Standortplanung denkt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Modell - Standortplanung mit Sicherheitsbestand je Lager (Risk Pooling) - und lässt stattdessen das Beispiel wachsen.
Neues Stück der Standortplanungs-Linie der "Konzepte"-Reihe, Kind des Standortproblems ohne Kapazität (Wurzel): dieselbe Standortwahl, aber jedes Lager hält Sicherheitsbestand, der nur mit der Wurzel wächst.
Siehe README für die Einordnung.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import lip_constants as C
import lip_evaluation as ev
from lip_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from lip_visualization import build_costs, build_dist, build_heat, build_map, build_series

st.set_page_config(page_title="Standort + Bestand – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return "–" if x is None else f"{int(round(x)):,}".replace(",", " ")


def _pct(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f} %".replace(".", ",")


@st.cache_resource(show_spinner=False, max_entries=32)
def _analysis(p):
    return ev.analyse(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _hz_series(p):
    return ev.hz_series(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _rho_series(p):
    return ev.rho_series(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _dist(p):
    return ev.distribution(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _heat(p):
    return ev.heatmap(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _exact(p):
    return ev.exact_compare(p)


st.title("🏭 Standort + Bestand – warum wenige große Lager billiger sind, als die Standortplanung denkt")
st.markdown(
    """
Die klassische **Standortplanung** wählt Lager nach **Fixkosten plus Transport**. Jedes Lager hält aber auch **Sicherheitsbestand** gegen schwankende Nachfrage – und der wächst nicht mit der Zahl der Kunden, sondern nur mit ihrer **Wurzel**:
ein großes Lager braucht weniger Bestand als viele kleine, die zusammen dasselbe bedienen (**Risk Pooling**). Wer die Lager ohne Bestand plant und den Bestand später „nachrechnet“, öffnet zu viele. Die Demo zeigt, **wie viel** das kostet,
was die **gemeinsame Planung** daran ändert – und wann der Effekt **verschwindet**: bei **korrelierter Nachfrage** hilft Bündeln nicht, bei kleinen Bestandskosten ist er unwichtig.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - ein Stück der Standortplanungs-Linie der \"Konzepte\"-Reihe - **ein** Modell an einem wachsenden Beispiel. "
    "Verwandt: das Standortproblem ohne Kapazität (Wurzel, ohne Bestand), die Bestands-Demos des Portfolios (ein Artikel je Lager, Lieferkette, Inventory Routing) - dort steht der Bestand allein, hier entscheidet er die Standortwahl mit."
)

with st.expander("So funktioniert das Modell", expanded=True):
    st.markdown(
        r"""
1. **Kosten eines Lagers** $i$, das die Kunden $S$ bedient: Fixkosten $f_i$ + Transport (Nachfrage mal Entfernung mal Satz) + **Bestandskosten** $hz\cdot\sqrt{(1-\rho)\sum_{j\in S}\sigma_j^2+\rho\big(\sum_{j\in S}\sigma_j\big)^2}$ – die Standardabweichung der Lagernachfrage, mal ein Gewicht $hz$ (Sicherheitsfaktor mal Haltekosten).
2. **Korrelation $\rho$:** bei $\rho=0$ gleichen sich Schwankungen der Kunden aus, der Bestand wächst mit der Wurzel; bei $\rho=1$ schwanken alle gleichzeitig, der Bestand ist die Summe der Einzelbestände – **kein Vorteil durch Bündeln**.
3. **Naiv:** das Standortproblem ohne Bestand exakt lösen (kleines MILP), dann mit den echten Kosten bewerten. **Neuzuordnung:** dieselben Lager, aber die Kunden werden mit den echten Kosten neu zugeordnet.
4. **Gemeinsam:** Lokalsuche über die Lagerwahl (öffnen, schließen, tauschen); jede Lagermenge bekommt ihre beste Zuordnung, gestartet wird fünfmal (naive Lösung, alle Lager offen, die drei besten Ein-Lager-Lösungen). Für kleine Netze rechnet ein exaktes Verfahren (Mengenpartitionierung) das Optimum nach.
        """
    )

st.caption("🎯 Schnellstart – ein Beispiel laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    sites = st.slider("Kandidaten-Lager", *bounds("sites_slider"), key="sites_slider", help="Wie viele mögliche Lagerstandorte es gibt (zufällig auf der Karte verteilt).")
    customers = st.slider("Kunden", *bounds("cust_slider"), key="cust_slider", help="Wie viele Kunden beliefert werden; jeder hat eine mittlere Nachfrage von 5 bis 15.")
    cv = st.slider("Schwankung der Nachfrage (in %)", *bounds("cv_slider"), step=10, key="cv_slider", help="Variationskoeffizient: Standardabweichung der Nachfrage eines Kunden in Prozent seiner mittleren Nachfrage.")
    hz = st.slider("Bestandsgewicht", *bounds("hz_slider"), step=5, key="hz_slider", help="Kosten je Einheit Standardabweichung der Lagernachfrage (Sicherheitsfaktor mal Haltekosten). Bei 0 gibt es keine Bestandskosten.")
    rho = st.slider("Korrelation der Kunden (in %)", *bounds("rho_slider"), step=5, key="rho_slider", help="Wie gleichgerichtet die Nachfragen der Kunden schwanken. Bei 0 gleichen sich Schwankungen aus (Risk Pooling), bei 100 nicht.")
    t = st.slider("Transportsatz", *bounds("t_slider"), step=10, key="t_slider", help="Hundertstel je Nachfrageeinheit und Karteneinheit (50 = 0,50). Teurer Transport hält die Lager nah an den Kunden.")
    fixed = st.slider("Fixkosten-Faktor (in %)", *bounds("fixed_slider"), step=10, key="fixed_slider", help="Skaliert die Fixkosten aller Lager (60 bis 140 % von 175 im Mittel, je Lager verschieden).")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Netz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilungen über feste Netze weiter unten ändern sich dabei nicht.")

sync_query_params({"sites_slider": int(sites), "cust_slider": int(customers), "cv_slider": int(cv), "hz_slider": int(hz), "rho_slider": int(rho), "t_slider": int(t), "fixed_slider": int(fixed), "seed_input": int(seed)})

params = ev.Params(int(sites), int(customers), int(cv), int(fixed), int(t), int(hz), int(rho), int(seed))
with st.spinner("Rechne..."):
    a = _analysis(params)
net, mod, naive, reassign, joint = a["net"], a["mod"], a["naive"], a["reassign"], a["joint"]

# --- Naiv gegen gemeinsam ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🏭 Naiv geplant gegen gemeinsam geplant")
st.markdown(
    f"Das Netz hat **{net.n} Kunden** und **{net.m} Kandidaten-Lager**. Das Standortproblem ohne Bestand öffnet **{len(naive.open)}** Lager; mit den echten Kosten (Bestand eingerechnet) kostet diese Planung **{_int(naive.total)}**. "
    f"Die gemeinsame Planung öffnet **{len(joint.open)}** Lager und kostet **{_int(joint.total)}** – die naive Planung ist um **{_pct(a['gap'])}** teurer."
)
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Naiv** (ohne Bestand geplant): {len(naive.open)} Lager")
    st.plotly_chart(build_map(net, mod, naive, color="#ff7f0e"), width="stretch", key="map_naive")
with c2:
    st.markdown(f"**Gemeinsam** (Standort und Bestand): {len(joint.open)} Lager")
    st.plotly_chart(build_map(net, mod, joint), width="stretch", key="map_joint")
st.caption("Quadrate: geöffnete Lager (Größe nach bedienter Nachfrage, Nummer = Lagernummer); Punkte: Kunden (Größe nach Nachfrage); graue Quadrate: nicht geöffnete Kandidaten.")

cost_rows = [("Naiv", naive.costs), ("Naiv, Kunden neu zugeordnet", reassign.costs), ("Gemeinsam", joint.costs)]
st.plotly_chart(build_costs(cost_rows), width="stretch", key="cost_bars")
st.table({"Lösung": ["Naiv (ohne Bestand geplant)", "Naiv, Kunden mit echten Kosten neu zugeordnet", "Gemeinsam optimiert (Lokalsuche)"],
          "Lager": [str(len(s.open)) for s in (naive, reassign, joint)],
          "Fixkosten": [_int(s.costs["fixed"]) for s in (naive, reassign, joint)],
          "Transport": [_int(s.costs["transport"]) for s in (naive, reassign, joint)],
          "Bestand": [_int(s.costs["stock"]) for s in (naive, reassign, joint)],
          "Gesamtkosten": [_int(s.total) for s in (naive, reassign, joint)],
          "Mehrkosten gegenüber gemeinsam": [_pct(ev.gap_pct(s.total, joint.total), 2) for s in (naive, reassign, joint)]})
st.caption(f"Die gemeinsame Lokalsuche startet fünfmal (aus der naiven Lösung, aus 'alle Lager offen' und aus den drei besten Ein-Lager-Lösungen) und nimmt die beste: {_int(joint.evals)} bewertete Nachbarn insgesamt; den besten Endpunkt lieferte der Start '{a['start']}' mit {len(joint.moves)} Zügen.")
st.caption("Weniger Lager sparen Fixkosten und Bestand, kosten aber Transport: die gemeinsame Lösung verschiebt Kosten von Fixkosten und Bestand in den Transport. Die reine Neuzuordnung der Kunden holt davon nur einen kleinen Teil – die Lagerwahl muss sich ändern.")

st.markdown("---")

# --- Selbst probieren ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🏭 Selbst probieren: welche Lager öffnen?")
if st.session_state.get("lip_pick_owner") != params:
    st.session_state["pick_multi"] = list(naive.open)
    st.session_state["lip_pick_owner"] = params
chosen = st.multiselect("Geöffnete Lager", list(range(net.m)), key="pick_multi", format_func=lambda i: net.site_names[i],
                        help="Voreingestellt ist die Lagermenge der naiven Lösung. Jeder Kunde wird bestmöglich (mit den echten Kosten) einem der gewählten Lager zugeordnet, deshalb entspricht die Voreinstellung der Zeile 'Naiv, Kunden neu zugeordnet'; ein gewähltes Lager ohne Kunden wird nicht bezahlt.")
cl, cr = st.columns([3, 2])
if chosen:
    trial = ev.try_open(mod, chosen)
    with cl:
        st.plotly_chart(build_map(net, mod, trial, height=420, color="#1f77b4"), width="stretch", key="pick_map")
    with cr:
        m1, m2 = st.columns(2)
        m1.metric("Gesamtkosten", _int(trial.total), delta=_pct(ev.gap_pct(trial.total, joint.total), 2) + " gegenüber gemeinsam" if trial.total > joint.total + 1e-9 else "so gut wie die Lokalsuche",
                  delta_color="inverse" if trial.total > joint.total + 1e-9 else "off")
        m2.metric("Geöffnet", f"{len(trial.open)} Lager")
        m3, m4, m5 = st.columns(3)
        m3.metric("Fixkosten", _int(trial.costs["fixed"]))
        m4.metric("Transport", _int(trial.costs["transport"]))
        m5.metric("Bestand", _int(trial.costs["stock"]))
        if trial.total < joint.total - 1e-9:
            st.success("🎉 Besser als die Lokalsuche – die Heuristik war hier nicht optimal.")
else:
    with cl:
        st.info("Wählen Sie mindestens ein Lager.")

st.markdown("---")

# --- Wovon hängt es ab? ---------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wovon hängt es ab?")
st.caption("Für das eingestellte Netz: die Lager und die Mehrkosten der naiven Lösung, wenn nur das Bestandsgewicht (oder nur die Korrelation) variiert.")
b1, b2 = st.columns(2)
with b1:
    if st.button("Reihe über das Bestandsgewicht", key="hz_start", width="stretch"):
        st.session_state["hz_on"] = True
with b2:
    if st.button("Reihe über die Korrelation", key="rho_start", width="stretch"):
        st.session_state["rho_on"] = True
if st.session_state.get("hz_on"):
    with st.spinner("Rechne 11 Bestandsgewichte..."):
        rows = _hz_series(params)
    st.markdown("**Über das Bestandsgewicht** (Korrelation wie eingestellt)")
    st.plotly_chart(build_series(rows, "Bestandsgewicht"), width="stretch", key="hz_chart")
if st.session_state.get("rho_on"):
    with st.spinner("Rechne 11 Korrelationen..."):
        rows = _rho_series(params)
    st.markdown("**Über die Korrelation** (Bestandsgewicht wie eingestellt)")
    st.plotly_chart(build_series(rows, "Korrelation (in %)"), width="stretch", key="rho_chart")

st.subheader("🔬 Gilt das in jedem Netz?")
st.caption("40 feste Netze mit den eingestellten Reglern (nur die Karte ist eine andere): Mehrkosten der naiven Lösung gegenüber der gemeinsam optimierten.")
if st.button("40 Netze durchrechnen (dauert einige Sekunden)", key="dist_start"):
    st.session_state["dist_on"] = True
if st.session_state.get("dist_on"):
    with st.spinner("Rechne 40 Netze..."):
        dist = _dist(params)
    s = dist["summary"]
    st.plotly_chart(build_dist(dist["gaps"]), width="stretch", key="dist_chart")
    st.table({"Größe": ["Mehrkosten der naiven Lösung, Mittel", "Median", "schlechtestes Netz", "Netze mit mehr als 0,5 % Mehrkosten", "Lager naiv / gemeinsam (Mittel)", "Mehrkosten nach bloßer Neuzuordnung (Mittel)"],
              "Wert": [_pct(s["gap_mean"], 2), _pct(s["gap_median"], 2), _pct(s["gap_max"], 1), f"{s['over_half']} von {s['count']}", f"{_f(s['naive_sites'], 2)} / {_f(s['joint_sites'], 2)}", _pct(s["gap_reassign_mean"], 2)]})
    if s["reassign_closed"] is not None:
        st.caption(f"Die bloße Neuzuordnung der Kunden schließt im Mittel nur {_pct(100 * s['reassign_closed'], 0)} der Mehrkosten – den Rest holt erst die andere Lagerwahl. Der Start aus der naiven Lösung lieferte in {s['start_naive']} von {s['count']} Netzen den besten Endpunkt; in den übrigen war ein anderer Start (alle Lager offen oder eine kleine Lösung) besser.")

st.subheader("🔬 Bestandsgewicht gegen Korrelation")
st.caption("Mittlere Mehrkosten der naiven Lösung über 10 feste Netze für fünf Bestandsgewichte und vier Korrelationen (Transport, Fixkosten und Schwankung wie eingestellt).")
if st.button("Wärmekarte durchrechnen (dauert einige Sekunden)", key="heat_start"):
    st.session_state["heat_on"] = True
if st.session_state.get("heat_on"):
    with st.spinner("Rechne 5 × 4 Zellen × 10 Netze..."):
        hm = _heat(params)
    st.plotly_chart(build_heat(hm), width="stretch", key="heat_chart")
    st.caption("Rechts (hohe Korrelation) und unten (kleines Bestandsgewicht) verschwindet der Vorteil: dort ist die Standortplanung ohne Bestand ausreichend.")

st.subheader("🔬 Wie weit ist die Lokalsuche vom Optimum?")
allowed = ev.exact_allowed(params)
st.caption(f"Für kleine Netze (höchstens {C.EXACT_MAX_CUSTOMERS} Kunden und {C.EXACT_MAX_SITES} Lager) rechnet eine Mengenpartitionierung das exakte Optimum mit Bestandskosten nach (jede Kundengruppe je Lager als eigene Spalte; dauert einige Sekunden).")
if st.button("Exakt nachrechnen", key="exact_start", disabled=not allowed, help=None if allowed else f"Nur bis {C.EXACT_MAX_CUSTOMERS} Kunden und {C.EXACT_MAX_SITES} Lager (dieses Netz: {net.n} Kunden, {net.m} Lager)."):
    st.session_state["exact_on"] = True
if st.session_state.get("exact_on") and allowed:
    with st.spinner("Rechne exakt..."):
        ex_res = _exact(params)
    st.table({"Lösung": ["Optimum (exakt)", "Gemeinsam optimiert (Lokalsuche, 5 Starts)", "Lokalsuche nur aus naiver Lösung und 'alle offen' (2 Starts)", "Naiv (ohne Bestand geplant)"],
              "Kosten": [_int(ex_res["opt"]), _int(ex_res["joint"]), _int(ex_res["two_starts"]), _int(ex_res["naive"])],
              "Mehrkosten gegenüber dem Optimum": ["–", _pct(ex_res["gap_joint"], 3), _pct(ex_res["gap_two"], 3), _pct(ex_res["gap_naive"], 2)]})
    if ex_res["gap_joint"] > 1e-6:
        st.warning(f"⚠️ Die Lokalsuche endet hier {_pct(ex_res['gap_joint'], 2)} über dem Optimum: einzelne Öffnen-, Schließen- und Tausch-Züge führen nicht dorthin (das Optimum liegt in einer anderen Lagermenge).")
    elif ex_res["gap_two"] > 1e-6:
        st.info(f"Mit den fünf Starts trifft die Lokalsuche das Optimum. Mit nur zwei Starts (naive Lösung, alle Lager offen) bliebe sie {_pct(ex_res['gap_two'], 2)} darüber: die kleine Lösung ist von dort mit Einzelzügen nicht zu erreichen.")
    else:
        st.success("✅ Die Lokalsuche trifft das Optimum.")

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist - und wer ansetzt |
|---|---|
| **Gleichkorrelation** | Alle Kundenpaare haben dieselbe Korrelation; reale Nachfragen sind regional oder nach Sortiment unterschiedlich korreliert. Der Effekt ist dann kleiner oder größer, je nachdem, wen das Lager bündelt. |
| **Nur Sicherheitsbestand** | Zyklusbestand (der ebenfalls mit der Wurzel der Menge wächst), Servicegrad-Definition und Lieferzeit stecken im einen Gewicht; die Bestandsdemos des Portfolios (Prognose, Bündelung, Lieferkette) rechnen sie einzeln. Der Zyklusbestand ist nicht gebaut. |
| **Ein Artikel, eine Periode** | Mehrere Artikel oder Sortimente teilen sich Lager; das Modell zeigt den Standorteffekt für einen. |
| **Keine Kapazitäten** | Lager haben unbegrenzte Größe; mit Kapazität greift die Lagrange-Relaxation aus dem Stück zur kapazitierten Standortplanung. |
| **Lokalsuche** | Heuristik: mit fünf Starts trifft sie in den gemessenen Kleinnetzen das Optimum, mit nur zwei Starts (naive Lösung, alle offen) nicht immer (Beispiel 'Ein Start reicht nicht'); für große Netze gibt es hier keinen Optimalitätsbeweis. |
| **Erzeugte Netze und erfundene Parameter** | Gleichverteilte Punkte, erfundene Kosten; die Aussagen gelten für diese Modellwelt, nicht für ein bestimmtes Unternehmen. |
"""
)
st.caption("Die Standortplanungs-Linie ist als Ganzes geplant: das Standortproblem ohne Kapazität als Wurzel, danach die kapazitierte Standortplanung mit Lagrange-Relaxation, p-Center, dieses Stück (Standort mit Bestand), Wettbewerbsstandort und Hub-Standorte.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Kandidaten $I$, Kunden $J$ mit mittlerer Nachfrage $\mu_j$ und Standardabweichung $\sigma_j=\mu_j\cdot cv$; $x_{ij}\in\{0,1\}$ ordnet Kunde $j$ dem Lager $i$ zu, $y_i\in\{0,1\}$ öffnet es:
$$\min\ \sum_i f_iy_i+\sum_{i,j}t\,\mu_jd_{ij}x_{ij}+\sum_i hz\cdot\sqrt{(1-\rho)\sum_j\sigma_j^2x_{ij}+\rho\Big(\sum_j\sigma_jx_{ij}\Big)^2}\quad\text{mit}\ \sum_ix_{ij}=1,\ x_{ij}\le y_i.$$
Die Wurzel ist in $x$ **konkav**: ein zusätzlicher Kunde erhöht den Bestand eines Lagers umso weniger, je größer es schon ist. Bei $\rho=1$ wird der Term linear, $hz\cdot\sum_j\sigma_jx_{ij}$, und das Problem ist das gewöhnliche Standortproblem: gemeinsame und naive Planung fallen zusammen.

**Naiv:** löse ohne den Bestandsterm (exaktes MILP) und bewerte mit ihm. **Neuzuordnung:** dieselbe Lagermenge, die Kunden ziehen einzeln um, wenn die Gesamtkosten sinken. **Gemeinsam:** Lokalsuche über die Lagermenge $S$ mit den Zügen Öffnen, Schließen, Tausch; jede Menge bewertet mit der besten gefundenen Zuordnung (Kundenzüge), Starts: naive Lösung, „alle offen“ und die drei besten Ein-Lager-Lösungen (die Suche bleibt sonst in Lagermengen stehen, die von einer viel kleineren übertroffen werden).

**Exakt (Kleinnetz).** Für jedes Lager $i$ und jede Kundenteilmenge $S$ eine Spalte mit den Kosten $f_i+\sum_{j\in S}t\mu_jd_{ij}+hz\sqrt{\cdots}$; jeder Kunde in genau einer gewählten Spalte, jedes Lager in höchstens einer (Mengenpartitionierung, $m\cdot2^n$ Spalten, HiGHS).

Implementiert in `lip_scenario.py` (Netze, Zufallsgenerator), `lip_costs.py` (Kostenmodell), `lip_heuristics.py` (Zuordnung, Lokalsuche), `lip_exact.py` (MILP, Mengenpartitionierung, Brute Force), `lip_evaluation.py` (Reihen, Verteilungen, Wärmekarte).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
