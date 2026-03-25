"""
CREATE TABLE DDL for the e-commerce BI database (PostgreSQL / Neon).
Tables must be created in this order to satisfy FK constraints:
  1. products  (referenced by all others)
  2. amz_orders
  3. shopify_orders
  4. amz_ads
  5. meta_ads
"""

CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    sku          VARCHAR(20)  NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category     VARCHAR(100),
    price        DECIMAL(10,2),
    -- NOTE: price is intentionally low (e.g. €3). This is the unit cost in EUR,
    -- not the sale price. Do not treat as a data error.
    PRIMARY KEY (sku)
);
"""

CREATE_AMZ_ORDERS = """
CREATE TABLE IF NOT EXISTS amz_orders (
    id             SERIAL        NOT NULL,
    order_date     TIMESTAMP     NOT NULL,
    order_type     VARCHAR(50),
    order_id       VARCHAR(50),
    sku            VARCHAR(20),
    seller_type    VARCHAR(50),
    sale_price     DECIMAL(10,2),
    total_taxes    DECIMAL(10,2),
    fee            DECIMAL(10,2),
    total_amount   DECIMAL(10,2),
    PRIMARY KEY (id),
    CONSTRAINT fk_amz_orders_sku FOREIGN KEY (sku) REFERENCES products(sku)
);
"""

CREATE_AMZ_ORDERS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_amz_order_date ON amz_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_amz_order_id   ON amz_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_amz_sku        ON amz_orders (sku);
"""

CREATE_SHOPIFY_ORDERS = """
CREATE TABLE IF NOT EXISTS shopify_orders (
    id           SERIAL        NOT NULL,
    order_id     VARCHAR(50),
    sku          VARCHAR(20),
    order_date   TIMESTAMP     NOT NULL,
    order_type   VARCHAR(50),
    email        VARCHAR(255),
    total_amount DECIMAL(10,2),
    -- NOTE: Shopify orders start from September 2025. Amazon orders are from 2024.
    -- There is no temporal overlap between channels — this is correct business history.
    -- order_id is not unique: the same order_id can appear as both 'order' and 'return'.
    PRIMARY KEY (id),
    CONSTRAINT fk_shopify_orders_sku FOREIGN KEY (sku) REFERENCES products(sku)
);
"""

CREATE_SHOPIFY_ORDERS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_shopify_order_id   ON shopify_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_shopify_order_date ON shopify_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_shopify_sku        ON shopify_orders (sku);
"""

CREATE_AMZ_ADS = """
CREATE TABLE IF NOT EXISTS amz_ads (
    id         SERIAL        NOT NULL,
    sku        VARCHAR(20),
    country    VARCHAR(100),
    clicks     INT,
    ctr        DECIMAL(8,6),
    total_cost DECIMAL(10,2),
    cpc        DECIMAL(10,4),
    purchases  DECIMAL(10,2),
    sales      DECIMAL(10,2),
    roas       DECIMAL(12,6),
    -- NOTE: This is a SKU-level snapshot (no date column). Join on sku only.
    PRIMARY KEY (id),
    CONSTRAINT fk_amz_ads_sku FOREIGN KEY (sku) REFERENCES products(sku)
);
"""

CREATE_AMZ_ADS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_amz_ads_sku     ON amz_ads (sku);
CREATE INDEX IF NOT EXISTS idx_amz_ads_country ON amz_ads (country);
"""

CREATE_META_ADS = """
CREATE TABLE IF NOT EXISTS meta_ads (
    sku         VARCHAR(20)  NOT NULL,
    spend       DECIMAL(10,2),
    impressions INT,
    clicks      INT,
    -- NOTE: This is a SKU-level snapshot (no date or country column).
    -- Join on sku only.
    PRIMARY KEY (sku),
    CONSTRAINT fk_meta_ads_sku FOREIGN KEY (sku) REFERENCES products(sku)
);
"""

# Ordered list used by the loader — tables first, then indexes
ALL_DDL = [
    CREATE_PRODUCTS,
    CREATE_AMZ_ORDERS,
    CREATE_AMZ_ORDERS_INDEXES,
    CREATE_SHOPIFY_ORDERS,
    CREATE_SHOPIFY_ORDERS_INDEXES,
    CREATE_AMZ_ADS,
    CREATE_AMZ_ADS_INDEXES,
    CREATE_META_ADS,
]
