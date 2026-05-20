"""
utils.py
========
Shared utilities for Erdos-Renyi graph simulations and visualizations.

This module centralizes common helper functions used across multiple plot scripts,
eliminating code duplication and ensuring consistency.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import networkx as nx

# ── Consistent color palette across all visualizations ───────────────────────
# Core palette (used in Phase 2-4)
NAVY  = "#1A3A5C"
TEAL  = "#0E7490"
RED   = "#DC2626"
GOLD  = "#D97706"
SLATE = "#64748B"
LIGHT = "#F1F5F9"

# Extended palette (used in Phase 6)
PURPLE = "#7C3AED"
GREEN  = "#059669"
ROSE   = "#BE185D"

# Dark theme palette (used in Manim and Phase 6)
BG    = "#020617"
CARD  = "#0F172A"
DIM   = "#334155"

# ═══════════════════════════════════════════════════════════════════════════
# GRAPH ANALYSIS HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def component_sizes(adj: list[list[int]]) -> list[int]:
    """
    Compute all connected component sizes via BFS.

    Parameters
    ----------
    adj : list[list[int]]
        Adjacency list representation of the graph.

    Returns
    -------
    sizes : list[int]
        List of component sizes (unsorted).
    """
    n = len(adj)
    visited = bytearray(n)
    sizes = []

    for start in range(n):
        if not visited[start]:
            size = 0
            queue = deque([start])
            visited[start] = 1

            while queue:
                v = queue.popleft()
                size += 1
                for u in adj[v]:
                    if not visited[u]:
                        visited[u] = 1
                        queue.append(u)

            sizes.append(size)

    return sizes


def giant_fraction(adj: list[list[int]]) -> float:
    """
    Compute the fraction of nodes in the largest connected component.

    Parameters
    ----------
    adj : list[list[int]]
        Adjacency list representation of the graph.

    Returns
    -------
    fraction : float
        Fraction of nodes in the largest component (0 if empty graph).
    """
    n = len(adj)
    sizes = component_sizes(adj)
    return max(sizes) / n if sizes else 0.0


def count_edges(adj: list[list[int]]) -> int:
    """
    Count edges in an adjacency list representation.

    Each edge is stored twice (once for each endpoint), so we divide by 2.

    Parameters
    ----------
    adj : list[list[int]]
        Adjacency list representation of the graph.

    Returns
    -------
    m : int
        Number of edges.
    """
    return sum(len(nb) for nb in adj) // 2


def average_degree(adj: list[list[int]]) -> float:
    """
    Compute the average degree of the graph.

    Parameters
    ----------
    adj : list[list[int]]
        Adjacency list representation of the graph.

    Returns
    -------
    avg_deg : float
        Average degree (0 if empty graph).
    """
    n = len(adj)
    return sum(len(nb) for nb in adj) / n if n > 0 else 0.0


def component_sizes_nx(G: "nx.Graph") -> list[int]:
    """
    Compute all connected component sizes using NetworkX.

    Parameters
    ----------
    G : nx.Graph
        NetworkX graph object.

    Returns
    -------
    sizes : list[int]
        List of component sizes (unsorted).
    """
    import networkx as nx
    return [len(c) for c in nx.connected_components(G)]


def giant_fraction_nx(G: "nx.Graph") -> float:
    """
    Compute the fraction of nodes in the largest connected component.

    Parameters
    ----------
    G : nx.Graph
        NetworkX graph object.

    Returns
    -------
    fraction : float
        Fraction of nodes in the largest component (0 if empty graph).
    """
    import networkx as nx
    components = nx.connected_components(G)
    largest = max(components, key=len, default=set())
    return len(largest) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════
# THEORETICAL PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════

def theoretical_S(lam: float, tol: float = 1e-12, max_iter: int = 2000) -> float:
    """
    Solve the self-consistency equation S = 1 - exp(-λ·S) by fixed-point iteration.

    This equation arises from the Galton-Watson branching process analysis
    of the Erdős-Rényi phase transition.

    Parameters
    ----------
    lam : float
        Mean degree λ = ⟨k⟩ = (n-1)·p.
    tol : float
        Convergence tolerance.
    max_iter : int
        Maximum iterations.

    Returns
    -------
    S : float
        Giant component fraction (0 for λ ≤ 1).
    """
    if lam <= 1.0:
        return 0.0

    S = 0.5
    for _ in range(max_iter):
        S_new = 1.0 - np.exp(-lam * S)
        if abs(S_new - S) < tol:
            return S_new
        S = S_new

    return S


def er_clustering_prediction(n: int, m: int) -> float:
    """
    Compute the expected clustering coefficient for an ER graph.

    For G(n, m), the clustering coefficient C = p = 2m / (n(n-1)).

    Parameters
    ----------
    n : int
        Number of nodes.
    m : int
        Number of edges.

    Returns
    -------
    C : float
        Expected clustering coefficient.
    """
    if n <= 1:
        return 0.0
    return (2 * m) / (n * (n - 1))


def er_avg_path_length_prediction(n: int, k_mean: float) -> float:
    """
    Compute the expected average path length for an ER graph.

    Approximation: L ≈ ln(n) / ln(⟨k⟩) for ⟨k⟩ > 1.

    Parameters
    ----------
    n : int
        Number of nodes.
    k_mean : float
        Mean degree.

    Returns
    -------
    L : float
        Expected average path length (nan if k_mean ≤ 1).
    """
    import math
    if k_mean <= 1:
        return float("nan")
    return math.log(n) / math.log(k_mean)


# ═══════════════════════════════════════════════════════════════════════════
# MATPLOTLIB HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def setup_dark_theme() -> None:
    """
    Configure matplotlib for dark-themed plots.

    Call this before creating figures to apply the dark theme.
    """
    import matplotlib
    matplotlib.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    CARD,
        "axes.edgecolor":    DIM,
        "axes.labelcolor":   LIGHT,
        "xtick.color":       SLATE,
        "ytick.color":       SLATE,
        "text.color":        LIGHT,
        "grid.color":        DIM,
        "grid.linewidth":    0.5,
        "legend.facecolor":  CARD,
        "legend.edgecolor":  DIM,
    })


def setup_light_theme() -> None:
    """
    Configure matplotlib for light-themed plots.

    This is the default matplotlib theme.
    """
    import matplotlib
    matplotlib.rcParams.update({
        "figure.facecolor":  "#F8FAFC",
        "axes.facecolor":    LIGHT,
        "axes.edgecolor":    SLATE,
        "axes.labelcolor":   NAVY,
        "xtick.color":       SLATE,
        "ytick.color":       SLATE,
        "text.color":        NAVY,
        "grid.color":        "white",
        "grid.linewidth":    0.9,
        "legend.facecolor":  "white",
        "legend.edgecolor":  SLATE,
    })


def despine(ax: "plt.Axes", keep: tuple[str, ...] = ("left", "bottom")) -> None:
    """
    Remove spines from a matplotlib axes.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes to modify.
    keep : tuple[str, ...]
        Spines to keep (default: left and bottom).
    """
    for spine_name in ax.spines:
        if spine_name not in keep:
            ax.spines[spine_name].set_visible(False)

    for spine_name in keep:
        ax.spines[spine_name].set_color(DIM)


def apply_axes_style(ax: "plt.Axes", grid: bool = True, alpha: float = 0.25) -> None:
    """
    Apply consistent styling to a matplotlib axes.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes to style.
    grid : bool
        Whether to show grid.
    alpha : float
        Grid transparency.
    """
    ax.set_facecolor(CARD)
    despine(ax)

    if grid:
        ax.grid(True, alpha=alpha)

    for spine in ax.spines.values():
        spine.set_color(DIM)

    ax.tick_params(colors=SLATE, labelsize=10)


# ═══════════════════════════════════════════════════════════════════════════
# STATISTICAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def z_score_and_pvalue(value: float, ensemble: np.ndarray) -> tuple[float, float]:
    """
    Compute Z-score and two-tailed p-value.

    Parameters
    ----------
    value : float
        Observed value.
    ensemble : np.ndarray
        Null model ensemble.

    Returns
    -------
    z : float
        Z-score (standard deviations from ensemble mean).
    p : float
        Two-tailed p-value.
    """
    import scipy.stats as stats

    mu, sigma = ensemble.mean(), ensemble.std(ddof=1)

    if sigma == 0:
        return float("inf"), 0.0

    z = (value - mu) / sigma
    p = 2 * stats.norm.sf(abs(z))

    return z, p


def format_pvalue(p: float) -> str:
    """
    Format a p-value for display.

    Parameters
    ----------
    p : float
        P-value.

    Returns
    -------
    formatted : str
        Human-readable p-value string.
    """
    if p < 1e-300:
        return "< 1e-300 (effectively 0)"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


# ═══════════════════════════════════════════════════════════════════════════
# TIMING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def measure_timing(func, n: int, p: float, reps: int = 5) -> float:
    """
    Measure median execution time of a function.

    Parameters
    ----------
    func : callable
        Function to benchmark (should accept n, p arguments).
    n : int
        Graph size parameter.
    p : float
        Edge probability parameter.
    reps : int
        Number of repetitions.

    Returns
    -------
    median_time : float
        Median wall-clock time in seconds.
    """
    import time

    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        func(n, p)
        times.append(time.perf_counter() - t0)

    return float(np.median(times))
