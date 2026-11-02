-- Staging table: raw CSV loaded as-is (see load_to_bigquery.py).
-- Replace ${PROJECT} and ${DATASET} with your values, or run via the loader script.

CREATE SCHEMA IF NOT EXISTS `${PROJECT}.${DATASET}`;

CREATE OR REPLACE TABLE `${PROJECT}.${DATASET}.stg_orders` (
  order_id      STRING,
  order_date    DATE,
  customer_id   STRING,
  customer_name STRING,
  segment       STRING,
  region        STRING,
  city          STRING,
  product_id    STRING,
  product_name  STRING,
  category      STRING,
  unit_price    NUMERIC,
  quantity      INT64,
  discount_pct  INT64,
  channel       STRING
);
