# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - DLT Notebook: Reddit Sentiment & Crypto Prices Ingestion Pipeline
# MAGIC --------------------------------------------------------------------------------
# MAGIC ## Description
# MAGIC
# MAGIC This notebook implements an end-to-end Delta Live Tables (DLT) pipeline for ingesting, cleansing, and enriching both Reddit sentiment data and CoinGecko crypto price data. The pipeline follows an enterprise-grade multi-layer architecture with Raw, Bronze, and Silver layers for both datasets.
# MAGIC
# MAGIC --------------------------------------------------------------------------------
# MAGIC
# MAGIC ### Key Features:
# MAGIC
# MAGIC -  **Autoloader ingestion** from cloud volumes with schema evolution and inference  
# MAGIC -  **Data quality enforcement** using `expect_or_drop`, `expect`, and `expect_or_fail` constraints  
# MAGIC -  **Deduplication** and quarantine handling for invalid or incomplete records  
# MAGIC -  **Regex-based sentiment scoring** for Reddit posts (Bullish, Bearish, Neutral)  
# MAGIC -  **AI sentiment enrichment** via `ai_analyze_sentiment` for advanced text classification  
# MAGIC -  **Symbol derivation** from post keywords to standardize crypto asset representation  
# MAGIC -  **Clean, curated Silver tables** prepared for downstream analytics, joins, and reporting  
# MAGIC
# MAGIC This notebook serves as the foundation for the capstone project's real-time data pipeline, supporting sentiment-price correlation analysis, KPI generation, and dashboarding.
# MAGIC

# COMMAND ----------

# --------------------------------------------------------------------------------
# Import Libraries
# --------------------------------------------------------------------------------
import dlt
from pyspark.sql.functions import *

# COMMAND ----------

# --------------------------------------------------------------------------------
# Configurable Parameters
# --------------------------------------------------------------------------------
project_prefix = "sakethg_capstone_project_1"

# Sentiment Tables
raw_sentiment_table = f"{project_prefix}_raw_sentiment"
bronze_sentiment_table = f"{project_prefix}_bronze_sentiment"
silver_sentiment_table = f"{project_prefix}_silver_sentiment"
quarantine_bronze_sentiment_table = f"{project_prefix}_bronze_reddit_quarantine"

# Prices Tables
raw_prices_table = f"{project_prefix}_raw_prices"
bronze_prices_table = f"{project_prefix}_bronze_prices"
silver_prices_table = f"{project_prefix}_silver_prices"

# Paths for Volumes & Schema Tracking
volume_path_reddit = "/Volumes/tabular/dataexpert/sakethg/capstone/raw/reddit_sentiment"
schema_location_reddit = "/Volumes/tabular/dataexpert/sakethg/capstone/schema_tracking/raw/reddit_sentiment"
volume_path_prices = "/Volumes/tabular/dataexpert/sakethg/capstone/raw/crypto_prices"
schema_location_prices = "/Volumes/tabular/dataexpert/sakethg/capstone/schema_tracking/raw/prices"

