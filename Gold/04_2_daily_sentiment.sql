-- =========================================================================================
-- Gold Layer Materialized View: Daily Reddit Sentiment Aggregation per Symbol
-- =========================================================================================
-- This materialized view aggregates daily Reddit sentiment metrics for each cryptocurrency 
-- symbol based on AI-generated sentiment labels. The output provides counts of positive, 
-- negative, neutral, and total mentions per symbol and day, supporting correlation analysis 
-- with price movements and downstream KPIs.
-- =========================================================================================
CREATE MATERIALIZED VIEW sakethg_capstone_project_1_gold_daily_sentiment
COMMENT "Daily Reddit sentiment aggregation per symbol"
AS
SELECT 
    symbol,
    event_date_reddit AS event_date, -- Extract event_date from Reddit post timestamp
    SUM(CASE WHEN lower(sentiment_label) = 'positive' THEN 1 ELSE 0 END) AS positive_mentions, -- Count of posts classified as positive sentiment (case-insensitive)

    SUM(CASE WHEN lower(sentiment_label) = 'negative' THEN 1 ELSE 0 END) AS negative_mentions, -- Count of posts classified as negative sentiment
    SUM(CASE WHEN lower(sentiment_label) = 'neutral' THEN 1 ELSE 0 END) AS neutral_mentions, -- Count of posts classified as neutral sentiment
    COUNT(*) AS total_mentions -- Total number of Reddit mentions for the symbol on that day
FROM sakethg_capstone_project_1_silver_sentiment
GROUP BY symbol, event_date_reddit; -- Group by symbol and event_date to produce daily aggregates
