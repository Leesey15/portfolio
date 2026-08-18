"""
Step 7-8: Train Logistic Regression and Random Forest per observation window,
using two feature sets (financial only vs. financial + behavioral) to isolate
the contribution of the behavioral-pattern features. Temporal cohort split,
majority-class baseline included.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.dummy import DummyClassifier
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

FEATURE_SETS = {
    "Financial only": FINANCIAL_COLS,
    "Financial + Behavioral": FINANCIAL_COLS + BEHAVIORAL_COLS,
}

results = []

for window in [30, 90, 180, 365]:
    d = pd.read_pickle(f"dataset_v3_window_{window}.pkl")
    d = d.merge(base, on="account_id", how="left")
    freq_dummies = pd.get_dummies(d["frequency"], prefix="freq")

    d_sorted_idx = d.sort_values("account_open_date").index
    split_point = int(len(d_sorted_idx) * 0.8)
    train_idx = d_sorted_idx[:split_point]
    test_idx = d_sorted_idx[split_point:]
    y = d["high_potential"]

    for set_name, cols in FEATURE_SETS.items():
        X = pd.concat([d[cols], freq_dummies], axis=1).fillna(0)
        X_train, X_test = X.loc[train_idx], X.loc[test_idx]
        y_train, y_test = y.loc[train_idx], y.loc[test_idx]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        models = {
            "Baseline (majority class)": DummyClassifier(strategy="most_frequent"),
            "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
            "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=8,
                                                     class_weight="balanced", random_state=42),
        }

        for name, model in models.items():
            if name == "Baseline (majority class)":
                if set_name != "Financial only":
                    continue
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_proba = model.predict_proba(X_test)[:, 1]
            else:
                model.fit(X_train_s, y_train)
                y_pred = model.predict(X_test_s)
                y_proba = model.predict_proba(X_test_s)[:, 1]

            try:
                auc = roc_auc_score(y_test, y_proba)
            except ValueError:
                auc = np.nan

            results.append({
                "window_days": window,
                "feature_set": set_name if name != "Baseline (majority class)" else "N/A",
                "model": name,
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
                "f1": f1_score(y_test, y_pred, zero_division=0),
                "roc_auc": auc,
                "n_train": len(y_train),
                "n_test": len(y_test),
            })

            if name == "Random Forest" and set_name == "Financial + Behavioral":
                imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
                imp.head(15).to_csv(f"feature_importance_window_{window}.csv")

results_df = pd.DataFrame(results)
results_df.to_csv("model_results.csv", index=False)
pd.set_option("display.float_format", lambda x: f"{x:.3f}")
print(results_df.to_string(index=False))
