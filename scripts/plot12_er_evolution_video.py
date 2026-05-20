"""
plot12_er_evolution_video.py  —  YouTube Cinematic Edition v4
=============================================================
Erdős–Rényi G(n,p) phase transition — polished science-video quality.

New in v4 vs v3:
  ✦ Starfield background — 130 stars with varied size/opacity for depth
  ✦ Outlined nodes — stroke gives 3D definition at any resolution
  ✦ Edge glow layer — soft halo behind every new edge
  ✦ Double-layer S(p) curve — wide dim glow + sharp bright line
  ✦ Flash() shockwave at Act III critical point
  ✦ Ripple rings when nodes join the giant component (per step)
  ✦ Live p-progress bar below HUD (blue→gold→green color-coded)
  ✦ Component count tracker (Act II)
  ✦ Per-act graph panel tint shift (atmosphere changes per act)
  ✦ Connectivity Flash burst at final connected milestone
  ✦ Ending: full-canvas teal wave + formula card with gold border glow

Render:
    manim -ql  plot12_er_evolution_video.py Plot12ErdosRenyiEvolution
    manim -qm  plot12_er_evolution_video.py Plot12ErdosRenyiEvolution
    manim -qh  plot12_er_evolution_video.py Plot12ErdosRenyiEvolution
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

import networkx as nx
import numpy as np
from manim import *

# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════════════════════
BG           = "#020B1A"   # deep-space navy (not pure black)

# Nodes
NODE_ISO     = "#93C5FD"   # sky-blue   — isolated/non-giant (CLEARLY visible)
NODE_GIANT   = "#2DD4BF"   # vivid teal — giant component
NODE_STROKE  = "#DBEAFE"   # pale blue  — node outline stroke (gives 3-D pop)

# Cluster rainbow (Act II — all vivid, never grey)
CLUST_COLS = [
    "#67E8F9",  # sky cyan
    "#C084FC",  # violet
    "#4ADE80",  # green
    "#F472B6",  # pink
    "#FB923C",  # orange
    "#FCD34D",  # amber
    "#F87171",  # coral red
    "#A78BFA",  # lavender
]

# Edges
EDGE_REST    = "#2563EB"   # electric blue — resting (clearly visible)
EDGE_GIANT   = "#0D9488"   # teal          — giant component
EDGE_NEW     = "#FCD34D"   # gold          — flash for new edge
EDGE_NEW_GLO = "#FEF08A"   # pale gold     — soft glow behind new edge

# Glow
GLOW_GIANT   = "#99F6E4"   # pale teal     — glow ring on giant nodes

# UI panels
PANEL_BG     = "#05101F"   # very dark navy
PANEL_BD     = "#1D4ED8"   # bright-blue border
DIVIDER_C    = "#1E40AF"
LIGHT        = "#F0F9FF"   # near-white
DIM_TEXT     = "#94A3B8"   # readable slate
GOLD         = "#FCD34D"   # amber highlights
GOLD_DIM     = "#D97706"   # dim amber (theory curve)
RED_THRESH   = "#F87171"   # connectivity threshold
TEAL_MED     = "#0D9488"
GREEN_VIV    = "#4ADE80"
PURPLE_VIV   = "#C084FC"

# Graph panel tint — shifts per act for atmosphere
ACT_PANEL = {
    1: ("#040E20", 0.55),   # cool blue-black
    2: ("#04180A", 0.55),   # dark green tint
    3: ("#180D00", 0.55),   # amber-black
    4: ("#021814", 0.55),   # deep teal-black
}

# Act identity
ACT_META = {
    1: ("Act I",   "Isolated Nodes",     NODE_ISO),
    2: ("Act II",  "Small Clusters",     GREEN_VIV),
    3: ("Act III", "Phase Transition",   GOLD),
    4: ("Act IV",  "Connected Graph",    NODE_GIANT),
}


# ═══════════════════════════════════════════════════════════════════════════
#  DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Snapshot:
    act: int
    p: float
    mean_degree: float
    giant_fraction: float
    edges: list[tuple[int, int]]
    new_edges: list[tuple[int, int]]
    components: list[list[int]]
    giant_nodes: set[int]
    is_connected: bool


# ═══════════════════════════════════════════════════════════════════════════
#  NETWORK HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def _edge_schedule(n: int, seed: int):
    rng = random.Random(seed)
    s = [(u, v, rng.random()) for u in range(n) for v in range(u + 1, n)]
    s.sort(key=lambda x: x[2])
    return s


def _pick_good_seed(n: int, target_p: float, base: int = 42):
    for seed in range(base, base + 500):
        sc = _edge_schedule(n, seed)
        G = nx.Graph()
        G.add_nodes_from(range(n))
        for u, v, t in sc:
            if t > target_p:
                break
            G.add_edge(u, v)
        if nx.is_connected(G):
            return sc, seed
    return _edge_schedule(n, base), base


def build_snapshots(n: int, p_plan: list, seed: int = 42):
    conn_p = math.log(n) / n
    sched, actual_seed = _pick_good_seed(n, conn_p, base=seed)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    snaps, ptr = [], 0
    prev_edges: set[tuple[int, int]] = set()
    for act, p in p_plan:
        while ptr < len(sched) and sched[ptr][2] <= p:
            G.add_edge(sched[ptr][0], sched[ptr][1])
            ptr += 1
        edges_now = {tuple(sorted(e)) for e in G.edges()}
        new = sorted(edges_now - prev_edges)
        prev_edges = set(edges_now)
        comps = sorted(
            (sorted(c) for c in nx.connected_components(G)),
            key=len, reverse=True,
        )
        giant = set(comps[0]) if comps else set()
        snaps.append(Snapshot(
            act=act, p=p,
            mean_degree=2 * len(edges_now) / n,
            giant_fraction=len(giant) / n,
            edges=sorted(edges_now),
            new_edges=new,
            components=comps,
            giant_nodes=giant,
            is_connected=(len(comps) == 1),
        ))
    return snaps, actual_seed


def compute_positions(n: int, final_edges: list, seed: int,
                      center: np.ndarray) -> dict[int, np.ndarray]:
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for e in final_edges:
        G.add_edge(*e)
    p2d = nx.spring_layout(G, k=0.40, iterations=280, seed=seed, scale=3.45)
    return {
        nd: np.array([x + center[0], y + center[1], 0.0])
        for nd, (x, y) in p2d.items()
    }


# ═══════════════════════════════════════════════════════════════════════════
#  STYLE HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def node_color_map(snap: Snapshot) -> dict[int, str]:
    cmap: dict[int, str] = {}
    if snap.act <= 2:
        ci = 0
        for comp in snap.components:
            if len(comp) == 1:
                for nd in comp:
                    cmap[nd] = NODE_ISO
            else:
                col = CLUST_COLS[ci % len(CLUST_COLS)]
                ci += 1
                for nd in comp:
                    cmap[nd] = col
    else:
        for comp in snap.components:
            col = NODE_GIANT if set(comp) == snap.giant_nodes else NODE_ISO
            for nd in comp:
                cmap[nd] = col
    return cmap


def edge_style(snap: Snapshot, u: int, v: int) -> tuple[str, float, float]:
    if snap.act <= 2:
        return EDGE_REST, 1.5, 0.65
    if u in snap.giant_nodes and v in snap.giant_nodes:
        return EDGE_GIANT, 2.5, 0.92
    return EDGE_REST, 1.2, 0.48


def theoretical_S(p_arr: list, n: int) -> list:
    results = []
    for p in p_arr:
        c = p * (n - 1)
        if c <= 1.0:
            results.append(0.0)
            continue
        S = 0.5
        for _ in range(500):
            S_new = 1.0 - math.exp(-c * S)
            if abs(S_new - S) < 1e-13:
                break
            S = S_new
        results.append(max(0.0, S))
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  SCENE
# ═══════════════════════════════════════════════════════════════════════════
class Plot12ErdosRenyiEvolution(MovingCameraScene):

    def construct(self) -> None:
        self.camera.background_color = BG

        n      = 100
        pc     = 1.0 / n
        conn_p = math.log(n) / n

        # ── evolution plan ────────────────────────────────────────────────
        act1 = [(1, p) for p in [0.0, 0.0002, 0.0005, 0.0008, 0.0010]]
        act2 = [(2, float(p)) for p in np.linspace(0.0015, 0.009, 14)]
        act3 = [(3, float(p)) for p in np.linspace(0.0095, 0.020, 16)]
        act4 = [(4, float(p)) for p in np.linspace(0.022, 0.050, 14)]
        p_plan = act1 + act2 + act3 + act4

        snapshots, seed = build_snapshots(n, p_plan, seed=42)
        GRAPH_CENTER = np.array([-2.20, 0.0, 0.0])
        pos = compute_positions(n, snapshots[-1].edges, seed, GRAPH_CENTER)

        # ── trackers ──────────────────────────────────────────────────────
        p_vt   = ValueTracker(0.0)
        k_vt   = ValueTracker(0.0)
        s_vt   = ValueTracker(0.0)
        ng_vt  = ValueTracker(0.0)
        ncc_vt = ValueTracker(float(n))   # component count

        # ══════════════════════════════════════════════════════════════════
        #  STARFIELD BACKGROUND
        #  130 static stars — varied size and opacity, adds depth/atmosphere
        # ══════════════════════════════════════════════════════════════════
        rng_stars = np.random.default_rng(77)
        stars = VGroup(*[
            Dot(
                np.array([
                    rng_stars.uniform(-7.1, 7.1),
                    rng_stars.uniform(-4.0, 4.0),
                    0.0,
                ]),
                radius=float(rng_stars.uniform(0.008, 0.024)),
                color=WHITE,
                fill_opacity=float(rng_stars.uniform(0.08, 0.48)),
                stroke_width=0,
            )
            for _ in range(130)
        ])
        stars.set_z_index(-5)
        self.add(stars)

        # ══════════════════════════════════════════════════════════════════
        #  ACT 0 — CINEMATIC TITLE CARD
        # ══════════════════════════════════════════════════════════════════
        glow_bar = Rectangle(width=7.0, height=0.06, stroke_width=0)
        glow_bar.set_fill(NODE_GIANT, opacity=0.75)
        glow_bar.shift(UP * 0.28)

        tc_main = Text(
            "Erdős–Rényi Random Graph",
            color=NODE_GIANT, weight=BOLD, font_size=52,
        )
        tc_sub = Text(
            "Phase Transition", color=LIGHT, font_size=36,
        )
        tc_eq = MathTex(
            r"G(n,\,p) \;:\quad p \;\longrightarrow\; \frac{\ln n}{n}",
            color=GOLD, font_size=30,
        )
        tc_cap = Text(
            f"n = {n} nodes  ·  CCNSB, IIIT Hyderabad  ·  Spring 2026",
            color=DIM_TEXT, font_size=14,
        )
        tc_grp = VGroup(tc_main, tc_sub, glow_bar, tc_eq, tc_cap)
        tc_grp.arrange(DOWN, buff=0.30)
        tc_grp.move_to(ORIGIN)

        self.play(
            LaggedStart(
                Write(tc_main, run_time=1.3),
                FadeIn(tc_sub, shift=UP * 0.12, run_time=0.8),
                GrowFromCenter(glow_bar, run_time=0.55),
                Write(tc_eq, run_time=1.2),
                FadeIn(tc_cap, run_time=0.7),
                lag_ratio=0.48,
            )
        )
        self.wait(2.0)
        self.play(FadeOut(tc_grp, shift=UP * 0.3), run_time=0.90)
        self.wait(0.18)

        # ══════════════════════════════════════════════════════════════════
        #  GRAPH AREA PANEL  (tinted, shifts per act)
        # ══════════════════════════════════════════════════════════════════
        graph_panel = RoundedRectangle(
            corner_radius=0.38, width=9.90, height=7.72,
            stroke_color=PANEL_BD, stroke_width=0.8, stroke_opacity=0.30,
        ).set_fill(ACT_PANEL[1][0], opacity=ACT_PANEL[1][1])
        graph_panel.move_to(GRAPH_CENTER)
        graph_panel.set_z_index(-1)
        self.add(graph_panel)

        # ══════════════════════════════════════════════════════════════════
        #  NODES
        #  radius 0.065 — large, with outlined stroke for 3-D definition
        #  + invisible glow ring that lights up when node joins giant
        # ══════════════════════════════════════════════════════════════════
        NODE_R = 0.065
        GLOW_R = 0.21

        node_glows: dict[int, Circle] = {}
        node_cores: dict[int, Dot]    = {}

        for i in range(n):
            glow = Circle(radius=GLOW_R, stroke_width=0)
            glow.set_fill(GLOW_GIANT, opacity=0.0)
            glow.move_to(pos[i])
            glow.set_z_index(6)

            core = Dot(
                pos[i], radius=NODE_R,
                color=NODE_ISO, fill_opacity=1.0,
                stroke_color=NODE_STROKE,
                stroke_width=1.1, stroke_opacity=0.65,
            )
            core.set_z_index(10)

            node_glows[i] = glow
            node_cores[i] = core
            self.add(glow)

        edge_mobs:      dict[tuple[int, int], Line] = {}
        edge_glow_mobs: dict[tuple[int, int], Line] = {}   # soft halos

        # ══════════════════════════════════════════════════════════════════
        #  HEADER
        # ══════════════════════════════════════════════════════════════════
        hdr_title = Text(
            "G(n, p) — Random Graph Evolution",
            color=LIGHT, weight=BOLD, font_size=21,
        )
        hdr_sub = Text(
            f"n = {n}   ·   critical  p_c = 1/n = {pc:.3f}"
            f"   ·   connectivity  p* = ln(n)/n = {conn_p:.4f}",
            color=DIM_TEXT, font_size=11,
        )
        header_grp = VGroup(hdr_title, hdr_sub).arrange(DOWN, buff=0.09)
        header_grp.to_edge(UP, buff=0.16).to_edge(LEFT, buff=0.28)

        # ══════════════════════════════════════════════════════════════════
        #  RIGHT PANEL
        # ══════════════════════════════════════════════════════════════════
        right_panel = RoundedRectangle(
            corner_radius=0.28, width=5.18, height=7.72,
            stroke_color=PANEL_BD, stroke_width=1.8,
        ).set_fill(PANEL_BG, opacity=0.98)
        right_panel.to_edge(RIGHT, buff=0.16).shift(DOWN * 0.06)

        # ── act label ──────────────────────────────────────────────────────
        act_dot = Dot(radius=0.075, color=NODE_ISO, fill_opacity=1.0)
        act_label_txt = Text(
            "Act I  –  Isolated Nodes",
            color=NODE_ISO, font_size=15, weight=BOLD,
        )
        act_label_row = VGroup(act_dot, act_label_txt).arrange(RIGHT, buff=0.14,
                                                                aligned_edge=DOWN)
        act_label_row.next_to(right_panel.get_top(), DOWN, buff=0.36)
        act_label_row.align_to(right_panel, LEFT).shift(RIGHT * 0.32)

        top_div = Line(
            right_panel.get_left()  + RIGHT * 0.24,
            right_panel.get_right() - RIGHT * 0.24,
            stroke_color=DIVIDER_C, stroke_width=1.3, stroke_opacity=0.70,
        ).next_to(act_label_row, DOWN, buff=0.18)

        # ── metrics ────────────────────────────────────────────────────────
        def _row(label: str, tracker: ValueTracker,
                 col: str, dec: int) -> VGroup:
            bullet = Dot(radius=0.052, color=col, fill_opacity=1.0)
            lbl    = Text(label, color=DIM_TEXT, font_size=15)
            num    = DecimalNumber(0, num_decimal_places=dec,
                                   color=col, font_size=22)
            num.add_updater(lambda m, t=tracker: m.set_value(t.get_value()))
            return VGroup(bullet, lbl, num).arrange(
                RIGHT, buff=0.10, aligned_edge=DOWN)

        metrics = VGroup(
            _row("p  =",  p_vt,  GOLD,       4),
            _row("⟨k⟩ =", k_vt,  LIGHT,      2),
            _row("S  =",  s_vt,  NODE_GIANT, 3),
            _row("n_G =", ng_vt, GLOW_GIANT, 0),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.21)
        metrics.next_to(top_div, DOWN, buff=0.24)
        metrics.align_to(right_panel, LEFT).shift(RIGHT * 0.36)

        # ── p progress bar ─────────────────────────────────────────────────
        # Shows how far p has advanced toward p_c and p_conn
        PROG_W = 4.28
        prog_track = RoundedRectangle(
            corner_radius=0.07, width=PROG_W, height=0.15, stroke_width=0,
        ).set_fill(DIVIDER_C, opacity=0.35)

        prog_fill = Rectangle(width=0.02, height=0.15, stroke_width=0)
        prog_fill.set_fill(NODE_ISO, opacity=0.90)
        prog_fill.align_to(prog_track, LEFT)

        # Threshold markers on progress bar
        pc_frac   = pc / conn_p
        cn_frac   = 1.0

        def _pc_tri_pos():
            return (prog_track.get_left()
                    + RIGHT * pc_frac * PROG_W
                    + DOWN * 0.18)

        def _cn_tri_pos():
            return (prog_track.get_left()
                    + RIGHT * (cn_frac - 0.005) * PROG_W
                    + DOWN * 0.18)

        pc_marker = Triangle(fill_opacity=1.0, stroke_width=0).set_fill(GOLD)
        pc_marker.scale(0.08).rotate(PI)
        pc_marker.move_to(_pc_tri_pos())

        cn_marker = Triangle(fill_opacity=1.0, stroke_width=0).set_fill(RED_THRESH)
        cn_marker.scale(0.08).rotate(PI)
        cn_marker.move_to(_cn_tri_pos())

        prog_lbl = Text("p  →", color=DIM_TEXT, font_size=11)

        prog_grp = VGroup(prog_lbl, prog_track)
        prog_grp.arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        prog_grp.next_to(metrics, DOWN, buff=0.24)
        prog_grp.align_to(right_panel, LEFT).shift(RIGHT * 0.36)

        prog_fill.align_to(prog_track, LEFT).align_to(prog_track, DOWN)
        pc_marker.move_to(
            prog_track.get_left() + RIGHT * pc_frac * PROG_W + DOWN * 0.17)
        cn_marker.move_to(
            prog_track.get_left() + RIGHT * 0.995 * PROG_W + DOWN * 0.17)

        def _update_prog(mob: Rectangle) -> None:
            ratio = min(1.0, max(0.0, p_vt.get_value() / conn_p))
            new_w = max(0.02, ratio * PROG_W)
            mob.stretch_to_fit_width(new_w)
            mob.align_to(prog_track, LEFT).align_to(prog_track, DOWN)
            pv = p_vt.get_value()
            if pv < pc * 0.8:
                mob.set_fill(NODE_ISO)
            elif pv < conn_p * 0.75:
                mob.set_fill(GOLD)
            else:
                mob.set_fill(GREEN_VIV)

        prog_fill.add_updater(_update_prog)

        mid_div = Line(
            right_panel.get_left()  + RIGHT * 0.24,
            right_panel.get_right() - RIGHT * 0.24,
            stroke_color=DIVIDER_C, stroke_width=1.1, stroke_opacity=0.55,
        )
        mid_div.next_to(prog_grp, DOWN, buff=0.26)

        # ── component count (visible in Act II) ────────────────────────────
        ncc_label = Text("components:", color=DIM_TEXT, font_size=13)
        ncc_val   = DecimalNumber(float(n), num_decimal_places=0,
                                  color=PURPLE_VIV, font_size=20)
        ncc_val.add_updater(lambda m: m.set_value(ncc_vt.get_value()))
        ncc_row   = VGroup(ncc_label, ncc_val).arrange(RIGHT, buff=0.10,
                                                        aligned_edge=DOWN)
        ncc_row.next_to(mid_div, DOWN, buff=0.15)
        ncc_row.align_to(right_panel, LEFT).shift(RIGHT * 0.36)
        ncc_row.set_opacity(0.0)   # hidden at start; shown in Act II

        # ── S(p) mini-plot ─────────────────────────────────────────────────
        plot_lbl = Text(
            "Giant Fraction  S(p)",
            color=LIGHT, font_size=13, weight=BOLD,
        )

        axes = Axes(
            x_range=[0, 0.055, 0.01],
            y_range=[0, 1.05,  0.25],
            x_length=4.15,
            y_length=2.45,
            axis_config={
                "color": DIM_TEXT, "stroke_width": 1.4,
                "include_tip": False,
            },
            tips=False,
        )

        plot_lbl.next_to(mid_div, DOWN, buff=0.48)
        plot_lbl.align_to(right_panel, LEFT).shift(RIGHT * 0.36)
        axes.next_to(plot_lbl, DOWN, buff=0.18)
        axes.align_to(right_panel, LEFT).shift(RIGHT * 0.38)

        ax_x = Text("p", color=DIM_TEXT, font_size=12).next_to(
            axes.x_axis.get_right(), RIGHT, buff=0.09)
        ax_y = Text("S", color=DIM_TEXT, font_size=12).next_to(
            axes.y_axis.get_top(), UP, buff=0.08)

        # threshold lines — bright, labeled
        pc_dash = DashedLine(
            axes.c2p(pc, 0), axes.c2p(pc, 1.0),
            color=GOLD, stroke_width=2.0, dash_length=0.09, stroke_opacity=0.88,
        )
        pc_lbl = Text("1/n", color=GOLD, font_size=11, weight=BOLD).next_to(
            axes.c2p(pc, 1.0), UP, buff=0.06)
        cn_dash = DashedLine(
            axes.c2p(conn_p, 0), axes.c2p(conn_p, 1.0),
            color=RED_THRESH, stroke_width=1.8, dash_length=0.09,
            stroke_opacity=0.82,
        )
        cn_lbl = Text("lnn/n", color=RED_THRESH, font_size=11, weight=BOLD).next_to(
            axes.c2p(conn_p, 1.0), UP, buff=0.06)

        # theoretical curve (pre-computed dashed amber)
        th_ps = np.linspace(0.0, 0.055, 300).tolist()
        th_ss = theoretical_S(th_ps, n)
        th_pts = [axes.c2p(p, s) for p, s in zip(th_ps, th_ss)]
        theory_crv = VMobject(color=GOLD_DIM, stroke_width=2.0,
                              stroke_opacity=0.65)
        theory_crv.set_points_smoothly(th_pts)

        # double-layer live curve: wide glow + sharp main
        curve_data: dict = {"ps": [0.0], "ss": [0.0]}

        def _pts():
            return list(zip(curve_data["ps"], curve_data["ss"]))

        def _glow_fn() -> VMobject:
            pts = _pts()
            if len(pts) < 2:
                return VMobject()
            mob = VMobject(color=NODE_GIANT, stroke_width=9.0,
                           stroke_opacity=0.14)
            mob.set_points_smoothly([axes.c2p(p, s) for p, s in pts])
            return mob

        def _main_fn() -> VMobject:
            pts = _pts()
            if len(pts) < 2:
                return VMobject()
            mob = VMobject(color=NODE_GIANT, stroke_width=3.0,
                           stroke_opacity=1.0)
            mob.set_points_smoothly([axes.c2p(p, s) for p, s in pts])
            return mob

        live_crv_glow = always_redraw(_glow_fn)
        live_crv_main = always_redraw(_main_fn)

        # live tracking dot (gold, on top of curve)
        live_dot = always_redraw(lambda: Dot(
            axes.c2p(p_vt.get_value(), s_vt.get_value()),
            radius=0.068, color=GOLD, fill_opacity=1.0,
        ).set_z_index(22))

        # dot outer halo
        live_dot_halo = always_redraw(lambda: Circle(
            radius=0.14, stroke_color=GOLD,
            stroke_width=1.2, fill_opacity=0.0, stroke_opacity=0.40,
        ).move_to(axes.c2p(p_vt.get_value(), s_vt.get_value())).set_z_index(21))

        # legend
        leg_th = VGroup(
            DashedLine(ORIGIN, RIGHT * 0.44, color=GOLD_DIM,
                       stroke_width=2.0, stroke_opacity=0.65),
            Text("theory", color=GOLD_DIM, font_size=11),
        ).arrange(RIGHT, buff=0.08)
        leg_ac = VGroup(
            Line(ORIGIN, RIGHT * 0.44, color=NODE_GIANT, stroke_width=2.8),
            Text("actual", color=NODE_GIANT, font_size=11),
        ).arrange(RIGHT, buff=0.08)
        plot_legend = VGroup(leg_th, leg_ac).arrange(RIGHT, buff=0.26)
        plot_legend.next_to(axes, DOWN, buff=0.16)

        # ══════════════════════════════════════════════════════════════════
        #  BOTTOM BANNER
        # ══════════════════════════════════════════════════════════════════
        banner_bg = RoundedRectangle(
            corner_radius=0.20, width=8.85, height=0.68, stroke_width=0,
        ).set_fill(PANEL_BG, opacity=0.97)
        banner_bg.to_edge(DOWN, buff=0.14).to_edge(LEFT, buff=0.22)

        banner_accent = Rectangle(width=0.13, height=0.68, stroke_width=0)
        banner_accent.set_fill(NODE_ISO, opacity=1.0)
        banner_accent.align_to(banner_bg, LEFT).align_to(banner_bg, UP)
        banner_accent.set_z_index(2)

        banner_txt = Text(
            "Act I  –  Isolated Nodes",
            color=NODE_ISO, font_size=20, weight=BOLD,
        )
        banner_txt.move_to(banner_bg).shift(RIGHT * 0.12)
        banner_grp = VGroup(banner_bg, banner_accent, banner_txt)

        # ══════════════════════════════════════════════════════════════════
        #  NODE APPEAR
        # ══════════════════════════════════════════════════════════════════
        self.add(header_grp)
        self.play(
            LaggedStart(
                *[FadeIn(node_cores[i], scale=0.28) for i in range(n)],
                lag_ratio=0.007,
            ),
            run_time=3.0,
        )
        self.wait(0.65)

        # all right-panel UI
        right_ui = VGroup(
            right_panel, act_label_row, top_div, metrics,
            prog_grp, prog_fill, pc_marker, cn_marker,
            mid_div, ncc_row,
            plot_lbl, axes, ax_x, ax_y,
            pc_dash, pc_lbl, cn_dash, cn_lbl,
            theory_crv, plot_legend,
        )
        self.play(
            FadeIn(right_ui,   run_time=1.35),
            FadeIn(banner_grp, run_time=1.05),
            rate_func=smooth,
        )
        self.add(live_crv_glow, live_crv_main, live_dot, live_dot_halo)
        self.wait(0.5)

        # ══════════════════════════════════════════════════════════════════
        #  STEP CONFIG
        # ══════════════════════════════════════════════════════════════════
        STEP_RT = {1: 2.4, 2: 1.85, 3: 1.65, 4: 1.50}
        HOLD_T  = {1: 0.36, 2: 0.26, 3: 0.22, 4: 0.20}

        prev_snap    = snapshots[0]
        prev_new_set: set[tuple[int, int]] = set()
        prev_ncols   = node_color_map(snapshots[0])
        act_has_shown_ncc = False

        # ══════════════════════════════════════════════════════════════════
        #  MAIN ANIMATION LOOP
        # ══════════════════════════════════════════════════════════════════
        for snap in snapshots[1:]:

            # ── act transition ────────────────────────────────────────────
            if snap.act != prev_snap.act:
                act_num, act_name, act_col = ACT_META[snap.act]

                new_dot_mob = Dot(radius=0.075, color=act_col, fill_opacity=1.0)
                new_label_txt = Text(
                    f"{act_num}  –  {act_name}",
                    color=act_col, font_size=15, weight=BOLD,
                )
                new_label_row = VGroup(new_dot_mob, new_label_txt).arrange(
                    RIGHT, buff=0.14, aligned_edge=DOWN)
                new_label_row.move_to(act_label_row)

                new_banner_txt = Text(
                    f"{act_num}  –  {act_name}",
                    color=act_col, font_size=20, weight=BOLD,
                )
                new_banner_txt.move_to(banner_txt).shift(RIGHT * 0.12)

                new_accent = Rectangle(width=0.13, height=0.68, stroke_width=0)
                new_accent.set_fill(act_col, opacity=1.0)
                new_accent.align_to(banner_bg, LEFT).align_to(banner_bg, UP)
                new_accent.set_z_index(2)

                # Graph panel tint shift
                new_tint, new_op = ACT_PANEL[snap.act]

                base_trans = [
                    Transform(act_label_row,   new_label_row),
                    Transform(banner_txt,       new_banner_txt),
                    Transform(banner_accent,    new_accent),
                    graph_panel.animate.set_fill(new_tint, opacity=new_op),
                ]

                # ── Act II: reveal component counter ─────────────────────
                if snap.act == 2 and not act_has_shown_ncc:
                    act_has_shown_ncc = True
                    base_trans.append(ncc_row.animate.set_opacity(1.0))

                # ── Act III: Flash shockwave ──────────────────────────────
                if snap.act == 3:
                    badge_inner = VGroup(
                        Text("⚡ Critical Point", color=WHITE,
                             font_size=17, weight=BOLD),
                        MathTex(r"p_c = \frac{1}{n}",
                                color=GOLD, font_size=24),
                    ).arrange(RIGHT, buff=0.22)
                    badge_rect = RoundedRectangle(
                        corner_radius=0.18,
                        width=badge_inner.width + 0.82,
                        height=badge_inner.height + 0.54,
                        stroke_color=GOLD, stroke_width=2.2,
                    ).set_fill("#160A00", opacity=0.98)
                    badge_inner.move_to(badge_rect)
                    badge = VGroup(badge_rect, badge_inner)
                    badge.move_to(GRAPH_CENTER + UP * 3.0)

                    # shockwave — Flash centered on graph
                    self.play(
                        *base_trans,
                        FadeIn(badge, scale=0.83),
                        Flash(
                            np.array(GRAPH_CENTER),
                            color=GOLD,
                            line_length=1.8,
                            num_lines=20,
                            flash_radius=3.2,
                            time_width=0.45,
                        ),
                        run_time=1.10,
                    )
                    # also flash on the mini-plot at p = pc
                    self.play(
                        Flash(
                            axes.c2p(pc, 0.0),
                            color=GOLD,
                            line_length=0.35,
                            num_lines=12,
                            flash_radius=0.50,
                            time_width=0.4,
                        ),
                        run_time=0.55,
                    )
                    self.wait(1.7)
                    self.play(FadeOut(badge), run_time=0.48)

                # ── Act IV: connectivity badge ────────────────────────────
                elif snap.act == 4:
                    badge_inner = VGroup(
                        Text("✓ Connected", color=WHITE,
                             font_size=17, weight=BOLD),
                        MathTex(r"p = \frac{\ln n}{n}",
                                color=NODE_GIANT, font_size=24),
                    ).arrange(RIGHT, buff=0.22)
                    badge_rect = RoundedRectangle(
                        corner_radius=0.18,
                        width=badge_inner.width + 0.82,
                        height=badge_inner.height + 0.54,
                        stroke_color=NODE_GIANT, stroke_width=2.2,
                    ).set_fill("#001510", opacity=0.98)
                    badge_inner.move_to(badge_rect)
                    badge = VGroup(badge_rect, badge_inner)
                    badge.move_to(GRAPH_CENTER + UP * 3.0)
                    self.play(*base_trans,
                              FadeIn(badge, scale=0.83), run_time=0.85)
                    self.wait(1.35)
                    self.play(FadeOut(badge), run_time=0.45)

                else:
                    self.play(*base_trans, run_time=0.68)

                self.wait(0.26)

            # ── per-step animations ────────────────────────────────────────
            anims: list[Animation] = [
                p_vt.animate.set_value(snap.p),
                k_vt.animate.set_value(snap.mean_degree),
                s_vt.animate.set_value(snap.giant_fraction),
                ng_vt.animate.set_value(float(len(snap.giant_nodes))),
                ncc_vt.animate.set_value(float(len(snap.components))),
            ]

            new_set = set(snap.new_edges)

            # New edges: glow halo layer (behind) + bright main line
            for u, v in snap.new_edges:
                # soft glow layer
                glow_ln = Line(
                    pos[u], pos[v],
                    color=EDGE_NEW_GLO,
                    stroke_width=7.0,
                    stroke_opacity=0.20,
                )
                glow_ln.set_z_index(1)
                edge_glow_mobs[(u, v)] = glow_ln
                self.add(glow_ln)

                # bright main edge
                ln = Line(
                    pos[u], pos[v],
                    color=EDGE_NEW,
                    stroke_width=2.8,
                    stroke_opacity=0.96,
                )
                ln.set_z_index(3)
                edge_mobs[(u, v)] = ln
                anims.append(Create(ln, rate_func=rush_from))

            # cool previous step's gold → resting palette (both layers)
            for u, v in prev_new_set:
                ln = edge_mobs.get((u, v))
                if ln is not None:
                    c, w, o = edge_style(snap, u, v)
                    anims.append(ln.animate.set_stroke(color=c, width=w, opacity=o))
                gl = edge_glow_mobs.get((u, v))
                if gl is not None:
                    anims.append(gl.animate.set_stroke(opacity=0.0))

            # update edges whose component changed
            for u, v in snap.edges:
                if (u, v) in new_set or (u, v) in prev_new_set:
                    continue
                c_new, w_new, o_new = edge_style(snap, u, v)
                c_old, _, _         = edge_style(prev_snap, u, v)
                if c_new != c_old:
                    ln = edge_mobs.get((u, v))
                    if ln:
                        anims.append(ln.animate.set_stroke(
                            color=c_new, width=w_new, opacity=o_new))
                    gl = edge_glow_mobs.get((u, v))
                    if gl:
                        anims.append(gl.animate.set_stroke(opacity=0.0))

            # node color + glow ring
            ncols = node_color_map(snap)
            newly_giant: list[int] = []
            for nd in range(n):
                nc = ncols.get(nd, NODE_ISO)
                oc = prev_ncols.get(nd, NODE_ISO)
                if nc != oc:
                    anims.append(node_cores[nd].animate.set_color(nc))
                    if nc == NODE_GIANT and snap.act >= 3:
                        newly_giant.append(nd)
                        anims.append(
                            node_glows[nd].animate.set_fill(
                                GLOW_GIANT, opacity=0.32))
                        # also brighten stroke
                        anims.append(
                            node_cores[nd].animate.set_stroke(
                                color=GLOW_GIANT, opacity=0.90))
                    elif oc == NODE_GIANT and nc != NODE_GIANT:
                        anims.append(
                            node_glows[nd].animate.set_fill(
                                GLOW_GIANT, opacity=0.0))
                        anims.append(
                            node_cores[nd].animate.set_stroke(
                                color=NODE_STROKE, opacity=0.65))

            # update live curve data
            curve_data["ps"].append(snap.p)
            curve_data["ss"].append(snap.giant_fraction)

            # ── play step ─────────────────────────────────────────────────
            self.play(*anims, run_time=STEP_RT[snap.act], rate_func=smooth)

            # ── RIPPLE RINGS on newly-joined giant nodes ───────────────────
            # Batch up to 10 nodes per step to avoid slowdown
            if newly_giant and snap.act >= 3:
                sample = newly_giant[:10]
                rings = []
                for nd in sample:
                    r = Circle(
                        radius=0.10,
                        stroke_color=GLOW_GIANT,
                        stroke_width=1.8,
                        fill_opacity=0.0,
                    )
                    r.set_stroke(opacity=0.80)
                    r.move_to(pos[nd])
                    r.set_z_index(7)
                    rings.append(r)

                for r in rings:
                    self.add(r)
                self.play(
                    *[r.animate.scale(3.8).set_stroke(opacity=0.0)
                      for r in rings],
                    run_time=0.48, rate_func=rush_from,
                )
                for r in rings:
                    self.remove(r)

            # ── Milestone: giant ≥ 40 % ────────────────────────────────────
            if prev_snap.giant_fraction < 0.40 <= snap.giant_fraction:
                self.play(
                    *[node_cores[nd].animate.set_color(WHITE)
                      for nd in snap.giant_nodes],
                    run_time=0.27, rate_func=rush_into,
                )
                self.play(
                    *[node_cores[nd].animate.set_color(NODE_GIANT)
                      for nd in snap.giant_nodes],
                    run_time=0.27, rate_func=smooth,
                )
                cb = RoundedRectangle(
                    corner_radius=0.14, width=4.60, height=0.62,
                    stroke_color=NODE_GIANT, stroke_width=1.8,
                ).set_fill(PANEL_BG, opacity=0.98)
                ct = Text(
                    "⬡  GIANT COMPONENT  (S ≥ 40%)",
                    color=NODE_GIANT, font_size=17, weight=BOLD,
                )
                ct.move_to(cb)
                callout = VGroup(cb, ct)
                callout.move_to(GRAPH_CENTER + UP * 3.05)
                self.play(FadeIn(callout, scale=0.88), run_time=0.38)
                self.wait(1.15)
                self.play(FadeOut(callout), run_time=0.34)

            # ── Milestone: graph connected ─────────────────────────────────
            if not prev_snap.is_connected and snap.is_connected:
                # Flash burst on connectivity
                self.play(
                    Flash(
                        np.array(GRAPH_CENTER),
                        color=GREEN_VIV,
                        line_length=2.0,
                        num_lines=16,
                        flash_radius=3.5,
                        time_width=0.4,
                    ),
                    run_time=0.80,
                )
                cb = RoundedRectangle(
                    corner_radius=0.14, width=4.60, height=0.62,
                    stroke_color=GREEN_VIV, stroke_width=1.8,
                ).set_fill(PANEL_BG, opacity=0.98)
                ct = Text(
                    "✓  Graph is fully connected!",
                    color=GREEN_VIV, font_size=17, weight=BOLD,
                )
                ct.move_to(cb)
                callout = VGroup(cb, ct)
                callout.move_to(GRAPH_CENTER + UP * 3.05)
                self.play(FadeIn(callout, scale=0.88), run_time=0.38)
                self.wait(1.25)
                self.play(FadeOut(callout), run_time=0.34)

            self.wait(HOLD_T[snap.act])
            prev_snap    = snap
            prev_new_set = new_set
            prev_ncols   = ncols

        # ══════════════════════════════════════════════════════════════════
        #  ENDING — teal wash + formula card
        # ══════════════════════════════════════════════════════════════════
        self.play(
            *[node_cores[i].animate.set_color(NODE_GIANT) for i in range(n)],
            *[node_glows[i].animate.set_fill(GLOW_GIANT, opacity=0.30)
              for i in range(n)],
            *[node_cores[i].animate.set_stroke(color=GLOW_GIANT, opacity=0.90)
              for i in range(n)],
            *[ln.animate.set_stroke(color=EDGE_GIANT, opacity=0.55)
              for ln in edge_mobs.values()],
            graph_panel.animate.set_fill(ACT_PANEL[4][0], opacity=0.65),
            run_time=2.2, rate_func=smooth,
        )

        # Banner → ending message
        end_bg  = RoundedRectangle(
            corner_radius=0.20, width=8.85, height=0.68, stroke_width=0,
        ).set_fill(TEAL_MED, opacity=0.95)
        end_bg.to_edge(DOWN, buff=0.14).to_edge(LEFT, buff=0.22)
        end_txt = Text(
            "Random local edges  →  Global phase transition",
            color=WHITE, font_size=20, weight=BOLD,
        )
        end_txt.move_to(end_bg)
        self.play(
            Transform(banner_bg,  end_bg),
            Transform(banner_txt, end_txt),
            run_time=1.0,
        )

        # Formula card — large, centered over graph
        form_card = RoundedRectangle(
            corner_radius=0.25, width=7.40, height=2.10,
            stroke_color=GOLD, stroke_width=2.2,
        ).set_fill(PANEL_BG, opacity=0.98)
        form_card.move_to(GRAPH_CENTER)
        form_card.set_z_index(20)

        form_glow = RoundedRectangle(
            corner_radius=0.25, width=7.60, height=2.30,
            stroke_color=GOLD, stroke_width=5.0, stroke_opacity=0.15,
        ).set_fill(opacity=0)
        form_glow.move_to(GRAPH_CENTER)
        form_glow.set_z_index(19)

        formula = MathTex(
            r"S \;=\; 1 - e^{\,-\langle k\rangle \cdot S}",
            r"\quad\quad \langle k\rangle = p(n-1)",
            color=GOLD, font_size=34,
        )
        formula.move_to(form_card)
        formula.set_z_index(21)

        form_sub = Text(
            "Self-consistency equation  ·  branching-process prediction",
            color=DIM_TEXT, font_size=13,
        )
        form_sub.next_to(formula, DOWN, buff=0.20)
        form_sub.set_z_index(21)

        self.play(
            FadeIn(form_glow, run_time=0.6),
            FadeIn(form_card, run_time=0.7),
            Write(formula,    run_time=1.8),
            FadeIn(form_sub,  run_time=1.1),
        )
        self.wait(5.5)
