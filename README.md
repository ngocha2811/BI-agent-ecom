# E-Commerce BI Agent
<img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
<img src="https://img.shields.io/badge/PostgreSQL-Neon-green" alt="PostgreSQL">
<img src="https://img.shields.io/badge/Streamlit-live-red" alt="Streamlit">
<img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">

---

🚀 **[Live Demo → insight-ai-ecom.streamlit.app](https://insight-ai-ecom.streamlit.app/)**
![Streamlit App](/visuals/streamlit_app.gif)

---

**An AI-powered Business Intelligence** application for e-commerce analytics. It combines a live KPI dashboard with a conversational agent that answers natural language questions about sales, ad performance, and product revenue — backed by a cloud PostgreSQL database (Neon) and powered by the Grok API.

---

Author: 
Ngoc Ha Nguyen 🔗 **[LinkedIn → Let's Connect](https://www.linkedin.com/in/hannah-ngocha-nguyen/)**

---

## Why This Project

Most BI tools require SQL knowledge or dashboard access. 
This agent lets any stakeholder — technical or not — ask 
questions in plain English and get back data, a chart, 
and a written interpretation in one response.

Key engineering decisions:
- **Two-call LLM pattern**: first call generates SQL, 
  second call interprets the result — separating data 
  retrieval from insight generation
- **Cloud-first**: PostgreSQL on Neon means zero local 
  setup for anyone who clones the repo
- **Same AI core, two interfaces**: Streamlit for desktop 
  analysis, Telegram for on-the-go alerts — both share 
  identical agent and database logic

---

## Architecture

The project is built as three interconnected layers sharing the same data and AI core.

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA LAYER                           │
│                                                             │
│   amz_orders  │  shopify_orders  │  products               │
│   amz_ads     │  meta_ads                                   │
│                                                             │
│           PostgreSQL — Neon (cloud, persistent)             │
│         seeded once via: python db/loader.py                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       AI CORE                               │
│                                                             │
│   ai/agent.py      Grok-3-mini via xAI API                  │
│   ai/tools.py      get_data_df(sql) — SELECT only           │
│   ai/prompts.py    schema + column rules injected           │
│                                                             │
│   User question → Grok writes SQL → Query executes          │
│                → DataFrame returned → Grok interprets       │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌─────────────────────────────────┐
│   STREAMLIT APP      │   │        TELEGRAM BOT             │
│                      │   │                                 │
│   KPI Dashboard      │   │   /ask  → same AI core          │
│   - Total revenue    │   │   /report → scheduled summary   │
│   - ROAS by channel  │   │   /alert → KPI threshold alerts │
│   - Top products     │   │                                 │
│   - Ad spend         │   │   bot/bot.py                    │
│                      │   │   bot/handlers.py               │
│   Chat Agent         │   │   bot/prompts.py                │
│   - Natural language │   │                                 │
│   - Table + chart    │   │                                 │
│   - Insight text     │   │                                 │
└──────────────────────┘   └─────────────────────────────────┘
```

**Data flow for a question (Streamlit and Telegram):**
1. User asks a question in plain English
2. Grok-3-mini receives the question + full PostgreSQL schema in system prompt
3. Grok decides: write SQL (data question) or answer directly (interpretive)
4. If SQL: `tools.py` executes SELECT query against Neon, returns DataFrame
5. Grok makes a second call to interpret the DataFrame — writes a 2–3 sentence business insight
6. Response rendered as table + chart + insight (Streamlit) or formatted message (Telegram)

**Tech stack:**
| Layer | Technology |
|---|---|
| LLM | Grok-3-mini (xAI API) |
| Database | PostgreSQL — Neon (cloud) |
| ORM / data loading | SQLAlchemy + Pandas |
| Streamlit UI | Streamlit + Plotly |
| Telegram bot | python-telegram-bot |
| Version control | Git + GitHub |

---

## Data Sources

*The dataset is synthetically generated based on simplified real business data.*

| File | Description | Rows |
|---|---|---|
| `amz_orders.csv` | Amazon order history (2024) | ~11,500 |
| `shopify_orders.csv` | Shopify order history (Sep 2025 →) | ~920 |
| `products.csv` | Product catalogue — SKU, name, category, cost | 30 |
| `amz_ads.csv` | Amazon Ads — spend, clicks, ROAS by SKU & country | 50 |
| `meta_ads.csv` | Meta Ads (Facebook/Instagram) — spend, impressions, clicks by SKU | 30 |

> Amazon and Shopify date ranges do not overlap — this is intentional. The business started selling on Shopify in September 2025. All time-series queries use `DATE_TRUNC` grouping, not hardcoded date ranges.

---

## Prerequisites

- Python 3.10+
- A Grok API key from [console.x.ai](https://console.x.ai)
- A Neon account and project from [neon.tech](https://neon.tech) (free tier is sufficient)

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/ngocha2811/BI-agent-ecom.git
cd BI-agent-ecom
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.sample` to `.env` and fill in your values:

```bash
cp .env.sample .env
```

```bash
# Grok API key — https://console.x.ai
XAI_API_KEY=your_xai_api_key_here

# Neon PostgreSQL connection string — https://neon.tech
DATABASE_URL=postgresql+psycopg2://user:password@host/dbname

# Telegram bot token — from @BotFather (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### 4. Seed the database (one time only)

The Neon database is persistent — you only need to run this once to create the tables and import all 5 CSVs:

```bash
python db/loader.py
```

You should see:

```
✓ products: 30 rows loaded
✓ amz_orders: 11,500 rows loaded
✓ shopify_orders: 920 rows loaded
✓ amz_ads: 50 rows loaded
✓ meta_ads: 30 rows loaded
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## Usage

### Dashboard

The top section of the page is a KPI dashboard loaded directly from the database. Use the **Period** radio button (top right) to switch between last 30, 60, and 90 days.

### BI Agent

Scroll down to the chat interface. The agent can:

- Run SQL queries and display results as an interactive table
- Render charts (bar, line, area, scatter, pie) based on the data
- Follow up each result with a 2–3 sentence written business insight

**Example questions:**

```
What is the total revenue by product category?
Show me monthly Amazon sales as a line chart
Which SKUs have the highest ROAS on Amazon Ads?
Bar chart of ad spend by platform
Compare revenue between Amazon and Shopify
What are the top 10 products by profit after ad spend?
```

### Telegram Bot

Start the bot:

```bash
python chat_bot.py
```
Find the bot here: [InsightAI on Telegram](https://t.me/my_bi_assistant_bot)


<table>
<tr>
<td valign="top" width="60%">

**Example conversation:**

The bot accepts plain English questions and returns formatted answers directly in Telegram — no dashboard access needed.

Useful for checking KPIs on the go or sharing quick data points with non-technical stakeholders.

**Available commands:**

| Command | Description |
|---|---|
| `/ask [question]` | Ask any business question: sales, ad performance, and product revenue |
| `/alert` | Check if any KPIs have crossed defined alert thresholds |
| `/search` | Search web for general insights or information. For example: "search when is the next public holiday in Germany?" |


</td>
<td valign="top" width="40%">

![Telegram bot](visuals/telegram_bot.jpeg)

</td>
</tr>
</table>

---

## Project Structure

```
BI-agent-ecom/
├── ecommerce_data/                # Source CSV files (read-only)
│   ├── amz_orders.csv
│   ├── shopify_orders.csv
│   ├── products.csv
│   ├── amz_ads.csv
│   └── meta_ads.csv
├── ai/
│   ├── agent.py                   # Two-call Grok agent (query → insight)
│   ├── tools.py                   # get_data_df and chart tools
│   ├── prompts.py                 # System prompt with schema and business rules
│   ├── ecommerce_schema.py        # Full DDL schema injected into the prompt
│   └── utils.py                   # SQLAlchemy connection helpers
├── bot/
│   ├── bot.py                     # Telegram bot entry point
│   ├── handlers.py                # /ask, /report, /alert command handlers
│   └── prompts.py                 # Telegram-specific system prompt
├── db/
│   ├── schema.py                  # CREATE TABLE DDL for all 5 tables
│   └── loader.py                  # One-time seed script: create tables + import CSVs
├── dashboard/
│   └── dashboard.py               # KPI dashboard (Plotly + pandas)
├── app.py                         # Streamlit entry point
├── chat_bot.py                    # Telegram chat bot entry point
├── .env.sample                    # Environment variable template
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Key Technical Details

- **Model**: `grok-3-mini` via the xAI API (OpenAI-compatible client)
- **Database**: PostgreSQL on Neon — cloud persistent, no local setup needed
- **Insight generation**: After every query the agent makes a second Grok call (no tools, capped at 50 rows) to generate a 2–3 sentence business interpretation
- **Date grouping**: The system prompt enforces `DATE_TRUNC('month', order_date)` for all time-series queries
- **Safety**: All queries are SELECT-only — enforced in both the system prompt and in `tools.py` before execution
- **Business context baked into the prompt**: the agent knows Amazon orders are from 2024, Shopify from September 2025, and that product `price` is the unit cost in EUR (not the sale price)

---

## Author & License

Ngoc Ha Nguyen
> 🔗 **[LinkedIn → Let's Connect](https://www.linkedin.com/in/hannah-ngocha-nguyen/)**

MIT License — see `LICENSE` for details.