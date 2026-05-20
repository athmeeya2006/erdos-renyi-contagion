"""
cascade.py
==========
Three cascade models on financial networks.

Model 1 - Bond percolation (structural):
    Remove each edge independently with prob (1-T).
    Cascade = giant component of connected banks collapses.
    Maps directly to plot11 SIR framework.

Model 2 - Threshold cascade (Watts 2002):
    Node i fails when fraction of failed neighbors >= threshold phi.
    Seed a single random failure. Measure cascade size.

Model 3 - DebtRank (Battiston et al. 2012):
    Economic-value cascade: node i transmits fraction of
    its liabilities-to-equity ratio to creditors.
    Measures systemic importance of each institution.
"""

import numpy as np
import networkx as nx
from collections import deque
from typing import Optional


def bond_percolation_cascade(G: nx.Graph, T: float,
                              seed: int = 42) -> float:
    """
    Bond percolation: each edge survives with prob T.
    Returns giant component fraction of surviving graph.
    Matches the SIR transmissibility framework from plot11.
    """
    rng = np.random.default_rng(seed)
    surviving_edges = [(u, v) for u, v in G.edges()
                       if rng.random() < T]
    H = nx.Graph()
    H.add_nodes_from(G.nodes())
    H.add_edges_from(surviving_edges)
    if H.number_of_nodes() == 0:
        return 0.0
    components = nx.connected_components(H)
    return len(max(components, key=len)) / H.number_of_nodes()


def threshold_cascade(G: nx.Graph, phi: float = 0.3,
                      n_seeds: int = 1,
                      seed: int = 42) -> dict:
    """
    Watts (2002) threshold model.
    
    Node fails when (failed neighbors / total neighbors) >= phi.
    
    Returns
    -------
    dict with:
        cascade_size : fraction of nodes that failed
        cascade_depth : number of rounds until no new failures
        failed_nodes : set of failed node ids
    """
    rng = np.random.default_rng(seed)
    n = G.number_of_nodes()
    nodes = list(G.nodes())
    
    failed = set(rng.choice(nodes, size=min(n_seeds, n), replace=False).tolist())
    
    depth = 0
    max_depth = n
    
    while depth < max_depth:
        new_failures = set()
        for node in nodes:
            if node in failed:
                continue
            neighbors = list(G.neighbors(node))
            if len(neighbors) == 0:
                continue
            frac_failed = sum(1 for nb in neighbors if nb in failed) / len(neighbors)
            if frac_failed >= phi:
                new_failures.add(node)
        
        if not new_failures:
            break
        failed |= new_failures
        depth += 1
    
    return {
        "cascade_size": len(failed) / n,
        "cascade_depth": depth,
        "failed_nodes": failed,
    }


def debt_rank(G: nx.Graph, shocked_nodes: list[int],
              shock_size: float = 1.0) -> dict:
    """
    DebtRank (Battiston et al. 2012, Scientific Reports).
    
    Measures systemic importance: total economic value lost
    from a shock to shocked_nodes.
    
    h_i(t) = economic distress level of node i in [0, 1]
    h_i(t+1) = min(1, h_i(t) + Sigma_j W_ji * h_j(t))
    
    where W_ji = (exposure of i to j) / (equity of i)
    
    Returns total impact: Sigma_i (h_i(T) - h_i(0)) * assets_i
    """
    nodes = list(G.nodes())
    n = len(nodes)
    node_idx = {nd: i for i, nd in enumerate(nodes)}
    
    # Build impact matrix W[i,j] = fraction of i's equity at risk from j
    W = np.zeros((n, n))
    for u, v, data in G.edges(data=True):
        exposure = data.get("weight", 0.0)
        i, j = node_idx[u], node_idx[v]
        eq_i = max(G.nodes[u].get("equity", 1.0), 1e-10)
        eq_j = max(G.nodes[v].get("equity", 1.0), 1e-10)
        W[i, j] = exposure / eq_i   # j's failure impacts i
        W[j, i] = exposure / eq_j   # i's failure impacts j
    
    # Initial distress
    h = np.zeros(n)
    for nd in shocked_nodes:
        if nd in node_idx:
            h[node_idx[nd]] = min(1.0, shock_size)
    
    h0 = h.copy()
    state = np.zeros(n)   # 0 = active, 1 = distressed (absorbing)
    state[h > 0] = 1
    
    # Propagate
    for _ in range(n):
        h_new = h.copy()
        for i in range(n):
            if state[i] == 1:
                continue
            impact = np.dot(W[i], h)
            h_new[i] = min(1.0, h[i] + impact)
            if h_new[i] > 0:
                state[i] = 1
        if np.allclose(h_new, h, atol=1e-10):
            break
        h = h_new
    
    # Total systemic impact = Sigma (h_i - h_i0) * A_i
    assets = np.array([G.nodes[nodes[i]].get("assets", 1.0) for i in range(n)])
    total_impact = float(np.dot(h - h0, assets))
    impact_fraction = float(np.mean(h - h0))
    
    return {
        "total_impact": total_impact,
        "impact_fraction": impact_fraction,
        "distress_vector": h,
        "n_failed": int(np.sum(h >= 1.0)),
    }


def sweep_threshold(G: nx.Graph, T_values: np.ndarray,
                    reps: int = 50, seed: int = 42) -> np.ndarray:
    """
    Sweep bond percolation threshold T and return mean giant fraction.
    Same API as the SIR transmissibility sweep in plot11.
    """
    S_mean = np.zeros(len(T_values))
    rng_seeds = np.random.default_rng(seed).integers(0, 2**31, size=len(T_values) * reps)
    idx = 0
    for i, T in enumerate(T_values):
        samples = []
        for _ in range(reps):
            samples.append(bond_percolation_cascade(G, T, seed=int(rng_seeds[idx])))
            idx += 1
        S_mean[i] = np.mean(samples)
    return S_mean
