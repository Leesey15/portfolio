"""
Step 4-6: Percentile-based target (matches proposal), built from future signals
that are conceptually distinct from the in-window predictors:
  1. future_txn_count        - sustained activity
  2. future_tail_activity    - transaction count in final 30 days of the
                                follow-up period (continuous retention/recency
                                signal)
  3. future_balance_change   - end minus start balance over follow-up
                                (economic VALUE GROWTH, not balance LEVEL)
These three are z-scored and summed into a composite future-engagement score;
top 40% = High Potential (1), matching the proposal's "percentile threshold
of future engagement."

Behavioral-pattern features (habit_strength, interval_cv, breadth_growth,
txn_trend, amount_trend) tied to cited theory (Lally 2010; Wood & Neal 2007;
Verhoef et al. 2010).
"""
import pandas as pd
import numpy as np

base = pd.read_pickle("base_accounts.pkl")
trans = pd.read_pickle("trans_clean.pkl")
loan = pd.read_pickle("loan_clean.pkl")
card = pd.read_pickle("card_clean.pkl")

disp = pd.read_csv("czech-banking-fin-analysis/disp.csv", sep=";")
card = card.merge(disp[["disp_id", "account_id"]], on="disp_id", how="left")

DATASET_MAX_DATE = trans["trans_date"].max()
FOLLOW_UP_DAYS = 180
TAIL_DAYS = 30
TOP_PCT = 0.40
WINDOWS = [30, 90, 180, 365]


def behavioral_features(g, window_days):
    out = {}
    dates = g["trans_date"].sort_values()
    n = len(dates)

    if n >= 2:
        intervals = dates.diff().dt.days.dropna().values.astype(float)
        interval_mean = intervals.mean()
        interval_std = intervals.std() if len(intervals) > 1 else 0.0
        out["interval_cv"] = (interval_std / interval_mean) if interval_mean > 0 else 0.0
    else:
        out["interval_cv"] = 0.0

    midpoint = g["trans_date"].min() + pd.Timedelta(days=window_days / 2)
    first_half = dates[dates < midpoint]
    second_half = dates[dates >= midpoint]

    def _std_intervals(s):
        if len(s) >= 3:
            iv = s.sort_values().diff().dt.days.dropna().values.astype(float)
            return iv.std() if len(iv) > 1 else 0.0
        return np.nan

    std_first = _std_intervals(first_half)
    std_second = _std_intervals(second_half)
    out["habit_strength"] = 0.0 if (np.isnan(std_first) or np.isnan(std_second)) else std_first - std_second

    ops_first = g.loc[g["trans_date"] < midpoint, "operation"].nunique()
    ops_second = g.loc[g["trans_date"] >= midpoint, "operation"].nunique()
    out["breadth_growth"] = ops_second - ops_first

    third = window_days / 3
    open_date = g["trans_date"].min()
    bounds = [open_date, open_date + pd.Timedelta(days=third),
              open_date + pd.Timedelta(days=2 * third), open_date + pd.Timedelta(days=window_days)]
    counts, amounts = [], []
    for i in range(3):
        seg = g[(g["trans_date"] >= bounds[i]) & (g["trans_date"] < bounds[i + 1])]
        counts.append(len(seg))
        amounts.append(seg["amount"].sum())
    x = np.array([0, 1, 2])
    out["txn_trend"] = np.polyfit(x, counts, 1)[0] if len(set(counts)) > 1 else 0.0
    out["amount_trend"] = np.polyfit(x, amounts, 1)[0] if len(set(amounts)) > 1 else 0.0
    return out


