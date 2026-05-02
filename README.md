# Erdős–Rényi Random Graph Evaluation

> **Complex Networks, Percolation Theory & Dynamical Systems** · Hyderabad, India

Large-scale Monte Carlo evaluation of the Erdős–Rényi $G(n, p)$ random graph model — from algorithmic generation through critical phenomena to real-world null-model rejection. This repository contains the codebase, simulations, and visualizations supporting an upcoming research manuscript on dynamical phase transitions in graph networks.

---

## Research Context

This project investigates the conditions under which complex networks undergo **irreversible dynamical phase transitions** — the sudden emergence of macroscopic structure from local randomness. The Erdős–Rényi model serves as the canonical mean-field framework for studying:

- **Percolation thresholds** — the critical edge probability $p_c = 1/n$ at which a giant connected component spontaneously emerges, directly analogous to second-order phase transitions in statistical physics.
- **Structural balance theory** — how signed edge weights influence the equilibrium configurations of complex networks.
- **Large-scale connectivity collapse** — mathematical models connecting percolation threshold behavior to network fragmentation under attack.

### Key Results

| Result | Description |
|--------|-------------|
| **$s^{-3/2}$ Power Law** | Empirically confirmed the cluster-size power-law exponent at the percolation threshold across 1,000+ Monte Carlo iterations with up to 10,000 vertices — the hallmark of mean-field percolation criticality. |
| **Phase Transition Curve** | Giant component fraction $S(p)$ matches the self-consistency equation $S = 1 - e^{-\lambda S}$ from Galton–Watson branching process theory. |
| **Finite-Size Scaling** | Transition width $\Delta\lambda \sim n^{-1/3}$ verified empirically, confirming the mean-field finite-size scaling exponent. |
| **Epidemic Threshold** | SIR epidemic spreading is equivalent to bond percolation with transmissibility $T = \beta/(\beta + \gamma - \beta\gamma)$, with epidemic threshold at $\langle k \rangle_c = 1/T$. |
| **Null-Model Rejection** | S&P 500 correlation network and synthetic brain connectome both rejected the ER null hypothesis at $Z > 30\sigma$ for clustering, confirming non-random mesoscale structure. |

---

## Architecture

```
erdos-graph/
├── fast_er.py                       # Batagelj–Brandes O(n + M) generator
├── naive_er.py                      # Baseline O(n²) generator
├── utils.py                         # Shared analysis & visualization utilities
├── requirements.txt                 # Python dependencies
│
├── Phase 2 — Algorithmic Efficiency
│   ├── plot1.py                     # Runtime benchmark (naive vs fast)
│   ├── plot2.py                     # Speedup ratio analysis
│   ├── plot3.py                     # Degree distribution validation
│   ├── plot4.py                     # Iteration count comparison
│   └── plot5.py                     # Fast generator scaling analysis
│
├── Phase 3 — Phase Transition & Critical Phenomena
│   ├── plot6_degree_distribution_phase3.py
│   ├── plot7_phase_transition_curve.py     # S vs ⟨k⟩ with theory overlay
│   ├── plot8_cluster_size_powerlaw.py      # s^{-3/2} power-law verification
│   └── plot9_finite_size_scaling.py        # Δλ ~ n^{-1/3} scaling
│
├── Phase 4 — Dynamical Processes on Networks
│   ├── plot11_sir_epidemic.py              # SIR epidemic spreading
│   └── plot15_network_resilience.py        # Attack tolerance (ER vs BA)
│
├── Phase 5 — Cinematic Visualization
│   ├── plot12_er_evolution_video.py        # Manim animation (YouTube quality)
│   └── Plot12ErdosRenyiEvolution.mp4       # Rendered video
│
└── Phase 6 — Real-World Null-Model Rejection
    ├── plot13_real_world_mapping.py         # S&P 500 correlation network
    └── plot14_brain_connectivity.py         # Synthetic brain connectome
```

