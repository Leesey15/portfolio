# Data

This project uses the **PKDD'99 Czech Financial Dataset** (the "Berka dataset") —
real, anonymized transaction records from a Czech bank, 1993-1998.

The raw data is not committed to this repository (it belongs to its own source
repository and is regenerated locally). To fetch it:

```bash
git clone https://github.com/Kusainov/czech-banking-fin-analysis.git
```

This creates a `czech-banking-fin-analysis/` folder in the project root containing
the seven relational CSV tables the pipeline expects:

- `account.csv`
- `client.csv`
- `disp.csv`
- `trans.csv`
- `loan.csv`
- `card.csv`
- `district.csv`

Once cloned, run the scripts in `src/` in order (01 through 05), or run
`notebooks/MSc_Project_Pipeline.ipynb` directly.
