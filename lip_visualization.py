"""Plotly-Abbildungen: Karte mit Lagern und zugeordneten Kunden, Kostenbalken (Fix / Transport / Bestand), Reihen über Bestandsgewicht und Korrelation, Verteilung der Mehrkosten, Wärmekarte.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Karten haben gleichen Maßstab (scaleanchor) mit automatischem Bereich; der Rand kommt über zwei unsichtbare Punkte
(ein fest vorgegebener Bereich wird beim ersten Zeichnen in schmaler Breite eingefroren)."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import lip_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(net, mod, sol, height=440, color=C.COLORS["joint"]):
    """Kunden (Punkte, Größe nach Nachfrage) mit Linie zum bedienenden Lager; geöffnete Lager (Quadrate, Nummer, Größe nach bedienter Nachfrage); nicht geöffnete Kandidaten grau."""
    fig = go.Figure()
    xs, ys = [], []
    for j, i in enumerate(sol.assign):
        xs += [net.cust_pos[j][0], net.site_pos[i][0], None]
        ys += [net.cust_pos[j][1], net.site_pos[i][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLORS["line"], width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[p[0] for p in net.cust_pos], y=[p[1] for p in net.cust_pos], mode="markers", name="Kunde",
                             marker=dict(color="#1f77b4", size=[5 + net.mu[j] * 0.5 for j in range(net.n)], opacity=0.8),
                             text=[f"{net.cust_names[j]}: Nachfrage {net.mu[j]}, Standardabweichung {net.sigma[j]:.1f}".replace(".", ",") for j in range(net.n)], hoverinfo="text"))
    closed = [i for i in range(net.m) if i not in sol.open]
    if closed:
        fig.add_trace(go.Scatter(x=[net.site_pos[i][0] for i in closed], y=[net.site_pos[i][1] for i in closed], mode="markers", name="nicht geöffnet",
                                 marker=dict(symbol="square-open", color=C.COLORS["closed"], size=10, line=dict(width=1.5)), text=[f"{net.site_names[i]} (Fixkosten {net.f[i]})" for i in closed], hoverinfo="text"))
    load = mod.load(sol.open, sol.assign)
    fig.add_trace(go.Scatter(x=[net.site_pos[i][0] for i in sol.open], y=[net.site_pos[i][1] for i in sol.open], mode="markers+text", name="Lager",
                             marker=dict(symbol="square", color=color, size=[12 + load[i]["mu"] / 8 for i in sol.open], line=dict(color="#111111", width=1)),
                             text=[str(i + 1) for i in sol.open], textposition="top center", textfont=dict(size=10),
                             hovertext=[f"{net.site_names[i]}: {load[i]['customers']} Kunden, Nachfrage {load[i]['mu']}, Standardabweichung {load[i]['sd']:.1f}".replace(".", ",") for i in sol.open], hoverinfo="text"))
    pad = 6
    fig.add_trace(go.Scatter(x=[-pad, 99 + pad], y=[-pad, 99 + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_costs(rows, height=260):
    """Gestapelte Balken je Lösung: Fixkosten, Transport, Bestand. `rows`: [(Beschriftung, Kostenaufteilung)]."""
    fig = go.Figure()
    labels = [r[0] for r in rows]
    for key, name in (("fixed", "Fixkosten"), ("transport", "Transport"), ("stock", "Sicherheitsbestand")):
        fig.add_trace(go.Bar(y=labels, x=[r[1][key] for r in rows], name=name, orientation="h", marker_color=C.COLORS[key],
                             text=[f"{r[1][key]:,.0f}".replace(",", " ") for r in rows], textposition="inside", hovertemplate="%{y}: %{x:,.0f}<extra>" + name + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Gesamtkosten je Periode")
    _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=1.18, x=0), margin=dict(l=10, r=10, t=30, b=10))
    return fig


def build_series(rows, xlabel, height=340):
    """Zwei Felder: Zahl der Lager (naive und gemeinsame Lösung) und Mehrkosten der naiven Lösung in Prozent, über `x` (Bestandsgewicht oder Korrelation)."""
    xs = [r["x"] for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Geöffnete Lager", "Mehrkosten der naiven Lösung"), horizontal_spacing=0.12)
    fig.add_trace(go.Scatter(x=xs, y=[r["naive_sites"] for r in rows], mode="lines+markers", name="naiv (ohne Bestand geplant)", line=dict(color=C.COLORS["naive"], shape="hv")), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[r["joint_sites"] for r in rows], mode="lines+markers", name="gemeinsam optimiert", line=dict(color=C.COLORS["joint"], shape="hv")), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[r["gap"] for r in rows], mode="lines+markers", name="Mehrkosten in %", showlegend=False, line=dict(color=C.COLORS["stock"])), row=1, col=2)
    fig.update_xaxes(title_text=xlabel)
    fig.update_yaxes(title_text="Lager", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Prozent", rangemode="tozero", row=1, col=2)
    _base(fig, height)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig


def build_dist(gaps, height=300):
    fig = go.Figure(go.Histogram(x=gaps, nbinsx=20, marker_color=C.COLORS["naive"], hovertemplate="%{x:.1f} %: %{y} Netze<extra></extra>"))
    mean = sum(gaps) / len(gaps)
    fig.add_vline(x=mean, line=dict(color="#111111", dash="dash"), annotation_text=f"Mittel {mean:.1f} %".replace(".", ","), annotation_position="top right")
    fig.update_xaxes(title="Mehrkosten der naiven Lösung in %")
    fig.update_yaxes(title="Netze")
    return _base(fig, height)


def build_heat(hm, height=300):
    z = hm["grid"]
    fig = go.Figure(go.Heatmap(x=[f"{r} %" for r in hm["rho"]], y=[str(h) for h in hm["hz"]], z=z, colorscale="Oranges", zmin=0,
                               text=[[f"{v:.1f}".replace(".", ",") + " %" for v in row] for row in z], texttemplate="%{text}", hovertemplate="Bestandsgewicht %{y}, Korrelation %{x}: %{z:.2f} %<extra></extra>",
                               colorbar=dict(title="%", thickness=12)))
    fig.update_xaxes(title="Korrelation der Kundennachfragen")
    fig.update_yaxes(title="Bestandsgewicht")
    return _base(fig, height)
