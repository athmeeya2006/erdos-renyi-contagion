# Erdős-Rényi Random Graph Evaluation

A large-scale Monte Carlo evaluation of the Erdős-Rényi $G(n, p)$ random graph model. This repository implements algorithmic generation protocols, evaluates macroscopic critical phenomena, and applies the framework as a null model to real-world topologies (financial markets and synthetic brain connectomes).

---

## 1. Core Implementations & Algorithmic Complexity

Generating large, sparse Erdős-Rényi graphs computationally is non-trivial. This project implements and rigorously benchmarks two fundamental graph generation algorithms, highlighting a massive difference in computational efficiency for sparse networks (constant average degree $\lambda$, where $p = \lambda/n$).

### **The Naïve Generator**
- **Complexity**: $O(n^2)$
- **Mechanics**: Evaluates a Bernoulli coin-flip for every possible pair of vertices. For $n$ vertices, this requires exactly $\binom{n}{2} = \frac{n(n-1)}{2}$ operations. 

### **The Batagelj-Brandes Fast Generator**
- **Complexity**: $O(n + M)$, where $M$ is the number of realized edges.
- **Mechanics**: Rather than flipping a coin for every possible edge, the algorithm mathematically skips sequences of non-edges. It samples the "skip distance" $d$ to the next realized edge directly from a Geometric distribution $d \sim \text{Geom}(p)$. This effectively removes the need to process any non-edges, driving the runtime down to the theoretical lower bound.

### **Quantitative Performance Improvements**
The Batagelj-Brandes implementation yields profound asymptotic improvements:
- **Speedup Scaling**: The speedup ratio formally scales as $O(n/\lambda)$. Because the naïve algorithm scales quadratically and the fast algorithm scales linearly, the gap widens indefinitely as $n$ increases.
- **Empirical Benchmarks ($n=10,000$)**: The fast generator runs approximately **1,000× faster** than the naïve implementation.
- **Large-Scale Capability ($n=500,000$)**: The naïve approach would require evaluating exactly **125 billion** potential edges (taking hours or days on standard hardware). The Batagelj-Brandes implementation completes this generation in a fraction of a second, reflecting an estimated theoretical speedup of over **$50,000\times$**.

---

## 2. Project Structure

The codebase has been refactored for professional clarity and reproducibility.

```text
erdos-graph/
├── src/                             # Core algorithms and utilities
│   ├── fast_er.py                   # Batagelj-Brandes O(n + M) generator
│   ├── naive_er.py                  # Baseline O(n²) generator
│   ├── utils.py                     # Shared analytical/graphing utilities
│   ├── financial_network.py         # Bank balance sheet network models
│   └── cascade.py                   # Financial contagion models
├── scripts/                         # Experiments, benchmarks, and simulation suites
│   ├── plot1.py                     # Runtime benchmark: naive vs fast
│   ├── plot2.py                     # Speedup ratio tracking
│   ├── plot7_phase_transition_curve.py  # S vs ⟨k⟩ critical point mapping
│   ├── plot8_cluster_size_powerlaw.py   # s^{-3/2} component size scaling
│   ├── plot9_finite_size_scaling.py     # Δλ ~ n^{-1/3} transition window
│   ├── plot11_sir_epidemic.py           # SIR epidemic spreading processes
│   ├── plot12_er_evolution_video.py     # Manim animation script
│   ├── plot13_real_world_mapping.py     # S&P 500 vs ER null model
│   ├── plot14_brain_connectivity.py     # Brain connectome analysis
│   ├── plot15_network_resilience.py     # Attack tolerance (ER vs BA networks)
│   └── plot16_financial_contagion.py    # Systemic risk and cascading failures
├── media/                           # Pipeline outputs
│   ├── figures/                     # Statistical plots and dashboards (.png)
│   └── videos/                      # Manim renders (.mp4)
├── data/                            # Persistent local caches (e.g., Yahoo Finance)
├── requirements.txt                 # Project dependencies
├── .gitignore                       # Git ignore list
└── README.md
```

---

## 3. Theoretical Framework & Critical Phenomena

