# APEX — Evaluation Protocol & Scoring Rules

## 1. Evaluation Philosophy

In sports forecasting, predictive quality is multi-dimensional. A single point metric (such as classification accuracy) obscures whether a model produces well-calibrated probabilities, captures tail-risk retirements, or distinguishes subtle midfield position shifts.

APEX defines an explicit mapping between prediction targets and statistically appropriate evaluation metrics. Metrics are never indiscriminately forced onto incompatible targets.

---

## 2. Target-to-Metric Mapping

| Target Name | Target Mathematical Type | Primary Scoring Metric | Secondary Metrics | Inappropriate Metrics (Do Not Use) |
|---|---|---|---|---|
| **Race Winner** ($Y_{\text{win}}$) | Multi-class Categorical ($K \approx 20$) | **Multi-Class Log Loss** | Multi-Class Brier Score, Top-1 Accuracy, Top-3 Coverage | Mean Squared Error (MSE), Pearson Correlation |
| **Podium Finish** ($Y_{\text{podium}}$) | Multiple Binary / Subset of Size 3 | **Binary Brier Score** | Binary Log Loss, ROC-AUC, PR-AUC, Exact Set Match Rate | Continuous MAE, R-squared |
| **Top-10 Points Finish** ($Y_{\text{top10}}$) | Multiple Binary / Subset of Size 10 | **Binary Brier Score** | Binary Log Loss, PR-AUC, Precision@10 | Top-1 Accuracy, RMSE |
| **Full Finishing Order** ($\mathbf{r}$) | Permutation / Ordinal Ranking | **Finishing Position MAE** | Spearman’s Rank Correlation ($\rho$), Kendall’s Tau ($\tau$), NDCG@10 | Categorical Log Loss, Cross-Entropy |
| **Classified DNF / Retirement** | Sparse Binary ($P(\text{DNF}) \approx 0.15$) | **PR-AUC (Precision-Recall)** | Binary Brier Score, F-beta ($\beta=2$) | ROC-AUC (misleading on imbalanced data), Top-1 Accuracy |

---

## 3. Mathematical Metric Definitions

### 3.1 Multi-Class Log Loss (Cross-Entropy)
Penalizes confident incorrect predictions exponentially:
$$\mathcal{L}_{\text{LogLoss}} = - \frac{1}{M} \sum_{m=1}^M \sum_{i=1}^N y_{mi} \ln(p_{mi})$$
where $M$ is the number of evaluated races, $N$ is the number of drivers ($N=20$), $y_{mi} \in \{0, 1\}$ indicates whether driver $i$ won race $m$, and $p_{mi} \in (0, 1)$ is the model's assigned win probability.

### 3.2 Multi-Class Brier Score
Measures mean squared probability error:
$$\text{BS} = \frac{1}{M} \sum_{m=1}^M \sum_{i=1}^N (p_{mi} - y_{mi})^2$$
Brier score is strictly proper: it is uniquely minimized when predicted probabilities equal true underlying probabilities. Ranges from $0.0$ (perfect certainty) to $2.0$ (worst possible).

### 3.3 Expected Calibration Error (ECE)
Evaluates alignment between predicted probabilities and empirical event rates. Predictions are grouped into $B$ equally spaced probability bins $I_b = (\frac{b-1}{B}, \frac{b}{B}]$:
$$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{M} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$
where $\text{acc}(B_b)$ is the empirical win frequency in bin $b$, and $\text{conf}(B_b)$ is the average confidence assigned to predictions in bin $b$.

### 3.4 Finishing Position Mean Absolute Error (MAE)
Measures the average error in predicted finishing order:
$$\text{MAE}_{\text{pos}} = \frac{1}{N_{\text{classified}}} \sum_{i=1}^{N_{\text{classified}}} |\hat{r}_i - r_i^*|$$
Evaluated strictly on drivers classified as official race finishers (excluding DNFs from position error to avoid distortion).

---

## 4. Fair Chronological Comparison Protocol

To ensure valid out-of-sample comparisons between baseline models and candidate sequential models:

1. **Strict Timestamp Parity:** When comparing a baseline to a sequential checkpoint model at $T_4$ (Post-Qualifying), both models must evaluate the exact same test races with zero future data.
2. **Paired Statistical Significance Testing:**
   - Because Grand Prix rounds within a season are correlated, metric differences must be evaluated using the non-parametric **Paired Wilcoxon Signed-Rank Test** across races.
   - Null hypothesis: $\text{Median}(\Delta_{\text{metric}}) = 0$.
   - Significance threshold: $\alpha = 0.05$.
3. **Bootstrap Confidence Intervals:** For all aggregate metrics, report 95% confidence intervals generated via $B=2,000$ block-bootstrap resamples of Grand Prix rounds.
