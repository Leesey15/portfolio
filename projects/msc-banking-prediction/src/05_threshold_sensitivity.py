"""
Check whether the diminishing-returns pattern across windows holds if the
percentile threshold for High Potential is 25%, 40%, or 50% instead of just 40%.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score
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

results = []
for window in [30, 90, 180, 365]:
    d = pd.read_pickle(f"dataset_v3_window_{window}.pkl")
    d = d.merge(base, on="account_id", how="left")
    freq_dummies = pd.get_dummies(d["frequency"], prefix="freq")
    X_all = pd.concat([d[FEATURE_COLS], freq_dummies], axis=1).fillna(0)

    d_sorted_idx = d.sort_values("account_open_date").index
    split_point = int(len(d_sorted_idx) * 0.8)
    train_idx = d_sorted_idx[:split_point]
    test_idx = d_sorted_idx[split_point:]

    for top_pct in [0.25, 0.40, 0.50]:
        threshold = d["engagement_score"].quantile(1 - top_pct)
        y = (d["engagement_score"] >= threshold).astype(int)

        X_train, X_test = X_all.loc[train_idx], X_all.loc[test_idx]
        y_train, y_test = y.loc[train_idx], y.loc[test_idx]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        model = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=42)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        y_proba = model.predict_proba(X_test_s)[:, 1]

        results.append({
            "window_days": window,
            "top_pct": top_pct,
            "positive_rate": y.mean(),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "f1": f1_score(y_test, y_pred, zero_division=0),
        })

df = pd.DataFrame(results)
df.to_csv("threshold_sensitivity.csv", index=False)
pivot_auc = df.pivot(index="window_days", columns="top_pct", values="roc_auc")
print("ROC-AUC by window and threshold:")
print(pivot_auc.round(3))
