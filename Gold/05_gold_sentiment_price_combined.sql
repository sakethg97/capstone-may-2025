-- =========================================================================================
-- Gold Layer Materialized View: Combined Daily Sentiment & Price Metrics with Alignment Logic
-- =========================================================================================
-- This materialized view joins daily Reddit sentiment metrics with corresponding daily 
-- price metrics for each cryptocurrency symbol. It derives sentiment direction, price 
-- direction, and an alignment flag indicating whether sentiment and price movement agree.
-- This forms the foundation for downstream KPI calculations and correlation analysis.
-- =========================================================================================
CREATE MATERIALIZED VIEW sakethg_capstone_project_1_gold_sentiment_price_combined
COMMENT "Combined daily sentiment and price metrics with derived alignment indicators"
AS
SELECT 
    p.symbol,
    p.event_date,
    
    -- Sentiment metrics with missing values handled via COALESCE
    COALESCE(s.positive_mentions, 0) AS positive_mentions,
    COALESCE(s.negative_mentions, 0) AS negative_mentions,
    COALESCE(s.neutral_mentions, 0) AS neutral_mentions,
    COALESCE(s.total_mentions, 0) AS total_mentions,

    -- Price metrics
    p.open_price,
    p.close_price,
    p.price_change_pct,

    -- Derived sentiment direction based on positive vs. negative mentions
    CASE 
        WHEN s.positive_mentions > s.negative_mentions THEN 'positive_day'
        WHEN s.negative_mentions > s.positive_mentions THEN 'negative_day'
        ELSE 'neutral_day'
    END AS sentiment_direction,

    -- Derived price direction based on price change percentage
    CASE 
        WHEN p.price_change_pct > 0 THEN 'positive_day'
        WHEN p.price_change_pct < 0 THEN 'negative_day'
        ELSE 'price_flat'
    END AS price_direction,

    -- Alignment flag: 1 if sentiment direction matches price direction
    CASE 
        WHEN (s.positive_mentions > s.negative_mentions AND p.price_change_pct > 0) OR 
             (s.negative_mentions > s.positive_mentions AND p.price_change_pct < 0) THEN 1
        ELSE 0
    END AS aligned_flag

FROM tabular.dataexpert.sakethg_capstone_project_1_gold_daily_prices p
LEFT JOIN tabular.dataexpert.sakethg_capstone_project_1_gold_daily_sentiment s -- Left join to retain all price records even if sentiment is missing
  ON p.symbol = s.symbol
  AND p.event_date = s.event_date
WHERE p.event_date > '2025-06-01'; -- Optional filter to limit to recent data