---

## Phase Breakdown

### Phase 2 · Algorithmic Efficiency & Complexity

Implements and benchmarks two $G(n, p)$ generators:

- **Naive generator** (`naive_er.py`) — $O(n^2)$ Bernoulli coin-flip over all $\binom{n}{2}$ pairs.
- **Batagelj–Brandes generator** (`fast_er.py`) — $O(n + M)$ geometric-skip algorithm. Labels each potential edge with a flat index, then samples $\text{Geometric}(p)$ skips to jump directly to included edges without wasted iterations.

The fast generator handles $n = 500{,}000$ in seconds where the naive approach would require $\sim 125$ billion coin flips.

### Phase 3 · Structural Simulations & Phase Transitions

Monte Carlo simulations confirming the three classical predictions of Erdős–Rényi theory:

1. **Giant component emergence** — At $p_c = 1/n$ (equivalently $\langle k \rangle = 1$), a giant connected component containing $\Theta(n)$ vertices appears. The self-consistency equation $S = 1 - e^{-\lambda S}$ from Galton–Watson branching process analysis perfectly predicts the empirical fraction.

2. **Cluster-size power law** — Exactly at the critical point, finite component sizes follow $P(s) \sim s^{-3/2}$. Verified via OLS regression in log-log space across 30 pooled realizations with $n = 40{,}000$ nodes.

3. **Finite-size scaling** — The transition window width scales as $\Delta\lambda \sim n^{-1/3}$, confirming the mean-field universality class. Demonstrated with $n \in \{100,\ 1{,}000,\ 10{,}000\}$ at 60 realizations each.

### Phase 4 · Dynamical Processes on Networks

Explores how the structural phase transition controls dynamical phenomena:

- **Network resilience** (`plot15`) — Compares random failure vs. targeted hub removal on ER (Poisson degree distribution) and Barabási–Albert (power-law) graphs. ER shows symmetric response (no hubs to exploit); BA collapses under targeted attack — the Achilles' heel of scale-free networks.

- **SIR epidemic spreading** (`plot11`) — Discrete-time SIR model on ER graphs. Proves that the epidemic threshold is governed by the effective mean degree $\lambda_{\text{eff}} = \langle k \rangle \cdot T$ where $T = \beta / (\beta + \gamma - \beta\gamma)$ is the transmissibility. Below $\lambda_{\text{eff}} = 1$, epidemics die out; above, pandemic waves emerge — mathematically equivalent to bond percolation.

### Phase 5 · Cinematic Manim Animation

A publication-quality animated video (`plot12_er_evolution_video.py`) rendering the complete $G(n, p)$ phase transition in four acts:

| Act | Description |
|-----|-------------|
| I   | Isolated nodes materialize in a starfield |
| II  | Small clusters form with rainbow coloring and live component count |
| III | Critical point $p_c = 1/n$ — flash shockwave, giant component emerges |
| IV  | Connectivity threshold $p^* = \ln(n)/n$ — full graph connectivity achieved |

Features a live $S(p)$ mini-plot with theory overlay, progress bar, and HUD metrics.

### Phase 6 · Real-World Null-Model Rejection

Tests whether real-world networks are structurally distinguishable from ER random graphs:

- **S&P 500 correlation network** (`plot13`) — Constructs a Pearson correlation network from 3 years of daily log-returns across ~100 stocks (5 GICS sectors). Thresholds at $|\rho| > 0.50$. Compares clustering coefficient, average path length, and degree assortativity against a 1,000-graph ER ensemble. Result: **$H_0$ rejected** — the real network exhibits community structure, heavy-tailed degree distribution, and small-world properties absent from ER.

- **Brain connectivity analysis** (`plot14`) — Generates a synthetic 90-region connectome modeled on the AAL atlas with 9 cortical/subcortical modules, rich-club hub topology, and log-normal connection weights matching DTI literature. Simulates diffusion-based signal propagation ($x(t+1) = \alpha D^{-1}Ax(t) + (1-\alpha)x(t)$) across brain, ER, and ring lattice architectures. The brain's small-world structure enables significantly faster signal spreading than either random or regular topologies.