# --------------------------------------------------------------------------------
# Sentiment Keyword Patterns
# --------------------------------------------------------------------------------
bullish_pattern = """bullish|pump|moon|rocket|breakout|rally|green|ATH|accumulation|strong support|moonshot|buy|uptrend|HODL|bullrun|new high|diamond hands|parabolic|squeeze|massive gains|bullish reversal|holding|entry point|support level|oversold|undervalued|next leg up|break resistance|price discovery|bullish sentiment|run up|skyrocket"""
bearish_pattern = """bearish|crash|dump|fear|FUD|selloff|red|capitulation|breakdown|resistance failure|liquidation|rug pull|scam|manipulation|bloodbath|panic|sell pressure|fake pump|trend reversal|weak hands|market crash|bear flag|sell wall|overbought|price rejection|failed breakout|bearish divergence|short squeeze fail|downtrend|lower low|death cross|bleeding"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reddit Sentiment Tables

# COMMAND ----------

# --------------------------------------------------------------------------------
# Raw Layer - Reddit Sentiment (Autoloader)
# --------------------------------------------------------------------------------
# Ingest raw Reddit sentiment JSON data from Volume using Autoloader.
# Includes schema evolution and quality constraints to drop bad records.
@dlt.table(name=raw_sentiment_table, comment="Raw Reddit Sentiment - Autoloader Ingest")
@dlt.expect_or_drop("non_null_post_id", "post_id IS NOT NULL")
@dlt.expect_or_drop("valid_created_utc", "created_utc IS NOT NULL")
def raw_reddit():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", schema_location_reddit)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "post_id STRING, created_utc TIMESTAMP")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("cloudFiles.includeExistingFiles", "true")
        .load(volume_path_reddit)
        .withColumn("record_source", lit("reddit"))
    )

# COMMAND ----------

# --------------------------------------------------------------------------------
# Bronze Layer - Clean & Deduplicated Reddit Sentiment
# --------------------------------------------------------------------------------
# Structures raw Reddit data, applies non-critical expectations, and deduplicates records.
@dlt.table(name=bronze_sentiment_table, comment="Bronze Reddit - Clean, Deduped")
@dlt.expect("non_null_text", "text IS NOT NULL")
@dlt.expect("non_empty_text", "length(trim(text)) > 0")
@dlt.expect("non_null_subreddit", "subreddit IS NOT NULL")
@dlt.expect("non_null_keyword", "keyword IS NOT NULL")
def bronze_reddit():
    return (
        dlt.read_stream(raw_sentiment_table)
        .select("post_id", "text", "created_utc", "subreddit", "keyword", "record_source")
        .withColumnRenamed("created_utc", "created_ts")
        .withColumn("event_date_reddit", to_date(col("created_ts")))
        .dropDuplicates(["post_id"])
    )

# --------------------------------------------------------------------------------
# Quarantine Table - Reddit Bronze Failures
# --------------------------------------------------------------------------------
# Captures records failing expectations for investigation
@dlt.table(name=quarantine_bronze_sentiment_table, comment="Bronze Reddit Quarantine")
def bronze_quarantine():
    return dlt.read_stream(raw_sentiment_table).filter("text IS NULL OR trim(text) = '' OR subreddit IS NULL OR keyword IS NULL")

# COMMAND ----------

# --------------------------------------------------------------------------------
# Silver Layer - Sentiment Scoring & AI Labeling
# --------------------------------------------------------------------------------
# Adds:
#   - Sentiment score based on text pattern matching
#   - Symbol derivation from keyword
#   - AI-generated sentiment label via ai_analyze_sentiment()
# Strict expectations applied to enforce critical data quality.
@dlt.table(name=silver_sentiment_table, comment="Silver Reddit - Sentiment Scored and labeled")
@dlt.expect_or_fail("non_null_post_id", "post_id IS NOT NULL")
@dlt.expect_or_fail("valid_created_ts", "created_ts IS NOT NULL")
def silver_reddit():
    return (
        dlt.read_stream(bronze_sentiment_table)
        .dropDuplicates(["post_id"])
        .withColumn(
            "sentiment_score",
            when(lower(col("text")).rlike(bullish_pattern), lit(1))
            .when(lower(col("text")).rlike(bearish_pattern), lit(-1))
            .otherwise(lit(0)))
        .withColumn(
            "symbol",
            when(lower(col("keyword")).isin("bitcoin", "btc"), lit("BTC"))
            .when(lower(col("keyword")).isin("ethereum", "eth"), lit("ETH"))
            .when(lower(col("keyword")).isin("binance", "bnb"), lit("BNB"))
            .when(lower(col("keyword")).isin("solana", "sol"), lit("SOL"))
            .when(lower(col("keyword")).isin("ripple", "xrp"), lit("XRP"))
            .when(lower(col("keyword")).isin("dogecoin", "doge"), lit("DOGE"))
            .when(lower(col("keyword")).isin("cardano", "ada"), lit("ADA"))
            .when(lower(col("keyword")).isin("polkadot", "dot"), lit("DOT"))
            .otherwise(lit("UNKNOWN")))
        .withColumn(
            "sentiment_label",
            expr("ai_analyze_sentiment(text)"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Crypto Prices Tables

# COMMAND ----------

# --------------------------------------------------------------------------------
# Raw Layer - Crypto Prices (Autoloader)
# --------------------------------------------------------------------------------
# Ingests raw crypto price JSON data from Volume using Autoloader.
# Includes schema evolution and critical quality checks via expect_or_drop.
@dlt.table(name=raw_prices_table, comment="Raw Prices - Autoloader Ingest")
@dlt.expect_or_drop("non_null_symbol", "symbol IS NOT NULL")
@dlt.expect_or_drop("valid_timestamp", "timestamp IS NOT NULL")
def raw_prices():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", schema_location_prices)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("cloudFiles.includeExistingFiles", "true")
        .load(volume_path_prices)
        .withColumn("record_source", lit("CoinGecko"))
    )

# COMMAND ----------

# --------------------------------------------------------------------------------
# Bronze Layer - Structured & Deduplicated Crypto Prices
# --------------------------------------------------------------------------------
# Structures raw price data, applies expectations for basic quality, and deduplicates 
# records based on symbol and timestamp to avoid duplicate entries.
@dlt.table(name=bronze_prices_table, comment="Bronze Prices - Structured")
@dlt.expect("non_null_timestamp", "timestamp IS NOT NULL")
@dlt.expect("non_null_open", "open IS NOT NULL")
@dlt.expect("non_null_high", "high IS NOT NULL")
@dlt.expect("non_null_low", "low IS NOT NULL")
@dlt.expect("non_null_close", "close IS NOT NULL")
@dlt.expect("non_null_symbol", "symbol IS NOT NULL")
def bronze_prices():
    return (
        dlt.read_stream(raw_prices_table)
        .select("symbol", "open", "high", "low", "close", "timestamp", "record_source")
        .dropDuplicates(["symbol", "timestamp"])
    )


# --------------------------------------------------------------------------------
# Quarantine Table - Prices Bronze Failures
# --------------------------------------------------------------------------------
# Captures records missing essential fields (symbol, timestamp, OHLC values).
# Enables investigation and potential recovery of bad data.
@dlt.table(name=f"{project_prefix}_bronze_prices_quarantine", comment="Bronze Prices Quarantine")
def bronze_prices_quarantine():
    return dlt.read_stream(raw_prices_table).filter("symbol IS NULL OR timestamp IS NULL OR open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL")

# COMMAND ----------

# --------------------------------------------------------------------------------
# Silver Layer - Cleaned Crypto Prices
# --------------------------------------------------------------------------------
# Enforces strict quality expectations via expect_or_fail and produces curated, 
# deduplicated price data ready for downstream consumption.
@dlt.table(name=silver_prices_table, comment="Silver Prices - Cleaned")
@dlt.expect_or_fail("non_null_symbol", "symbol IS NOT NULL")
@dlt.expect_or_fail("valid_timestamp", "timestamp IS NOT NULL")
def silver_prices():
    return (
        dlt.read_stream(bronze_prices_table)
        .dropDuplicates(["symbol", "timestamp"])
    )
