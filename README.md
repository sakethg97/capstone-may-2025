# 📊 Crypto Sentiment & Price Correlation Capstone

**Author:** Saketh Gadde  

---

## 🚀 Objective

This project analyzes the correlation between Reddit sentiment and cryptocurrency price movements using a robust Delta Live Tables (DLT) pipeline in Databricks. The goal is to determine whether crowd sentiment from Reddit can serve as a reliable indicator of market direction.

---

## 📚 Pipeline Architecture

The pipeline follows the Medallion Architecture pattern with Raw → Bronze → Silver → Gold layers.

### 🔁 Data Sources

| Source     | Description                              |
|------------|------------------------------------------|
| Reddit     | Crypto-related post titles via Reddit API (`praw`) |
| CoinGecko  | OHLC price data for major crypto assets via REST API |


## 🧠 Why These Datasets?

Reddit is a leading source of community sentiment around cryptocurrency. Its crypto-focused subreddits contain timely, opinion-rich discussions that reflect retail market psychology. CoinGecko provides reliable, granular OHLC price data through a free and well-documented API, making it ideal for academic and production-grade correlation analysis.

## 🔀 Alternatives Considered

- **Static Reddit data** from Kaggle → Rejected due to lack of freshness and no control over keywords.
- **Using Twitter data** → More noisy and harder to access at scale due to API limitations.

---

## 📂 Notebooks & SQL Scripts

### 1. `01_Raw_Reddit_Sentiment_Ingestion.py`
- Fetches recent Reddit posts from major crypto subreddits
- Filters posts based on keywords
- Writes structured JSON to the raw volume

### 2. `02_Raw_Crypto_Prices_Ingestion.py`
- Ingests OHLC price data from CoinGecko API
- Supports configurable batch size and days
- Handles API rate limiting gracefully

### 3. `Raw_Bronze_Silver/03_Raw_Bronze_Silver.py`
- Defines Delta Live Tables for:
  - Raw Reddit & Price ingestion
  - Bronze layer with expectations and deduplication
  - Silver layer with sentiment scoring (`regex` + `ai_analyze_sentiment`)
  - Symbol extraction and normalization

### 4. `Gold/04_1_daily_prices.sql`
- Creates a Gold materialized view summarizing daily open, close, and price % change per coin

### 5. `Gold/04_2_daily_sentiment.sql`
- Aggregates daily sentiment metrics: counts of positive, negative, and neutral Reddit posts

### 6. `Gold/05_gold_sentiment_price_combined.sql`
- Joins sentiment and price data per symbol/day
- Derives:
  - `sentiment_direction` vs `price_direction`
  - `aligned_flag` indicating if sentiment matched market behavior

### 7. `06_Dimensions_Setup.sql`
- Creates dimension tables for a star schema:
  - `dim_symbol` (coin metadata)
  - `dim_date` (calendar dimension for 2025)
  - `dim_sentiment_direction` (label + color mapping)

---

## 🧪 Features & Highlights

- ✅ Fully parameterized ingestion via widgets
- ✅ Handles schema evolution and data quality with DLT expectations
- ✅ Leverages Databricks `ai_analyze_sentiment()` for enrichment
- ✅ Uses materialized views for gold layer optimization
- ✅ Supports downstream BI dashboards and KPI queries
- ✅ Aligns with DataExpert’s enterprise-grade capstone guidelines

## ⚙️ Why Delta Live Tables (DLT)?

DLT allows for declarative pipeline design with built-in data quality enforcement, schema inference, and orchestration support. It ensures modular, production-grade ETL logic that can evolve seamlessly as new data and schema changes occur. DLT also integrates well with Unity Catalog, Autoloader, and other core Databricks services.

---

## 🗃️ Data Model (Star Schema)
### 🔸 Fact Table: `gold_sentiment_price_combined`
Contains daily sentiment and price metrics per symbol and date, with alignment flags and direction indicators.

### 🔹 Dimension Tables:
- **`dim_symbol`** – Coin metadata (name, category)
- **`dim_date`** – Calendar attributes (month, weekday, is_weekend)
- **`dim_sentiment_direction`** – Mapping for sentiment labels and chart color codes

This model supports flexible filtering, time-series grouping, and enhanced visualization

## 🧱 Why This Data Model?

A star schema simplifies joins, supports semantic modeling, and keeps the fact table normalized. It enables efficient filtering and aggregations on common dimensions like `symbol`, `event_date`, and `sentiment_direction`, making it ideal for reporting and downstream BI tools. Dimension tables decouple the business context from ingestion logic.

---

## ▶️ How to Run

