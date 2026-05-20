"""
plot16_financial_contagion.py
==============================
Financial Contagion via Percolation on ER vs BA Networks
Outputs: plot16_financial_contagion.png

Results:
  Panel A: Bond percolation cascade size vs transmissibility T
           ER vs BA - maps to plot11 SIR framework
  Panel B: Threshold cascade size vs phi (failure threshold)
           Shows BA collapses at lower phi than ER
  Panel C: DebtRank systemic importance distribution
           BA: hub nodes carry disproportionate systemic risk
  Panel D: Phase diagram (T, equity_ratio) - safe vs crisis region
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.financial_network import generate_financial_er, generate_financial_ba
from src.cascade import bond_percolation_cascade, threshold_cascade, debt_rank, sweep_threshold

# Colors
NAVY   = "#1A3A5C"
TEAL   = "#0E7490"
RED    = "#DC2626"
GOLD   = "#D97706"
SLATE  = "#64748B"
LIGHT  = "#F1F5F9"

N = 1000
K = 4
M_BA = K // 2
SEED = 42

def panel_a_percolation(ax):
    T_vals = np.linspace(0.0, 1.0, 21)
    
    G_er = generate_financial_er(N, K, seed=SEED)
    G_ba = generate_financial_ba(N, M_BA, seed=SEED)
    
    S_er = sweep_threshold(G_er, T_vals, reps=10, seed=SEED)
    S_ba = sweep_threshold(G_ba, T_vals, reps=10, seed=SEED)
    
    ax.plot(T_vals, S_er, "o-", color=TEAL, label="ER (Homogeneous)")
    ax.plot(T_vals, S_ba, "s-", color=RED, label="BA (Scale-free)")
    
    ax.axvline(1.0/K, color=GOLD, linestyle="--", label="ER Theory T_c = 1/<k>")
    
    ax.set_xlabel("Transmissibility T (counterparty default prob)")
    ax.set_ylabel("Cascade Size (Giant Fraction)")
    ax.set_title("Panel A: Bond Percolation Cascade")
    ax.legend()
    ax.grid(True, alpha=0.3)

def panel_b_threshold(ax):
    phi_vals = np.linspace(0.05, 0.5, 20)
    
    G_er = generate_financial_er(N, K, seed=SEED)
    G_ba = generate_financial_ba(N, M_BA, seed=SEED)
    
    reps = 10
    S_er = np.zeros(len(phi_vals))
    S_ba = np.zeros(len(phi_vals))
    
    rng = np.random.default_rng(SEED)
    
    for i, phi in enumerate(phi_vals):
        er_vals = []
        ba_vals = []
        for _ in range(reps):
            seed_node = int(rng.integers(0, 100000))
            er_res = threshold_cascade(G_er, phi=phi, seed=seed_node)
            ba_res = threshold_cascade(G_ba, phi=phi, seed=seed_node)
            er_vals.append(er_res["cascade_size"])
            ba_vals.append(ba_res["cascade_size"])
        S_er[i] = np.mean(er_vals)
        S_ba[i] = np.mean(ba_vals)
        
    ax.plot(phi_vals, S_er, "o-", color=TEAL, label="ER")
    ax.plot(phi_vals, S_ba, "s-", color=RED, label="BA")
    
    ax.set_xlabel(r"Failure Threshold $\phi$")
    ax.set_ylabel("Cascade Size (Fraction of failed nodes)")
    ax.set_title("Panel B: Watts Threshold Cascade")
    ax.legend()
    ax.grid(True, alpha=0.3)

def panel_c_debtrank(ax):
    G_er = generate_financial_er(N, K, seed=SEED)
    G_ba = generate_financial_ba(N, M_BA, seed=SEED)
    
    dr_er = []
    dr_ba = []
    
    for G, dr_list in [(G_er, dr_er), (G_ba, dr_ba)]:
        degrees = dict(G.degree())
        nodes = list(G.nodes())
        sorted_nodes = sorted(nodes, key=lambda n: degrees[n], reverse=True)
        sample = sorted_nodes[:20] + list(np.random.choice(nodes, 20, replace=False))
        for n_i in set(sample):
            res = debt_rank(G, [n_i])
            dr_list.append((degrees[n_i], res["total_impact"]))
            
    dr_er = np.array(dr_er)
    dr_ba = np.array(dr_ba)
    
    ax.scatter(dr_er[:, 0], dr_er[:, 1], color=TEAL, alpha=0.7, label="ER")
    ax.scatter(dr_ba[:, 0], dr_ba[:, 1], color=RED, alpha=0.7, label="BA")
    
    ax.set_xlabel("Node Degree")
    ax.set_ylabel("DebtRank (Total Impact)")
    ax.set_title("Panel C: DebtRank vs Degree")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)

def panel_d_phase(ax):
    T_vals = np.linspace(0.1, 0.9, 10)
    eq_vals = np.linspace(0.02, 0.15, 10)
    
    Z = np.zeros((len(eq_vals), len(T_vals)))
    
    for i, eq in enumerate(eq_vals):
        G_er = generate_financial_er(N, K, equity_ratio=eq, seed=SEED)
        Z[i, :] = sweep_threshold(G_er, T_vals, reps=3, seed=SEED)
        
    im = ax.imshow(Z, origin="lower", extent=[T_vals[0], T_vals[-1], eq_vals[0], eq_vals[-1]],
                   aspect="auto", cmap="viridis")
    
    plt.colorbar(im, ax=ax, label="Cascade Size")
    ax.set_xlabel("Transmissibility T")
    ax.set_ylabel("Equity Ratio")
    ax.set_title("Panel D: Phase Diagram (ER)")

def main():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor(LIGHT)
    
    panel_a_percolation(axes[0, 0])
    panel_b_threshold(axes[0, 1])
    panel_c_debtrank(axes[1, 0])
    panel_d_phase(axes[1, 1])
    
    plt.tight_layout()
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "media", "figures"), exist_ok=True)
    plt.savefig(os.path.join(os.path.dirname(__file__), "..", "media", "figures", "plot16_financial_contagion.png"), dpi=150)
    print("Saved: plot16_financial_contagion.png")

if __name__ == "__main__":
    main()
