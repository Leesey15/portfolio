# Aseye Gbagbo — Data Analytics Portfolio

Source for [aseye's GitHub Pages portfolio site](https://leesey15.github.io/portfolio/) (update the link once published — see setup steps below).

Five projects spanning machine learning, data engineering, and business analytics:

1. **`projects/msc-banking-prediction/`** — MSc thesis: predicting high-potential banking customers from early transaction data (Python, scikit-learn).
2. **`projects/afilearn-data-management/`** — end-to-end data management pipeline: database design, ETL, warehousing, NoSQL, security (SQL, DuckDB, Python).
3. **`projects/excel-retail-analysis/`** — retail sales & profitability dashboard, formula-driven (Excel).
4. **`projects/sql-chinook-analytics/`** — business analytics queries with joins, CTEs, and window functions (SQL).
5. **`projects/powerbi-development-dashboard/`** — global human development dashboard data model + DAX (Power BI).

## Publishing this site on GitHub Pages

1. Create a new **public** GitHub repository (e.g. `portfolio`).
2. Upload everything in this folder to the repository root (keep the folder structure as-is).
3. In the repo, go to **Settings → Pages**.
4. Under **Source**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`. Save.
5. After a minute or two, your site will be live at `https://<your-username>.github.io/<repo-name>/`.
6. Update the GitHub link in `index.html` (and this README) if your username differs from the placeholder used here.

## Local preview

Open `index.html` directly in a browser, or serve it locally:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```
