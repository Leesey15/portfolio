"""
Step 1-3: Load relational tables, merge, preprocess.
PKDD'99 Czech Financial Dataset (Berka dataset).
"""
import pandas as pd
import numpy as np

DATA_DIR = "czech-banking-fin-analysis"

def parse_pkdd_date(series):
    """Dates are stored as YYMMDD (int/str), years 93-98 -> 1993-1998."""
    s = series.astype(str).str.zfill(6)
    year = s.str[0:2].astype(int) + 1900
    month = s.str[2:4].astype(int)
    day = s.str[4:6].astype(int)
    return pd.to_datetime(dict(year=year, month=month, day=day), errors="coerce")

# --- Load ---
account = pd.read_csv(f"{DATA_DIR}/account.csv", sep=";")
client = pd.read_csv(f"{DATA_DIR}/client.csv", sep=";")
disp = pd.read_csv(f"{DATA_DIR}/disp.csv", sep=";")
trans = pd.read_csv(f"{DATA_DIR}/trans.csv", sep=";", low_memory=False)
loan = pd.read_csv(f"{DATA_DIR}/loan.csv", sep=";")
card = pd.read_csv(f"{DATA_DIR}/card.csv", sep=";")
district = pd.read_csv(f"{DATA_DIR}/district.csv", sep=";")

print("Raw shapes:")
for name, df in [("account", account), ("client", client), ("disp", disp),
                  ("trans", trans), ("loan", loan), ("card", card), ("district", district)]:
    print(f"  {name}: {df.shape}")

# --- Clean column names / dates ---
account["account_open_date"] = parse_pkdd_date(account["date"])
trans["trans_date"] = parse_pkdd_date(trans["date"])
loan["loan_date"] = parse_pkdd_date(loan["date"])
card["card_issue_date"] = parse_pkdd_date(card["issued"].astype(str).str[:6])

# district: rename key columns per Berka data dictionary
district = district.rename(columns={
    "A1": "district_id",
    "A2": "district_name",
    "A3": "region",
    "A4": "n_inhabitants",
    "A10": "urban_ratio_pct",
    "A11": "avg_salary",
    "A12": "unemployment_95",
    "A13": "unemployment_96",
    "A14": "entrepreneurs_per_1000",
    "A15": "crimes_95",
    "A16": "crimes_96",
})
for col in ["unemployment_95", "unemployment_96", "crimes_95", "crimes_96"]:
    district[col] = pd.to_numeric(district[col], errors="coerce")

# disp: keep only account OWNERS
disp_owner = disp[disp["type"] == "OWNER"][["account_id", "client_id"]]

# --- Merge account-level base table ---
base = account.merge(disp_owner, on="account_id", how="left")
base = base.merge(client[["client_id", "district_id"]].rename(columns={"district_id": "client_district_id"}),
                   on="client_id", how="left")
base = base.merge(district, left_on="district_id", right_on="district_id", how="left")

print("\nMerged base (account-level) shape:", base.shape)

# --- Save intermediate artifacts ---
base.to_pickle("base_accounts.pkl")
trans.to_pickle("trans_clean.pkl")
loan.to_pickle("loan_clean.pkl")
card.to_pickle("card_clean.pkl")

print("\nAccount opening date range:", account['account_open_date'].min(), "to", account['account_open_date'].max())
print("Transaction date range:", trans['trans_date'].min(), "to", trans['trans_date'].max())
print("\nSaved: base_accounts.pkl, trans_clean.pkl, loan_clean.pkl, card_clean.pkl")
