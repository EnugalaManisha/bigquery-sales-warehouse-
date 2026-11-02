-- Analytical queries (CTEs and window functions).
-- Written to run on BigQuery; they also run unchanged on DuckDB for local testing
-- when the table names are swapped (see local_validate.py).

-- 1) Monthly revenue with month-over-month growth
WITH monthly AS (
  SELECT
    DATE_TRUNC(order_date, MONTH) AS month,
    SUM(net_revenue) AS revenue
  FROM fact_sales
  GROUP BY month
)
SELECT
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
  ROUND(
    100 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2
  ) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- 2) Top 3 products by revenue within each category
WITH product_rev AS (
  SELECT category, product_id, SUM(net_revenue) AS revenue
  FROM fact_sales
  GROUP BY category, product_id
),
ranked AS (
  SELECT
    category,
    product_id,
    revenue,
    RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rnk
  FROM product_rev
)
SELECT category, product_id, revenue, rnk
FROM ranked
WHERE rnk <= 3
ORDER BY category, rnk;

-- 3) Top 10 customers by lifetime value with running share of total revenue
WITH customer_rev AS (
  SELECT customer_id, SUM(net_revenue) AS lifetime_value
  FROM fact_sales
  GROUP BY customer_id
),
ranked AS (
  SELECT
    customer_id,
    lifetime_value,
    ROW_NUMBER() OVER (ORDER BY lifetime_value DESC) AS rn,
    SUM(lifetime_value) OVER (ORDER BY lifetime_value DESC
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    SUM(lifetime_value) OVER () AS grand_total
  FROM customer_rev
)
SELECT
  customer_id,
  lifetime_value,
  ROUND(100 * running_total / grand_total, 2) AS cumulative_share_pct
FROM ranked
WHERE rn <= 10
ORDER BY rn;

-- 4) Revenue by region and channel with share of region total
WITH region_channel AS (
  SELECT region, channel, SUM(net_revenue) AS revenue
  FROM fact_sales
  GROUP BY region, channel
)
SELECT
  region,
  channel,
  revenue,
  ROUND(100 * revenue / SUM(revenue) OVER (PARTITION BY region), 2) AS pct_of_region
FROM region_channel
ORDER BY region, revenue DESC;