The project validates classical random graph theory through extensive, pooled Monte Carlo simulations:

### **Giant Component Emergence**
At the critical probability threshold $p_c = 1/n$ (equivalently, an average degree $\langle k \rangle = 1$), a macroscopic connected component forms. The empirical fraction of nodes in this giant component $S$ perfectly matches the Galton-Watson branching process self-consistency equation:
$$S = 1 - e^{-\lambda S}$$

### **Cluster-Size Power Law**
Exactly at the percolation threshold ($p = 1/n$), the random graph exists in a critical state. The distribution of sizes $s$ for finite components follows a strict power law:
$$P(s) \sim s^{-3/2}$$
This was validated via Ordinary Least Squares (OLS) regression in log-log space over 30 realizations of massive graphs ($n=40,000$).

### **Finite-Size Scaling**
In finite graphs, the phase transition from isolated clusters to a giant component is not instantaneous. The width of this critical transition window $\Delta\lambda$ scales inversely with the system size according to the mean-field exponent:
$$\Delta\lambda \sim n^{-1/3}$$
This scaling law was empirically proven by tracking the variance of the giant component size across ensembles of $n \in \{100, 1000, 10000\}$.

---

## 4. Dynamical Processes on Networks

### **Network Resilience (ER vs. Scale-Free)**
We compare the structural resilience of Erdős-Rényi graphs (Poisson degree distribution) against Barabási-Albert graphs (power-law degree distribution) under random node failure and targeted hub attacks.
- **Symmetric Degradation in ER**: Because ER graphs lack "mega-hubs" (a consequence of the rapidly decaying Poisson tail), targeting the highest-degree nodes is virtually no more damaging than removing nodes entirely at random.
- **The Achilles' Heel of Scale-Free Networks**: Barabási-Albert networks are heavily reliant on a few massive hubs. While they survive random failures better than ER graphs, a targeted attack on these hubs causes the giant component to completely shatter and collapse when just $\sim 15\%$ of nodes are removed.

### **SIR Epidemic Spreading**
Simulating a discrete-time Susceptible-Infected-Recovered epidemic on ER topologies reveals a direct mapping to bond percolation. The transmissibility $T$ (probability a disease transverses an edge before recovery) is defined as:
$$T = \frac{\beta}{\beta + \gamma - \beta\gamma}$$
A global pandemic only emerges when the effective mean degree exceeds the critical threshold:
$$\lambda_{\mathrm{eff}} = \langle k \rangle \cdot T > 1$$

### **Financial Contagion & Systemic Risk (`plot16_financial_contagion.py`)**
We model interconnected financial institutions with dynamic balance sheets, tracking how counterparty default propagates across the interbank network. This extends the existing pure-structural resilience work by introducing actual economic models of contagion:

- **`src/financial_network.py`**: Generates synthetic interbank networks (both Erdős-Rényi and Barabási-Albert). Each bank is initialized with a balance sheet containing assets, liabilities, and an equity buffer. Interbank exposures form the weighted edges of the network.
- **`src/cascade.py`**: Implements three separate cascade transmission protocols that model different mechanisms of systemic failure:
  1. **Bond Percolation Cascade**: A purely structural failure propagation mirroring the SIR epidemic model. Each exposure link survives failure with a transmissibility probability $T$.
  2. **Watts Threshold Cascade (2002)**: A behavioral and balance-sheet threshold model. A node fails if the fraction of its failed neighbors exceeds a critical threshold $\phi$. 
  3. **DebtRank (Battiston et al., 2012)**: An economic-value cascade model that measures the systemic importance of each institution based on how a shock to its equity propagates recursively through its creditors.

