# Digital Media Store — SQL Business Analytics

**Author:** Aseye Amenuveve Gbagbo

## Purpose

A set of nine business-analytics SQL queries against a relational sales database, demonstrating multi-table joins, aggregation, subqueries, common table expressions (CTEs), and window functions (`RANK`, `NTILE`, `LAG`, running `SUM() OVER`) — the query patterns behind most real-world revenue, customer, and performance reporting.

## Dataset

The [Chinook sample database](https://github.com/lerocha/chinook-database) (SQLite) — a fictional digital media store with customers, invoices, tracks, albums, artists, and employees. It's a small, widely-used public practice dataset (59 customers, 412 invoices, 3,503 tracks), so absolute revenue figures here are illustrative rather than business-scale — the point is the query technique, not the dollar amounts.

## Queries and what they demonstrate

| # | Question | Technique |
|---|---|---|
| 1 | Which countries generate the most revenue? | JOIN, GROUP BY, aggregates |
| 2 | Which genres generate the most revenue, and what share of the total? | multi-table JOIN, scalar subquery |
| 3 | Monthly revenue and cumulative running total | window function `SUM() OVER` |
| 4 | Top 10 customers by lifetime spend, ranked | window function `RANK() OVER` |
| 5 | Sales performance by employee (sales support agent) | 3-table JOIN, aggregation |
| 6 | Customer value segmentation (spend quartiles) | CTE, `NTILE(4) OVER`, CASE |
| 7 | Year-over-year change in average order value | CTE, window function `LAG() OVER` |
| 8 | Tracks purchased more than the store average | correlated subquery, HAVING |
| 9 | Reusable view for downstream reporting tools | `CREATE VIEW` |

## Selected findings (from real query output)

- **Revenue concentration:** the USA and Canada alone account for roughly 36% of total revenue across the top-10 countries (`Q1`).
- **Genre concentration:** Rock accounts for 35.5% of all revenue on its own — more than the next three genres (Latin, Metal, Alternative & Punk) combined (`Q2`).
- **Customer value spread:** the top spending quartile of customers generates $654 of revenue at an average of $43.62/customer, versus $37.55/customer in the bottom quartile — modest but real spread given the dataset's size (`Q6`).
- **Employee performance:** all three sales support agents perform within a similar band (~$720-$833 in managed revenue), suggesting an evenly distributed customer book rather than one standout performer (`Q5`).
- **YoY average order value:** fluctuates within a ±7% band year to year, with no sustained trend up or down across 2021-2025 (`Q7`).

## Files

```
analysis_queries.sql   # all 9 queries, commented, ready to run against chinook.sqlite
run_queries.py         # executes every query and prints/exports results
query_results.json     # captured output of every query, for reference without re-running
chinook.sqlite         # the database itself
```

## Running it

```bash
python3 run_queries.py
```

Requires only Python's built-in `sqlite3` module — no external dependencies.

## Limitations

This is a small, synthetic-dates practice database, not a production sales system — figures are for demonstrating query technique, not real business decisions. In a production setting these same query patterns would run against a live warehouse and typically get wrapped in stored views, scheduled into a BI tool (see the companion Power BI project), or exposed via an API.
