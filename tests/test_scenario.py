"""Szenario: Zufallsnetze - ganzzahlig, deterministisch, in den erwarteten Grenzen; Geometrie unabhängig von Schwankung und Fixkosten-Faktor."""

import pytest

import lip_scenario as sc


def test_distance_is_integer_euclid_in_tenths():
    assert sc.distance((0, 0), (3, 4)) == 50 and sc.distance((5, 5), (5, 5)) == 0 and sc.distance((0, 0), (1, 1)) == 14


def test_generate_is_deterministic_and_within_bounds():
    a = sc.generate(12, 30, 50, 100, 1)
    assert a == sc.generate(12, 30, 50, 100, 1) and a != sc.generate(12, 30, 50, 100, 2)
    assert (a.m, a.n) == (12, 30) and all(0 <= x < sc.MAP_W and 0 <= y < sc.MAP_W for x, y in a.site_pos + a.cust_pos)
    assert all(sc.MU_MIN <= v <= sc.MU_MAX for v in a.mu) and all(isinstance(v, int) for v in a.f)
    assert all(105 <= v <= 245 for v in a.f)                       # 60 bis 140 % von 175
    assert all(isinstance(v, int) for row in a.d for v in row)


def test_geometry_does_not_depend_on_cv_or_fixed_factor():
    a, b = sc.generate(10, 20, 30, 100, 7), sc.generate(10, 20, 90, 200, 7)
    assert (a.site_pos, a.cust_pos, a.mu, a.d) == (b.site_pos, b.cust_pos, b.mu, b.d)
    assert all(abs(fb - 2 * fa) <= 1 for fa, fb in zip(a.f, b.f))      # ganzzahlig abgerundet and b.sigma[0] == pytest.approx(3 * a.sigma[0])


def test_sigma_is_cv_percent_of_mu():
    net = sc.generate(6, 8, 50, 100, 3)
    assert all(s == pytest.approx(0.5 * m) for s, m in zip(net.sigma, net.mu))


def test_distances_are_symmetric_in_the_sense_of_the_positions():
    net = sc.generate(8, 12, 50, 100, 5)
    assert all(net.d[i][j] == sc.distance(net.site_pos[i], net.cust_pos[j]) for i in range(net.m) for j in range(net.n))