**Empirical Results (Plot 16 Panels):**
- **Panel A (Bond Percolation)**: The structural contagion threshold on Erdős-Rényi networks exactly matches the theoretical $T_c = 1/\langle k \rangle$. Below this threshold, cascades are strictly contained; above it, a giant component of failed banks emerges.
- **Panel B (Threshold Cascades)**: Comparing ER against Barabási-Albert (BA) networks under the Watts threshold model reveals that BA scale-free networks collapse at a significantly lower failure threshold $\phi$. 
- **Panel C (DebtRank vs. Degree)**: DebtRank analysis shows that "mega-hubs" in BA networks carry vastly disproportionate systemic risk compared to nodes in ER networks, quantitatively demonstrating the "Too Connected to Fail" paradigm.
- **Panel D (Phase Diagram)**: A 2D heatmap tracking cascade size across two dimensions: Transmissibility $T$ and Equity Ratio. It clearly delineates the "safe" operating region from the systemic "crisis" region, proving that higher capital requirements (equity buffers) directly shift the critical phase transition boundary.

---

## 5. Real-World Topologies vs. ER Null Models

Erdős-Rényi random graphs serve as the ultimate null hypothesis. By generating 1,000 equivalent ER graphs (matching the exact $N$ and $M$ of a real-world dataset), we can compute $Z$-scores to prove whether real networks exhibit structures that cannot arise by pure chance.

### **S&P 500 Correlation Network**
- **Methodology**: Pearson correlations were computed over 3 years of daily log-returns from Yahoo Finance across 5 GICS sectors (Tech, Finance, Healthcare, Energy, Consumer). Edges were formed at a threshold of $|\rho| > 0.50$.
- **Statistical Rejection**: The S&P 500 network exhibits profound community structure, yielding a clustering coefficient $C$ that generates a $Z$-score of **$> 30\sigma$** compared to the ER ensemble. The null hypothesis is decisively rejected, proving the existence of non-random, heavy-tailed financial clustering.

### **Synthetic Brain Connectome (AAL Atlas)**
- **Methodology**: Modeled a 90-region connectome based on the Automated Anatomical Labeling (AAL) atlas. It features 9 cortical/subcortical modules with an intra-module density of $55\%$, an inter-module density of $4\%$, and 15 rich-club hubs with log-normal connection weights.
- **Signal Propagation**: Simulated diffusion-based signal propagation using a discrete random-walk model:
$$x(t+1) = \alpha D^{-1}A x(t)  +  (1-\alpha) x(t)$$
- **Results**: Side-by-side spreading speed comparisons reveal that the small-world, modular architecture of the brain integrates signals drastically faster than equivalently dense ER or regular ring-lattice networks.

---

## 6. Setup and Execution

### **Installation**
Create a virtual environment and install the dependencies (`NetworkX`, `NumPy`, `SciPy`, `Matplotlib`, `Manim`, `yfinance`):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Running Simulations**
Scripts dynamically resolve `sys.path`, allowing direct execution. Output artifacts are automatically saved to `media/figures/`.

```bash
# Algorithmic Scaling & Benchmarks
python scripts/plot1.py
python scripts/plot2.py

# Phase Transition & Percolation
python scripts/plot7_phase_transition_curve.py
python scripts/plot8_cluster_size_powerlaw.py

# Epidemics & Resilience
python scripts/plot11_sir_epidemic.py
python scripts/plot15_network_resilience.py
python scripts/plot16_financial_contagion.py

# Real-world data analysis
python scripts/plot13_real_world_mapping.py
python scripts/plot14_brain_connectivity.py
```

### **Video Rendering (Phase 5)**
To generate the animated Erdős-Rényi phase transition using Manim:
```bash
manim -qm scripts/plot12_er_evolution_video.py Plot12ErdosRenyiEvolution
```

---

## 7. References
- Erdős, P. & Rényi, A. (1959). *On Random Graphs I.* Publicationes Mathematicae, 6, 290-297.
- Batagelj, V. & Brandes, U. (2005). *Efficient Generation of Large Random Networks.* Physical Review E, 71(3), 036113.
- Honey, C.J. et al. (2009). *Predicting human resting-state functional connectivity from structural connectivity.* PNAS, 106(6).
- Newman, M.E.J. (2010). *Networks: An Introduction.* Oxford University Press.
- Bollobás, B. (2001). *Random Graphs.* Cambridge University Press.
- Barabási, A.-L. & Albert, R. (1999). *Emergence of Scaling in Random Networks.* Science.
