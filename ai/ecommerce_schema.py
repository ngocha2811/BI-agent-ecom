ECOMMERCE_SCHEMA = """
==================================================
DATABASE: ecommerce
==================================================

TABLES
------
- products
- amz_orders
- shopify_orders
- amz_ads
- meta_ads

==================================================
TABLE DEFINITIONS
==================================================

Table: products
---------------
  sku          VARCHAR(20)   PRIMARY KEY
  product_name VARCHAR(255)  NOT NULL
  category     VARCHAR(100)  -- values: Tablets, Computers, Headphones, Cameras, Smart Home
  price        DECIMAL(10,2) -- unit cost in EUR (intentionally low, e.g. €3 — not a data error)

Table: amz_orders
-----------------
  id           INT           PRIMARY KEY (auto-increment)
  order_date   DATETIME      NOT NULL   -- Amazon orders span 2024
  order_type   VARCHAR(50)              -- e.g. 'Order'
  order_id     VARCHAR(50)              -- Amazon order ID; NOT unique (multi-line orders)
  sku          VARCHAR(20)   FK → products.sku
  seller_type  VARCHAR(50)              -- e.g. 'Seller'
  sale_price   DECIMAL(10,2)            -- item sale price
  total_taxes  DECIMAL(10,2)
  fee          DECIMAL(10,2)            -- Amazon commission (stored as negative value)
  total_amount DECIMAL(10,2)            -- net amount received

Table: shopify_orders
---------------------
  id           INT           PRIMARY KEY (auto-increment)
  order_id     VARCHAR(50)              -- e.g. 'SHO-87854364'; NOT unique (same order_id for 'order' + 'return')
  sku          VARCHAR(20)   FK → products.sku
  order_date   DATETIME      NOT NULL   -- Shopify orders start September 2025
  order_type   VARCHAR(50)              -- 'order' or 'return'; returns have negative total_amount
  email        VARCHAR(255)
  total_amount DECIMAL(10,2)            -- negative for returns

Table: amz_ads
--------------
  id         INT           PRIMARY KEY (auto-increment)
  sku        VARCHAR(20)   FK → products.sku
  country    VARCHAR(100)  -- e.g. 'France', 'Germany'; multiple rows per SKU
  clicks     INT
  ctr        DECIMAL(8,6)  -- click-through rate (decimal, e.g. 0.0073 = 0.73%)
  total_cost DECIMAL(10,2) -- total ad spend in EUR
  cpc        DECIMAL(10,4) -- cost per click
  purchases  DECIMAL(10,2) -- number of purchases attributed to ads
  sales      DECIMAL(10,2) -- revenue attributed to ads in EUR
  roas       DECIMAL(12,6) -- return on ad spend = sales / total_cost
  -- NOTE: SKU-level snapshot (no date column). Join on sku only.

Table: meta_ads
---------------
  sku         VARCHAR(20)   PRIMARY KEY, FK → products.sku
  spend       DECIMAL(10,2) -- total Meta (Facebook/Instagram) ad spend in EUR
  impressions INT
  clicks      INT
  -- NOTE: SKU-level snapshot (no date or country column). Join on sku only.

==================================================
FOREIGN KEY RELATIONSHIPS
==================================================

- amz_orders.sku     → products.sku
- shopify_orders.sku → products.sku
- amz_ads.sku        → products.sku
- meta_ads.sku       → products.sku

==================================================
KEY JOIN PATHS
==================================================

Revenue by product (Amazon):
  SELECT p.sku, p.product_name, SUM(o.total_amount) AS revenue
  FROM amz_orders o JOIN products p ON o.sku = p.sku
  GROUP BY p.sku, p.product_name

Revenue by product (Shopify):
  SELECT p.sku, p.product_name, SUM(o.total_amount) AS revenue
  FROM shopify_orders o JOIN products p ON o.sku = p.sku
  GROUP BY p.sku, p.product_name

Combined revenue across channels (UNION):
  SELECT sku, total_amount, 'amazon' AS channel FROM amz_orders
  UNION ALL
  SELECT sku, total_amount, 'shopify' AS channel FROM shopify_orders

Amazon ROAS by SKU:
  SELECT a.sku, p.product_name, SUM(a.sales) AS ad_sales, SUM(a.total_cost) AS ad_spend,
         SUM(a.sales) / NULLIF(SUM(a.total_cost), 0) AS roas
  FROM amz_ads a JOIN products p ON a.sku = p.sku
  GROUP BY a.sku, p.product_name

Gross margin per SKU (Amazon):
  SELECT o.sku, p.product_name,
         AVG((o.sale_price - p.price + o.fee) / NULLIF(o.sale_price, 0)) AS avg_margin
  FROM amz_orders o JOIN products p ON o.sku = p.sku
  GROUP BY o.sku, p.product_name
  -- fee is negative; adding it subtracts the commission from the margin

==================================================
BUSINESS CONTEXT
==================================================

1. Amazon orders date from 2024. Shopify was launched in September 2025.
   There is NO temporal overlap between channels — this is correct business history.
   When analysing trends over time, use EXTRACT(YEAR FROM ...) or TO_CHAR(..., 'YYYY-MM') to separate periods.

2. Product prices in the products table are in EUR and are intentionally low (e.g. €3).
   These represent unit costs, not sale prices. Order revenue in the hundreds is normal
   and correct. Do NOT flag product prices as a data error.

3. amz_ads and meta_ads are period-level snapshots without dates.
   They represent cumulative or summary ad performance per SKU.
   Do NOT attempt date-based joins with these tables.
  
4. The total sales is the sum of the sales_amount column in the sales table.
5. Just ignore the fee column in the sales table.
6. amz_ads.csv and meta_ads.csv are snapshot of the ads data from 01.01.2026 until now so there is no date column. 
7. COGS is the column price in products table.
8. Margin is total_amount - COGS.

"""