---

## Tech Stack

| Tool | Role |
|------|------|
| **Python 3.10+** | Core language |
| **NetworkX** | Graph construction, component analysis, centrality metrics |
| **NumPy / SciPy** | Linear algebra, statistical testing, distributions |
| **Matplotlib** | All static visualizations with custom dark/light themes |
| **Manim** | Cinematic phase-transition animation |
| **pandas / yfinance** | Financial data loading for S&P 500 analysis |

---

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

Each script is self-contained. Run any phase directly:

```bash
# Phase 2 — Benchmarks
python3 plot1.py
python3 plot2.py

# Phase 3 — Phase transition & critical phenomena
python3 plot7_phase_transition_curve.py
python3 plot8_cluster_size_powerlaw.py
python3 plot9_finite_size_scaling.py

# Phase 4 — Dynamical processes
python3 plot11_sir_epidemic.py
python3 plot15_network_resilience.py

# Phase 6 — Real-world null-model rejection
python3 plot13_real_world_mapping.py
python3 plot14_brain_connectivity.py
```

Render the Manim animation:

```bash
manim -qm plot12_er_evolution_video.py Plot12ErdosRenyiEvolution   # medium quality
manim -qh plot12_er_evolution_video.py Plot12ErdosRenyiEvolution   # high quality
```

## Phase 6 Data

`plot13_real_world_mapping.py` prefers a local CSV cache before attempting a live Yahoo Finance download.

- **Default cache path:** `data/sp500_adj_close.csv`
- **Override with:** `ERDOS_PRICE_DATA=/path/to/file.csv`

The CSV should contain adjusted close prices with a date index in the first column and ticker symbols as column headers. If no cache is found, the script downloads via `yfinance` and saves the result for future offline runs.

## Outputs

All generated figures (`.png`) and videos (`.mp4`) are written to the project root. Key outputs include:

| File | Description |
|------|-------------|
| `plot1_runtime_benchmark.png` | Naive vs fast generator timing |
| `plot7_phase_transition_curve.png` | $S$ vs $\langle k \rangle$ with theory |
| `plot8_cluster_size_powerlaw.png` | $P(s) \sim s^{-3/2}$ verification |
| `plot9_finite_size_scaling.png` | $\Delta\lambda \sim n^{-1/3}$ scaling law |
| `plot11_sir_epidemic.png` | SIR epidemic dynamics |
| `plot13d_summary_dashboard.png` | S&P 500 null-model rejection dashboard |
| `plot14d_brain_dashboard.png` | Brain connectivity analysis dashboard |
| `plot15_network_resilience.png` | ER vs BA attack tolerance |
| `Plot12ErdosRenyiEvolution.mp4` | Phase transition animation |

---

## References

- Erdős, P. & Rényi, A. (1959). "On Random Graphs I." *Publicationes Mathematicae*, 6, 290–297.
- Batagelj, V. & Brandes, U. (2005). "Efficient Generation of Large Random Networks." *Physical Review E*, 71(3), 036113.
- Bollobás, B. (2001). *Random Graphs*. Cambridge University Press.
- Newman, M.E.J. (2010). *Networks: An Introduction*. Oxford University Press.
- Barabási, A.-L. & Albert, R. (1999). "Emergence of Scaling in Random Networks." *Science*, 286(5439), 509–512.
- Honey, C.J. et al. (2009). "Predicting human resting-state functional connectivity from structural connectivity." *PNAS*, 106(6), 2035–2040.
- Sporns, O. (2010). *Networks of the Brain*. MIT Press.

---

<p align="center">
  <em>Part of ongoing research in complex networks and dynamical phase transitions.</em><br>
  <em>Manuscript in preparation.</em>
</p>
