/* ==========================================================================
   Chinook Digital Media Store — SQL Business Analytics
   Author: Aseye Amenuveve Gbagbo

   Dataset: Chinook sample database (SQLite) — a fictional digital media
   store (customers, invoices, tracks, albums, artists, employees), widely
   used as a public SQL practice dataset. Source:
   https://github.com/lerocha/chinook-database

   Each query below answers a specific business question and is annotated
   with the SQL techniques it demonstrates (joins, aggregation, subqueries,
   CTEs, window functions, views).
   ========================================================================== */


/* --------------------------------------------------------------------------
   Q1. Which countries generate the most revenue?
   Technique: JOIN + GROUP BY + aggregate functions, ORDER BY / LIMIT
   -------------------------------------------------------------------------- */
SELECT
    c.Country,
    COUNT(DISTINCT i.InvoiceId)      AS total_invoices,
    ROUND(SUM(i.Total), 2)           AS total_revenue,
    ROUND(AVG(i.Total), 2)           AS avg_invoice_value
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.Country
ORDER BY total_revenue DESC
LIMIT 10;


/* --------------------------------------------------------------------------
   Q2. Which music genres generate the most revenue, and what share of the
       total do they represent?
   Technique: multi-table JOIN, subquery in SELECT for % of total
   -------------------------------------------------------------------------- */
SELECT
    g.Name                                                    AS genre,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2)                 AS genre_revenue,
    ROUND(
        100.0 * SUM(il.UnitPrice * il.Quantity) /
        (SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine), 2
    )                                                          AS pct_of_total_revenue
FROM InvoiceLine il
JOIN Track t  ON t.TrackId = il.TrackId
JOIN Genre g  ON g.GenreId = t.GenreId
GROUP BY g.Name
ORDER BY genre_revenue DESC
LIMIT 10;


/* --------------------------------------------------------------------------
   Q3. What does monthly revenue look like over time, and what is the
       cumulative (running total) revenue?
   Technique: date functions, window function SUM() OVER (running total)
   -------------------------------------------------------------------------- */
SELECT
    strftime('%Y-%m', i.InvoiceDate)                           AS year_month,
    ROUND(SUM(i.Total), 2)                                      AS monthly_revenue,
    ROUND(SUM(SUM(i.Total)) OVER (ORDER BY strftime('%Y-%m', i.InvoiceDate)), 2)
                                                                 AS running_total_revenue
FROM Invoice i
GROUP BY year_month
ORDER BY year_month;


/* --------------------------------------------------------------------------
   Q4. Who are the top 10 customers by lifetime spend, and how do they rank?
   Technique: window function RANK() OVER, JOIN
   -------------------------------------------------------------------------- */
SELECT
    RANK() OVER (ORDER BY SUM(i.Total) DESC)   AS spend_rank,
    c.FirstName || ' ' || c.LastName           AS customer,
    c.Country,
    ROUND(SUM(i.Total), 2)                     AS lifetime_spend,
    COUNT(i.InvoiceId)                         AS orders
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId
ORDER BY spend_rank
LIMIT 10;


/* --------------------------------------------------------------------------
   Q5. How does each sales support employee's book of customers perform?
   Technique: JOIN across Employee -> Customer -> Invoice, aggregate
   -------------------------------------------------------------------------- */
SELECT
    e.FirstName || ' ' || e.LastName          AS sales_agent,
    e.Title,
    COUNT(DISTINCT c.CustomerId)              AS customers_managed,
    COUNT(i.InvoiceId)                        AS invoices_handled,
    ROUND(SUM(i.Total), 2)                    AS total_revenue
FROM Employee e
JOIN Customer c ON c.SupportRepId = e.EmployeeId
JOIN Invoice i  ON i.CustomerId = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY total_revenue DESC;


/* --------------------------------------------------------------------------
   Q6. Segment customers into spend quartiles and see how each segment
       contributes to revenue (a simple RFM-style value segmentation).
   Technique: CTE (WITH clause), window function NTILE(), CASE expression
   -------------------------------------------------------------------------- */
WITH customer_spend AS (
    SELECT
        c.CustomerId,
        c.FirstName || ' ' || c.LastName AS name,
        SUM(i.Total)                     AS total_spend
    FROM Customer c
    JOIN Invoice i ON i.CustomerId = c.CustomerId
    GROUP BY c.CustomerId
),
tiered AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY total_spend DESC) AS spend_quartile
    FROM customer_spend
)
SELECT
    CASE spend_quartile
        WHEN 1 THEN '1. Top 25% spenders'
        WHEN 2 THEN '2. 2nd quartile'
        WHEN 3 THEN '3. 3rd quartile'
        ELSE '4. Bottom 25% spenders'
    END AS segment,
    COUNT(*)                       AS customers,
    ROUND(SUM(total_spend), 2)     AS segment_revenue,
    ROUND(AVG(total_spend), 2)     AS avg_spend_per_customer
FROM tiered
GROUP BY spend_quartile
ORDER BY spend_quartile;


/* --------------------------------------------------------------------------
   Q7. What is the year-over-year change in average order value?
   Technique: window function LAG() for period-over-period comparison
   -------------------------------------------------------------------------- */
WITH yearly AS (
    SELECT
        strftime('%Y', InvoiceDate)  AS year,
        ROUND(AVG(Total), 2)         AS avg_order_value
    FROM Invoice
    GROUP BY year
)
SELECT
    year,
    avg_order_value,
    LAG(avg_order_value) OVER (ORDER BY year)                                 AS prev_year_aov,
    ROUND(
        100.0 * (avg_order_value - LAG(avg_order_value) OVER (ORDER BY year))
        / LAG(avg_order_value) OVER (ORDER BY year), 1
    )                                                                          AS pct_change
FROM yearly
ORDER BY year;


/* --------------------------------------------------------------------------
   Q8. Which tracks have been purchased more times than the store average,
       and which artist do they belong to?
   Technique: correlated/scalar subquery in WHERE, multi-table JOIN
   -------------------------------------------------------------------------- */
SELECT
    ar.Name          AS artist,
    al.Title         AS album,
    t.Name           AS track,
    SUM(il.Quantity) AS times_purchased
FROM InvoiceLine il
JOIN Track t   ON t.TrackId = il.TrackId
JOIN Album al  ON al.AlbumId = t.AlbumId
JOIN Artist ar ON ar.ArtistId = al.ArtistId
GROUP BY t.TrackId
HAVING SUM(il.Quantity) > (
    SELECT AVG(track_qty) FROM (
        SELECT SUM(Quantity) AS track_qty FROM InvoiceLine GROUP BY TrackId
    )
)
ORDER BY times_purchased DESC
LIMIT 15;


/* --------------------------------------------------------------------------
   Q9. Reusable view: monthly revenue by country, for downstream reporting
       tools (e.g. a BI dashboard) to query directly without repeating logic.
   Technique: CREATE VIEW
   -------------------------------------------------------------------------- */
DROP VIEW IF EXISTS vw_monthly_revenue_by_country;
CREATE VIEW vw_monthly_revenue_by_country AS
SELECT
    c.Country,
    strftime('%Y-%m', i.InvoiceDate)  AS year_month,
    ROUND(SUM(i.Total), 2)            AS revenue
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.Country, year_month;

-- Example usage of the view:
SELECT * FROM vw_monthly_revenue_by_country
WHERE Country = 'USA'
ORDER BY year_month
LIMIT 12;
