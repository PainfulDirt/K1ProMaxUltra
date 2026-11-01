"""Low-level geometry for the part-cooling ducts (build123d / OCP), all lengths in mm.

The duct is built from *chains*: ordered lists of planar polygon sections that are joined by
ruled lofts. Every chain produces two solids:

  air    - the internal air path (loft of the sections)
  outer  - the same sections offset outward by the wall thickness

The printed body is   union(outer of all chains) - union(air of all chains),  so junctions,
splitters and branch openings fall out of the booleans automatically.

Chain ends:
  "open"  - the end is an opening (fan inlet, outlet). The air is extended past the outer by
            `ext` so the boolean cuts a clean hole.
  "cap"   - closed end. The outer is extended past the air by the wall thickness.
            This is also used where a chain merges into another chain's air volume (a branch,
            a port root, a feed entering the manifold): the part of the cap that lies inside the
            other air volume is removed by the subtraction, the rest closes the shell.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from build123d import Solid, Wire


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# --------------------------------------------------------------------------- polygons (2D)
def poly_rect(w, h, a0=None, b0=None):
    """Rectangle w (along u) x h (along v). Default centred; a0/b0 give the min corner."""
    a0 = -w / 2 if a0 is None else a0
    b0 = -h / 2 if b0 is None else b0
    return [(a0, b0), (a0 + w, b0), (a0 + w, b0 + h), (a0, b0 + h)]


def poly_gable(w, h_side, roof, b0=None):
    """Pentagon: rectangle w x h_side with a ridge `roof` above the top edge (roof=0: rectangle
    with a mid-point on the top edge, so it can be lofted against a real gable)."""
    b0 = -h_side / 2 if b0 is None else b0
    return [(-w / 2, b0), (w / 2, b0), (w / 2, b0 + h_side), (0.0, b0 + h_side + roof), (-w / 2, b0 + h_side)]


def poly_area(p):
    p = np.asarray(p, float)
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def ccw(p):
    return p if poly_area(p) > 0 else list(reversed(p))


def offset_convex(p, t):
    """Offset a convex polygon outward by t (mitred corners). Collinear vertices are kept."""
    p = np.asarray(ccw(list(p)), float)
    n = len(p)
    out = []
    for i in range(n):
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        e1, e2 = unit(b - a), unit(c - b)
        n1 = np.array([e1[1], -e1[0]])
        n2 = np.array([e2[1], -e2[0]])
        cross = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(cross) < 1e-9:                     # collinear: plain normal shift
            out.append(b + n1 * t)
            continue
        # intersection of the two offset lines  a + n1 t + s e1  and  b + n2 t + r e2
        A = np.array([e1, -e2]).T
        s = np.linalg.solve(A, (b + n2 * t) - (a + n1 * t))[0]
        out.append(a + n1 * t + s * e1)
    return [tuple(q) for q in out]


def inscribed_diameter(p, n=60):
    """Largest inscribed circle diameter of a convex polygon (grid search + refine)."""
    p = np.asarray(ccw(list(p)), float)
    edges = [(p[i], p[(i + 1) % len(p)]) for i in range(len(p))]

    def dist(q):
        d = 1e9
        for a, b in edges:
            e = unit(b - a)
            nrm = np.array([e[1], -e[0]])
            d = min(d, -float((q - a) @ nrm))     # inside -> positive
        return d
    lo, hi = p.min(0), p.max(0)
    best, bq = -1, None
    for x in np.linspace(lo[0], hi[0], n):
        for y in np.linspace(lo[1], hi[1], n):
            d = dist(np.array([x, y]))
            if d > best:
                best, bq = d, (x, y)
    return 2 * best


# --------------------------------------------------------------------------- sections / chains
@dataclass
class Section:
    c: np.ndarray            # centre (3,)
    u: np.ndarray            # local a-axis (3,)
    v: np.ndarray            # local b-axis (3,)
    poly: list               # [(a, b), ...] air polygon
    outer: list | None = None  # optional explicit outer polygon (else offset by chain t)

    def pts(self, poly=None):
        poly = self.poly if poly is None else poly
        return [tuple(self.c + a * self.u + b * self.v) for a, b in poly]

    def normal(self):
        return unit(np.cross(self.u, self.v))

    def moved(self, d):
        return Section(self.c + np.asarray(d, float), self.u, self.v, self.poly, self.outer)


def sec(c, u, v, poly, outer=None):
    return Section(np.asarray(c, float), unit(u), unit(v), list(poly), outer)


@dataclass
class Chain:
    name: str
    sections: list
    t: float = 1.2
    start: str = "cap"        # open | cap
    end: str = "cap"
    ext: float = 1.0          # air extension at open ends
    role: str = ""            # feed | manifold | port | ...
    meta: dict = field(default_factory=dict)

    def _end_dir(self, first):
        s = self.sections
        if first:
            d = s[0].c - s[1].c
        else:
            d = s[-1].c - s[-2].c
        if np.linalg.norm(d) < 1e-9:
            d = s[0].normal()
        return unit(d)

    def _outer_poly(self, s):
        return s.outer if s.outer is not None else offset_convex(s.poly, self.t)

    def air_sections(self):
        s = list(self.sections)
        if self.start == "open":
            s.insert(0, s[0].moved(self._end_dir(True) * self.ext))
        if self.end == "open":
            s.append(s[-1].moved(self._end_dir(False) * self.ext))
        return s

    def outer_sections(self):
        s = [Section(x.c, x.u, x.v, self._outer_poly(x)) for x in self.sections]
        if self.start == "cap":
            s.insert(0, s[0].moved(self._end_dir(True) * self.t))
        if self.end == "cap":
            s.append(s[-1].moved(self._end_dir(False) * self.t))
        return s

    def air(self):
        return loft_sections(self.air_sections())

    def outer_solid(self):
        return loft_sections(self.outer_sections())


def loft_sections(secs):
    wires = [Wire.make_polygon(s.pts(), close=True) for s in secs]
    sol = Solid.make_loft(wires, ruled=True)
    if not sol.is_valid:
        raise ValueError("invalid loft")
    if sol.volume < 0:
        raise ValueError("negative loft volume")
    return sol


def fuse_all(solids):
    solids = [s for s in solids if s is not None]
    if len(solids) == 1:
        return solids[0]
    return solids[0].fuse(*solids[1:]).clean()


# --------------------------------------------------------------------------- frames / paths
def bend_sections(s0: Section, axis, radius, angle_deg, n=6, poly_end=None):
    """Sections along a circular bend starting at section s0 (whose normal is the flow direction).
    The bend turns the flow toward `axis` x normal ... specified explicitly: rotate about the unit
    vector `axis` through the bend centre located at s0.c + radius * (axis x n)."""
    n0 = s0.normal()
    axis = unit(axis)
    rdir = unit(np.cross(axis, n0))          # from centreline toward the bend centre
    centre = s0.c + radius * rdir
    out = []
    for k in range(1, n + 1):
        th = math.radians(angle_deg) * k / n
        R = rot(axis, th)
        c = centre + R @ (s0.c - centre)
        poly = s0.poly if poly_end is None else interp_poly(s0.poly, poly_end, k / n)
        out.append(Section(c, R @ s0.u, R @ s0.v, poly))
    return out


def rot(axis, th):
    a = unit(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def interp_poly(p0, p1, f):
    return [tuple((1 - f) * np.asarray(a) + f * np.asarray(b)) for a, b in zip(p0, p1)]


class RoundedRectPath:
    """Closed CCW path = axis-aligned rectangle [xa,xb]x[ya,yb] offset outward by d."""

    def __init__(self, xa, xb, ya, yb, d):
        self.xa, self.xb, self.ya, self.yb, self.d = xa, xb, ya, yb, d
        W, H = xb - xa, yb - ya
        q = math.pi * d / 2
        # pieces in CCW order starting at the front edge's left end
        self.pieces = [("line", (xa, ya - d), (xb, ya - d), W),
                       ("arc", (xb, ya), -90.0, q),
                       ("line", (xb + d, ya), (xb + d, yb), H),
                       ("arc", (xb, yb), 0.0, q),
                       ("line", (xb, yb + d), (xa, yb + d), W),
                       ("arc", (xa, yb), 90.0, q),
                       ("line", (xa - d, yb), (xa - d, ya), H),
                       ("arc", (xa, ya), 180.0, q)]
        self.L = sum(p[-1] for p in self.pieces)

    def at(self, s):
        """(point xy, outward normal xy) at arclength s (wraps)."""
        s = s % self.L
        for kind, a, b, ln in self.pieces:
            if s <= ln + 1e-12:
                f = s / ln if ln > 0 else 0
                if kind == "line":
                    p = (1 - f) * np.array(a) + f * np.array(b)
                    t = unit(np.array(b) - np.array(a))
                    return p, np.array([t[1], -t[0]])
                th = math.radians(b + 90 * f)
                nrm = np.array([math.cos(th), math.sin(th)])
                return np.array(a) + self.d * nrm, nrm
            s -= ln
        raise RuntimeError

    def s_at_azimuth(self, az_deg):
        """Arclength where the ray from the origin at azimuth az hits the path."""
        ss = np.linspace(0, self.L, 4001)[:-1]
        az = np.array([math.degrees(math.atan2(*self.at(s)[0][::-1])) % 360 for s in ss])
        target = az_deg % 360
        diff = (az - target + 180) % 360 - 180
        i = int(np.argmin(np.abs(diff)))
        # refine by bisection on a small bracket
        lo, hi = ss[i] - self.L / 4000, ss[i] + self.L / 4000
        for _ in range(40):
            mid = (lo + hi) / 2
            a_mid = math.degrees(math.atan2(*self.at(mid)[0][::-1])) % 360
            if ((a_mid - target + 180) % 360 - 180) < 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def samples(self, s0, s1, arc_step_deg=12.0):
        """Arclength samples from s0 to s1 (CCW, s1 may exceed L): piece ends + arc subdivisions."""
        if s1 < s0:
            s1 += self.L
        pts = [s0]
        base = 0.0
        for lap in range(2):
            acc = base
            for kind, a, b, ln in self.pieces:
                if kind == "arc":
                    nsub = max(1, int(math.ceil(90 / arc_step_deg)))
                    for k in range(nsub + 1):
                        pts.append(acc + ln * k / nsub)
                else:
                    pts += [acc, acc + ln]
                acc += ln
            base += self.L
        pts = sorted(set(round(x, 9) for x in pts if s0 < x < s1))
        out = [s0] + [p for p in pts if p - s0 > 0.3 and s1 - p > 0.3] + [s1]
        return out


def ray_exit_box(az_deg, xa, xb, ya, yb):
    """Distance from the origin along azimuth az to the boundary of the box (origin inside)."""
    c, s = math.cos(math.radians(az_deg)), math.sin(math.radians(az_deg))
    ts = []
    if c > 1e-12:
        ts.append(xb / c)
    if c < -1e-12:
        ts.append(xa / c)
    if s > 1e-12:
        ts.append(yb / s)
    if s < -1e-12:
        ts.append(ya / s)
    return min(ts)


def box_solid(xmin, xmax, ymin, ymax, zmin, zmax):
    return Solid.make_box(xmax - xmin, ymax - ymin, zmax - zmin).translate((xmin, ymin, zmin))
