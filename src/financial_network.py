"""
financial_network.py
====================
Bank node model with balance sheets for cascade simulation.

Each node = a financial institution with:
  - assets A_i
  - liabilities L_i  
  - equity buffer e_i = A_i - L_i  (absorbs losses before default)
  - interbank exposures: edges with weight = bilateral exposure size

Network types:
  - ER:  homogeneous institution sizes
  - BA:  heavy-tailed institution sizes (hubs = systemically important banks)
"""

import numpy as np
import networkx as nx
from dataclasses import dataclass


@dataclass
class BankNode:
    assets: float
    liabilities: float
    equity: float          # = assets - liabilities
    is_failed: bool = False

    @property
    def leverage(self) -> float:
        return self.assets / max(self.equity, 1e-10)

    def absorb_loss(self, loss: float) -> float:
        """Apply loss to equity. Returns spillover (loss beyond equity)."""
        if self.is_failed:
            return loss
        self.equity -= loss
        if self.equity <= 0:
            self.is_failed = True
            return abs(self.equity)   # spillover to creditors
        return 0.0


def generate_financial_er(n: int, mean_k: float,
                           equity_ratio: float = 0.08,
                           asset_scale: float = 1.0,
                           seed: int = 42) -> nx.Graph:
    """
    ER financial network with homogeneous balance sheets.
    
    equity_ratio = e_i / A_i  (Basel III minimum ~8%)
    Edge weight = bilateral exposure drawn from Exp(1/mean_exposure).
    """
    rng = np.random.default_rng(seed)
    p = mean_k / (n - 1)
    G = nx.erdos_renyi_graph(n, p, seed=seed)

    for i in G.nodes():
        A = float(rng.lognormal(np.log(asset_scale), 0.3))
        e = equity_ratio * A
        G.nodes[i].update({"assets": A, "liabilities": A - e,
                           "equity": e, "is_failed": False})

    for u, v in G.edges():
        w = float(rng.exponential(asset_scale * 0.05))
        G[u][v]["weight"] = w

    return G


def generate_financial_ba(n: int, m: int,
                           equity_ratio: float = 0.08,
                           seed: int = 42) -> nx.Graph:
    """
    BA scale-free financial network.
    Hub nodes (high degree) have larger balance sheets — 
    assets proportional to degree (too-big-to-fail structure).
    """
    rng = np.random.default_rng(seed)
    G = nx.barabasi_albert_graph(n, m, seed=seed)

    degrees = dict(G.degree())
    mean_deg = np.mean(list(degrees.values()))

    for i in G.nodes():
        # Larger institutions have more connections (empirically realistic)
        size_factor = degrees[i] / mean_deg
        A = float(rng.lognormal(np.log(size_factor), 0.4))
        e = equity_ratio * A
        G.nodes[i].update({"assets": A, "liabilities": A - e,
                           "equity": e, "is_failed": False})

    for u, v in G.edges():
        avg_assets = (G.nodes[u]["assets"] + G.nodes[v]["assets"]) / 2
        w = float(rng.exponential(avg_assets * 0.05))
        G[u][v]["weight"] = w

    return G
