-- Star schema built from stg_orders.
-- Dimensions are small; the fact table is partitioned by order_date and
-- clustered by the columns most used in filters and joins.

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.dim_customer` AS
SELECT DISTINCT
  customer_id,
  customer_name,
  segment
FROM `${PROJECT}.${DATASET}.stg_orders`;

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.dim_product` AS
SELECT DISTINCT
  product_id,
  product_name,
  category,
  unit_price AS list_price
FROM `${PROJECT}.${DATASET}.stg_orders`;

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.dim_location` AS
SELECT DISTINCT
  region,
  city
FROM `${PROJECT}.${DATASET}.stg_orders`;

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.dim_date` AS
SELECT
  d AS date_key,
  EXTRACT(YEAR FROM d)       AS year,
  EXTRACT(QUARTER FROM d)    AS quarter,
  EXTRACT(MONTH FROM d)      AS month,
  FORMAT_DATE('%B', d)       AS month_name,
  EXTRACT(DAYOFWEEK FROM d)  AS day_of_week,
  EXTRACT(DAYOFWEEK FROM d) IN (1, 7) AS is_weekend
FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2025-12-31')) AS d;

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.fact_sales`
PARTITION BY order_date
CLUSTER BY region, category, customer_id
AS
SELECT
  order_id,
  order_date,
  customer_id,
  product_id,
  region,
  city,
  category,
  channel,
  quantity,
  unit_price,
  discount_pct,
  ROUND(quantity * unit_price * (1 - discount_pct / 100), 2) AS net_revenue
FROM `${PROJECT}.${DATASET}.stg_orders`;