def build_dataset(window_days, base, trans, loan, card, follow_up_days=FOLLOW_UP_DAYS):
    acc = base.copy()
    acc["window_end"] = acc["account_open_date"] + pd.Timedelta(days=window_days)
    acc["future_end"] = acc["window_end"] + pd.Timedelta(days=follow_up_days)
    acc = acc[acc["future_end"] <= DATASET_MAX_DATE].copy()

    t = trans.merge(acc[["account_id", "account_open_date", "window_end", "future_end"]],
                     on="account_id", how="inner")
    in_window = t[(t["trans_date"] >= t["account_open_date"]) & (t["trans_date"] < t["window_end"])]
    in_future = t[(t["trans_date"] >= t["window_end"]) & (t["trans_date"] < t["future_end"])]

    credit_mask = in_window["type"] == "PRIJEM"
    debit_mask = in_window["type"].isin(["VYDAJ", "VYBER"])

    feat = in_window.groupby("account_id").agg(
        txn_count=("trans_id", "count"), avg_txn_amount=("amount", "mean"),
        std_txn_amount=("amount", "std"), total_amount=("amount", "sum"),
        avg_balance=("balance", "mean"), min_balance=("balance", "min"),
        max_balance=("balance", "max"), n_unique_operations=("operation", "nunique"),
        n_days_active=("trans_date", "nunique"),
    ).reset_index()

    ending_bal = (in_window.sort_values("trans_date").groupby("account_id").tail(1)
                  [["account_id", "balance"]].rename(columns={"balance": "ending_balance"}))
    feat = feat.merge(ending_bal, on="account_id", how="left")

    credit_sum = in_window[credit_mask].groupby("account_id")["amount"].sum().rename("credit_amount")
    debit_sum = in_window[debit_mask].groupby("account_id")["amount"].sum().rename("debit_amount")
    feat = feat.merge(credit_sum, on="account_id", how="left").merge(debit_sum, on="account_id", how="left")
    feat["credit_amount"] = feat["credit_amount"].fillna(0)
    feat["debit_amount"] = feat["debit_amount"].fillna(0)
    feat["net_flow"] = feat["credit_amount"] - feat["debit_amount"]

    def balance_slope(g):
        if len(g) < 2:
            return 0.0
        x = (g["trans_date"] - g["trans_date"].min()).dt.days.values.astype(float)
        y = g["balance"].values.astype(float)
        return 0.0 if np.std(x) == 0 else np.polyfit(x, y, 1)[0]

    slopes = in_window.groupby("account_id").apply(balance_slope, include_groups=False).rename("balance_trend")
    feat = feat.merge(slopes, on="account_id", how="left")
    feat["txn_count_per_day"] = feat["txn_count"] / window_days
    feat["active_day_ratio"] = feat["n_days_active"] / window_days

    beh_rows = []
    for acct_id, g in in_window.groupby("account_id"):
        if len(g) == 0:
            continue
        row = behavioral_features(g, window_days)
        row["account_id"] = acct_id
        beh_rows.append(row)
    beh_df = pd.DataFrame(beh_rows)
    if len(beh_df) > 0:
        feat = feat.merge(beh_df, on="account_id", how="left")

    loan_in_window = loan.merge(acc[["account_id", "account_open_date", "window_end"]], on="account_id")
    loan_in_window = loan_in_window[(loan_in_window["loan_date"] >= loan_in_window["account_open_date"]) &
                                     (loan_in_window["loan_date"] < loan_in_window["window_end"])]

    fut_count = in_future.groupby("account_id").agg(future_txn_count=("trans_id", "count")).reset_index()

    tail_start = acc.set_index("account_id")["future_end"] - pd.Timedelta(days=TAIL_DAYS)
    in_future_tail = in_future.merge(tail_start.rename("tail_start"), left_on="account_id", right_index=True)
    in_future_tail = in_future_tail[in_future_tail["trans_date"] >= in_future_tail["tail_start"]]
    tail_activity = in_future_tail.groupby("account_id").size().rename("future_tail_activity").reset_index()

    fut_start_bal = (in_future.sort_values("trans_date").groupby("account_id").head(1)
                      [["account_id", "balance"]].rename(columns={"balance": "future_start_balance"}))
    fut_end_bal = (in_future.sort_values("trans_date").groupby("account_id").tail(1)
                   [["account_id", "balance"]].rename(columns={"balance": "future_end_balance"}))
    fut_balance = fut_start_bal.merge(fut_end_bal, on="account_id", how="outer")

    data = acc[["account_id", "frequency", "avg_salary", "unemployment_95", "unemployment_96",
                "urban_ratio_pct", "entrepreneurs_per_1000", "n_inhabitants"]].copy()
    data = data.merge(feat, on="account_id", how="left")
    data = data.merge(fut_count, on="account_id", how="left")
    data = data.merge(tail_activity, on="account_id", how="left")
    data = data.merge(fut_balance, on="account_id", how="left")
    data["has_loan_in_window"] = data["account_id"].isin(loan_in_window["account_id"]).astype(int)

    fill_zero_cols = ["txn_count", "avg_txn_amount", "std_txn_amount", "total_amount", "avg_balance",
                       "min_balance", "max_balance", "n_unique_operations", "n_days_active", "ending_balance",
                       "credit_amount", "debit_amount", "net_flow", "balance_trend", "txn_count_per_day",
                       "active_day_ratio", "interval_cv", "habit_strength", "breadth_growth",
                       "txn_trend", "amount_trend", "has_loan_in_window",
                       "future_txn_count", "future_tail_activity", "future_start_balance", "future_end_balance"]
    for c in fill_zero_cols:
        data[c] = data[c].fillna(0)

    data["future_balance_change"] = data["future_end_balance"] - data["future_start_balance"]

    for col, z in [("future_txn_count", "z_activity"),
                   ("future_tail_activity", "z_retention"),
                   ("future_balance_change", "z_value_growth")]:
        mu, sigma = data[col].mean(), data[col].std()
        data[z] = (data[col] - mu) / sigma if sigma > 0 else 0.0

    data["engagement_score"] = data[["z_activity", "z_retention", "z_value_growth"]].sum(axis=1)
    threshold = data["engagement_score"].quantile(1 - TOP_PCT)
    data["high_potential"] = (data["engagement_score"] >= threshold).astype(int)

    data["window_days"] = window_days
    return data


for w in WINDOWS:
    d = build_dataset(w, base, trans, loan, card)
    print(f"Window={w} days -> n={len(d)} | positive rate={d['high_potential'].mean():.3f} | "
          f"corr(score, avg_balance)={d['engagement_score'].corr(d['avg_balance']):.3f}")
    d.to_pickle(f"dataset_v3_window_{w}.pkl")

print("\nSaved dataset_v3_window_{30,90,180,365}.pkl")
