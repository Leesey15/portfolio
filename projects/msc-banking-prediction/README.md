# Early Prediction of High-Potential Banking Customers

**Do banks really need to wait a year to know who their best customers will be?**

This project tests whether behavioral and transactional data from a customer's first 30, 90, 180, or 365 days can predict — as reliably as traditional Customer Lifetime Value (CLV) models — which customers will become high-potential, without waiting the full observation period banks conventionally use.

## Key finding

Predictive reliability keeps improving all the way to 365 days, but the *rate* of improvement is far from constant:

| Window | ROC-AUC (Random Forest) | Gain from previous window |
|---|---|---|
| 30 days | 0.743 | — |
| 90 days | 0.734 | −0.009 (not statistically significant) |
| 180 days | 0.810 | **+0.076** (largest gain, highly significant) |
| 365 days | 0.865 | +0.055 (smaller gain, double the wait) |

Traditional CLV models are not wrong to use long observation windows — reliability genuinely keeps climbing toward the one-year mark. But **most of the achievable improvement arrives by six months**, not by waiting a full year. Going from 90 to 180 days buys roughly three times more reliability per day waited than going from 180 to 365 days does.

Both findings are confirmed with bootstrap significance testing (200 resamples per window) and hold up across three different percentile thresholds (25%, 40%, 50%) for defining "high potential."

## Why this matters

Banks currently wait close to a year before confidently assessing a new customer's value. This project suggests a bank could assess customer potential around the six-month mark instead — capturing most of the achievable predictive reliability at roughly half the wait.

## Methodology

- **Dataset:** [PKDD'99 Czech Financial Dataset](https://github.com/Kusainov/czech-banking-fin-analysis) (the "Berka dataset") — 4,500 real, anonymized bank accounts, 1993–1998, over 1 million transactions across 7 relational tables (account, client, disposition, transaction, loan, card, district).
- **No leakage:** predictor features are built *only* from transactions inside each observation window (30/90/180/365 days). The target label is built *only* from a 180-day follow-up period *after* the window ends. The two never overlap in time.
- **Target definition:** "High potential" is a percentile threshold (top 40%) on a composite score of three post-window signals — sustained activity, recent (tail) activity, and balance growth — deliberately built from variables distinct from the predictors, so the target isn't just restating the features.
- **Behavioral features:** beyond standard financial features (transaction count, average balance, etc.), five behavioral-pattern features are engineered from transaction *timing*, grounded in cited theory:
  - `habit_strength` — does transaction timing become more regular over the window? (Lally et al., 2010, on habit formation)
  - `interval_cv` — consistency of time between transactions (Wood & Neal, 2007)
  - `breadth_growth` — growth in variety of transaction types used
  - `txn_trend` / `amount_trend` — trajectory of activity across the window (Verhoef et al., 2010)
- **Models:** Logistic Regression and Random Forest, compared against a majority-class baseline, evaluated with Accuracy, Precision, Recall, F1, and ROC-AUC.
- **Validation:** temporal, cohort-based train/test split (earliest 80% of accounts by opening date → train, most recent 20% → test) rather than a random split, since this is an inherently time-ordered problem.
- **Robustness:** bootstrap significance testing across windows, and a threshold-sensitivity check across three percentile cutoffs.

## Repository structure

```
notebooks/
  MSc_Project_Pipeline.ipynb   # full pipeline, runs end to end
src/
  01_load_preprocess.py        # load & merge relational tables
  02_features_target.py        # feature engineering & target construction
  03_train_evaluate.py         # model training & evaluation
  04_significance_check.py     # bootstrap significance testing
  05_threshold_sensitivity.py  # percentile threshold robustness check
results/
  model_results.csv
  results_comparison.png
  threshold_sensitivity.csv
  feature_importance_window_*.csv
```

## Running it

```bash
git clone https://github.com/Kusainov/czech-banking-fin-analysis.git
pip install -r requirements.txt
python src/01_load_preprocess.py
python src/02_features_target.py
python src/03_train_evaluate.py
python src/04_significance_check.py
python src/05_threshold_sensitivity.py
```

Or run `notebooks/MSc_Project_Pipeline.ipynb` directly — it executes the same steps end to end and produces the charts in `results/`.

## Limitations

- **Geographic scope:** no open, transaction-level African banking dataset was identified at the time of this study; available African datasets are either demographic/survey-based or synthetic. Replicating this study on real African transaction or mobile-money data is a direction for future work.
- **Temporal scope:** the dataset spans 1993–1998. Banking behavior has evolved since, though the underlying behavioral principles (habit formation, engagement trajectory) remain relevant to test.
- **No intervention tested:** this project predicts *who* to act on, not *whether* acting on them changes outcomes. That question requires a separate field experiment or A/B test — flagged as future work.

## Theoretical framing

Beyond prediction, the project proposes a two-track intervention framework grounded in Human-Computer Interaction and Persuasive Systems Design (Fogg, 2003; Oinas-Kukkonen & Harjumaa, 2009):
- **Early window (30–90 days):** low-cost, exploratory nudges aimed at shifting customers on a weaker trajectory while habits are still forming.
- **Later window (180 days):** higher-confidence reinforcement of already-established positive trajectories, once prediction is more reliable.

This framework is proposed, not empirically tested — see Limitations.

## Author

Aseye Ameneuveve Gbagbo — MSc Data Science, University of Ghana

## License

MIT — see [LICENSE](LICENSE).