1. Set up credentials (Reddit API via Databricks secrets)
2. Run Notebooks 1 & 2 to populate raw volumes
3. Deploy DLT pipeline via Notebook 3
4. Run Gold SQL scripts to create materialized views
5. Create dashboard or KPIs from `gold_sentiment_price_combined`

---

## 🔄 DAG & Execution Flow

- The following DAG shows the ingestion, DLT pipeline layers, and Gold-layer materialized views.  
![output](https://github.com/user-attachments/assets/584e0d6f-85b4-4bf9-aec6-4298d5ffd1fd)


---

## 🖼️ Succesfull Pipeline Runs and Visualization Charts

- Screenshot of successful pipeline run DAG
<img width="1181" alt="Screenshot 2025-07-07 at 18 32 41" src="https://github.com/user-attachments/assets/f0e801ce-d2bd-4048-add7-c86928c583d3" />


- Screenshot of successful pipeline run Tables
<img width="755" alt="Screenshot 2025-07-07 at 18 36 05" src="https://github.com/user-attachments/assets/4a936707-3ddd-4fc5-a509-266a668f43d4" />


- Sample KPI showing correlation between reddit sentiment and prices daily for a single coin (Eg. BTC)
<img width="1242" alt="Screenshot 2025-07-07 at 18 59 19" src="https://github.com/user-attachments/assets/a77f0e1d-14f7-4c2d-95f6-2dc186b2b4a9" />

---

## 🧠 Analytical Takeaway: Does Reddit Sentiment Influence Price?

Through the combined dataset of Reddit sentiment and CoinGecko OHLC price data, we computed alignment metrics to evaluate the correlation between **daily sentiment direction** and **price movement**.

Across the board, results were mixed:

- Coins like **Bitcoin (BTC)** demonstrated a higher **alignment percentage**, indicating that bullish or bearish sentiment days often matched price trends (e.g., upward movement on bullish sentiment days).
- However, for most other tokens, the **alignment between Reddit sentiment and actual price changes** was either weak or statistically insignificant.

### 📌 Conclusion from KPI Analysis

> **Reddit sentiment is not a consistent predictor of price movement across all symbols.**

While community sentiment may occasionally influence high-volume tokens or during major market events, our KPI-driven analysis suggests that:
- Sentiment data **alone** is **not sufficient** for price prediction.
- Broader market factors, trading volumes, and technical indicators likely play a **stronger role** in short-term price fluctuations.

### ✅ Implications

This reinforces the importance of:
- **Quantitative validation** of hypotheses before incorporating alternative data sources like Reddit into trading strategies.
- Designing **multi-factor analytical models** when building production-grade financial systems.
- Leveraging sentiment data more as a **complementary signal**, rather than a primary driver.

---

## 📈 Expansion Opportunities

This project provides a strong foundation, and several enhancements could take it to a production-grade analytical system:

### 🔄 Real-Time Ingestion & Processing
- Upgrade Reddit ingestion to **streaming pipelines** using [Pushshift.io](https://pushshift.io), **Kafka**, or **Reddit’s WebSocket feeds**.
- Move CoinGecko data to a **Delta Live Tables streaming source**, or explore **CoinAPI** for more granular real-time price updates.

### 🧠 Smarter Sentiment & Anomaly Detection
- Integrate **Twitter data via Twitter API v2**, expanding sentiment analysis across platforms.
- Add **keyword co-occurrence**, **topic modeling**, or **word cloud analytics** for richer NLP features.
- Detect sentiment **volatility spikes** and send **alerts** via Slack, email, or Databricks SQL alerting.

### 🔮 Predictive Modeling
- Train ML models to forecast **next-day price movement** based on rolling sentiment and volume.
- Classify coins into **"sentiment-sensitive" vs "market-driven"** categories using clustering algorithms.

### 📊 Dashboard & Reporting
- Push aligned signal outputs to **auto-refreshed dashboards** or **scheduled reports** for stakeholders.
- Build an executive summary dashboard that highlights:
  - Daily alignment stats
  - Sentiment surges
  - Unexpected sentiment-price divergence
  
### 🚀 Scaling & Distribution
- Orchestrate jobs using **Databricks Workflows**, **Airflow**, or **Dagster**.
- Build a **modular REST API or webhook system** that external tools can use to pull sentiment-aligned metrics.
- Store enriched datasets in **Unity Catalog volumes**, making them accessible across departments.



These additions would enable this project to evolve from an exploratory capstone into a robust, enterprise-ready data product.

---

## 🙌 Acknowledgements

- Built for the **DataExpert.io Capstone Program**
- Uses core Databricks components: Autoloader, DLT, Unity Catalog, AI Functions

---


