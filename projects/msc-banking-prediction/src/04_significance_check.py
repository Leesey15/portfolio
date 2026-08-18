"""
Bootstrap confidence intervals on ROC-AUC per window, to confirm the
diminishing-returns pattern (30->90 flat, 90->180 jump, 180->365 further but
smaller gain) is real and not noise from a single train/test split.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings("ignore")

base = pd.read_pickle("base_accounts.pkl")[["account_id", "account_open_date"]]

FINANCIAL_COLS = [
    "txn_count", "avg_txn_amount", "std_txn_amount", "total_amount",
    "avg_balance", "min_balance", "max_balance", "ending_balance",
    "n_unique_operations", "n_days_active", "credit_amount", "debit_amount",
    "net_flow", "balance_trend", "txn_count_per_day", "active_day_ratio",
    "has_loan_in_window", "avg_salary", "unemployment_95", "unemployment_96",
    "urban_ratio_pct", "entrepreneurs_per_1000", "n_inhabitants",
]
BEHAVIORAL_COLS = ["interval_cv", "habit_strength", "breadth_growth", "txn_trend", "amount_trend"]
FEATURE_COLS = FINANCIAL_COLS + BEHAVIORAL_COLS

N_BOOTSTRAP = 200
rng = np.random.default_rng(42)

auc_distributions = {}

for window in [30, 90, 180, 365]:
    d = pd.read_pickle(f"dataset_v3_window_{window}.pkl")
    d = d.merge(base, on="account_id", how="left")
    freq_dummies = pd.get_dummies(d["frequency"], prefix="freq")
    X = pd.concat([d[FEATURE_COLS], freq_dummies], axis=1).fillna(0)
    y = d["high_potential"]

    d_sorted_idx = d.sort_values("account_open_date").index
    split_point = int(len(d_sorted_idx) * 0.8)
    train_idx = d_sorted_idx[:split_point]
    test_idx = d_sorted_idx[split_point:]

    X_train, X_test = X.loc[train_idx], X.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=42)
    model.fit(X_train_s, y_train)
    y_proba = model.predict_proba(X_test_s)[:, 1]

    y_test_arr = y_test.values
    n = len(y_test_arr)
    boot_aucs = []
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, n)
        yb, pb = y_test_arr[idx], y_proba[idx]
        if len(set(yb)) < 2:
            continue
        boot_aucs.append(roc_auc_score(yb, pb))
    boot_aucs = np.array(boot_aucs)
    auc_distributions[window] = boot_aucs
    lo, hi = np.percentile(boot_aucs, [2.5, 97.5])
    print(f"Window {window:3d} days: AUC = {boot_aucs.mean():.3f}  95% CI [{lo:.3f}, {hi:.3f}]")

print("\nPairwise comparison (probability window B's bootstrap AUC > window A's):")
windows = [30, 90, 180, 365]
for i in range(len(windows) - 1):
    a, b = windows[i], windows[i + 1]
    n = min(len(auc_distributions[a]), len(auc_distributions[b]))
    prob_b_better = np.mean(auc_distributions[b][:n] > auc_distributions[a][:n])
    print(f"  P(AUC[{b}d] > AUC[{a}d]) = {prob_b_better:.3f}")
