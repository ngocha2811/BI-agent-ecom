# E-Commerce BI Agent

An AI-powered Business Intelligence application for e-commerce analytics. It combines a live KPI dashboard with a conversational agent that answers natural language questions about sales, products, advertising, and margins — backed by a local MySQL database and powered by the Grok API.

Created by 
Ngoc Ha Nguyen
> 🔗 **[LinkedIn → Let's Connect](https://www.linkedin.com/in/hannah-ngocha-nguyen/)**

## Features

- **Live KPI Dashboard** — Sales, margin, profit, ad spend, and returns at a glance with period filtering (last 30 / 60 / 90 days)
- **Channel Breakdown** — Weekly stacked bar chart and revenue share donut across Amazon FBA, Amazon FMN, and Shopify
- **Product Performance** — Top 10 products by profit (gross margin vs. profit after ads)
- **Returns Analysis** — Return rate by channel and top returned SKUs
- **Conversational BI Agent** — Ask any business question in natural language; the agent generates MySQL queries and returns both a data table and a written insight
- **Interactive Charts** — Ask for bar, line, area, scatter, or pie charts from the agent
- **Auto-Bootstrap** — On first run the app creates the MySQL schema and imports all 5 CSVs automatically
- **Query Transparency** — Every agent response shows the SQL query in an expandable section

## Data Sources
*The dataset is synthetically generated based on simplified real business data.*

| File | Description | Rows |
|---|---|---|
| `amz_orders.csv` | Amazon order history (2024) | ~11,500 |
| `shopify_orders.csv` | Shopify order history (Sep 2025 →) | ~920 |
| `products.csv` | Product catalogue — SKU, name, category, cost | 30 |
| `amz_ads.csv` | Amazon Ads — spend, clicks, ROAS by SKU & country | 50 |
| `meta_ads.csv` | Meta Ads (Facebook/Instagram) — spend, impressions, clicks by SKU | 30 |

## Prerequisites

- Python 3.10+
- MySQL running locally (any version 8+)
- A Grok API key from [console.x.ai](https://console.x.ai)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/BI-data-ai-agent.git
cd BI-data-ai-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the MySQL database

The app creates the tables and imports the data automatically, but the database itself must exist first:

```sql
CREATE DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure environment variables

Copy `.env.sample` to `.env` and fill in your values:

```bash
cp .env.sample .env
```

```bash
# Grok API key — https://console.x.ai
XAI_API_KEY=your_xai_api_key_here

# MySQL connection string
LOCAL_CONNECTION_STRING=mysql+pymysql://root:your_password@localhost:3306/ecommerce
```

### 5. Run the app

```bash
streamlit run app.py
```

On the first launch, the app will print bootstrap logs as it creates all 5 tables and imports the CSVs, then open the dashboard.

## Usage

### Dashboard

The top section of the page is a static KPI dashboard loaded directly from the CSV files. Use the **Period** radio button (top right) to switch between last 30, 60, and 90 days.

### BI Agent

Scroll to the bottom of the page to reach the chat interface. The agent can:

- Run MySQL queries and display the results as a table
- Render interactive charts (bar, line, area, scatter, pie)
- Follow up each result with a 2–3 sentence written business insight

**Example questions:**

```
What is the total revenue by product category?
Show me monthly Amazon sales as a line chart
Which SKUs have the highest ROAS on Amazon Ads?
What is the gross margin per product on Shopify?
Bar chart of ad spend by platform
Which products were returned most often?
Compare revenue between Amazon and Shopify
What are the top 10 products by profit after ad spend?
```

## Project Structure

```
BI-data-ai-agent/
├── e-commerce_data/               # Source CSV files (read-only)
│   ├── amz_orders.csv
│   ├── shopify_orders.csv
│   ├── products.csv
│   ├── amz_ads.csv
│   └── meta_ads.csv
├── ai/
│   ├── agent.py                   # Two-call Grok agent (query → insight)
│   ├── tools.py                   # get_data_df and create_chart tools
│   ├── prompts.py                 # System prompt with schema and MySQL rules
│   ├── ecommerce_schema.py        # Full schema string injected into the prompt
│   └── utils.py                   # SQLAlchemy connection helpers
├── db/
│   ├── schema.py                  # CREATE TABLE DDL for all 5 tables
│   └── loader.py                  # Bootstrap: check → create → import CSVs
├── dashboard/
│   └── dashboard.py               # Static KPI dashboard (Plotly + pandas)
├── app.py                         # Streamlit entry point
├── .env.sample                    # Environment variable template
├── requirements.txt               # Python dependencies
└── README.md
```

## Architecture

```
Browser
  └── Streamlit (app.py)
        ├── Dashboard (dashboard/dashboard.py)
        │     └── reads CSVs directly via pandas
        └── BI Agent (ai/agent.py)
              ├── Call 1 → Grok-3-mini (tool calling)
              │     └── tool: get_data_df  → MySQL → st.dataframe
              │     └── tool: create_chart → MySQL → st.plotly_chart
              └── Call 2 → Grok-3-mini (plain text)
                    └── interprets query results → written insight
```

**Database layer** (`db/loader.py`) runs on every app start. It checks whether the `products` table has rows; if any table is empty it truncates and re-imports all CSVs from `e-commerce_data/`.

## Key Technical Details

- **Model**: `grok-3-mini` via the xAI API (OpenAI-compatible SDK)
- **Database**: MySQL with PyMySQL + SQLAlchemy
- **Insight generation**: After every query the agent makes a second Grok call (no tools, capped at 50 rows) to generate a 2–3 sentence business interpretation
- **Date grouping**: The system prompt enforces MySQL `DATE_FORMAT(order_date, '%Y-%m')` — never PostgreSQL `DATE_TRUNC`
- **Business context baked into the prompt**: the agent knows Amazon orders are from 2024, Shopify from September 2025, and that product `price` is the unit cost in EUR (not the sale price)

## Tech Stack

| Library | Purpose |
|---|---|
| `openai` | Grok API client (xAI, OpenAI-compatible) |
| `streamlit` | Web UI and chat interface |
| `plotly` | Interactive charts in dashboard and agent |
| `pandas` | Data manipulation and CSV loading |
| `sqlalchemy` + `pymysql` | MySQL connection and query execution |
| `python-dotenv` | Environment variable management |

## License

MIT License — see `LICENSE` for details.
