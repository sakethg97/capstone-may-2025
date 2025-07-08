-- =========================================================================================
-- Gold Layer Materialized View: Daily Open, Close, and Price Change Percentage per Symbol
-- =========================================================================================
-- This materialized view aggregates daily open and close prices for each cryptocurrency 
-- symbol and calculates the corresponding daily price change percentage. It is designed 
-- for efficient downstream consumption in dashboards, KPI calculations, and trend analysis.
-- =========================================================================================
CREATE MATERIALIZED VIEW sakethg_capstone_project_1_gold_daily_prices
COMMENT "Daily open, close and price change percentage per symbol"
AS
-- Prepare price data with derived event_date (date component of timestamp)
WITH price_with_date AS (
  SELECT
    symbol,
    timestamp,
    DATE(timestamp) AS event_date,
    open,
    close
  FROM sakethg_capstone_project_1_silver_prices
),

-- Extract daily open and close prices per symbol using window functions
daily_open_close AS (
  SELECT
    symbol,
    event_date,
    
    -- First observed open price of the day
    FIRST(open) IGNORE NULLS 
      OVER (PARTITION BY symbol, event_date ORDER BY timestamp ASC) AS open_price,
    
    -- Last observed close price of the day
    LAST(close) IGNORE NULLS 
      OVER (PARTITION BY symbol, event_date ORDER BY timestamp ASC) AS close_price
  FROM price_with_date
)

-- Final daily aggregation and price change calculation
SELECT
  symbol,
  event_date,
  FIRST(open_price) AS open_price,
  FIRST(close_price) AS close_price,
  ROUND(((FIRST(close_price) - FIRST(open_price)) / FIRST(open_price)) * 100, 2) AS price_change_pct -- Price change percentage: (close - open) / open * 100, rounded to 2 decimals
FROM daily_open_close
GROUP BY symbol, event_date;