import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def show_dashboard():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { padding: 2rem 2.5rem; max-width: 1400px; }

    [data-testid="stMetric"] {
        background: #f8f7f4;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border: 0.5px solid #e8e6e0;
    }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #888 !important; letter-spacing: 0.04em; }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 600 !important; color: #1a1a1a !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    .section-header {
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.1em;
        color: #aaa;
        text-transform: uppercase;
        margin: 2rem 0 1rem 0;
        padding-bottom: 8px;
        border-bottom: 0.5px solid #e8e6e0;
    }
    .data-note {
        font-size: 12px;
        color: #aaa;
        margin-top: 0.5rem;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Load ──────────────────────────────────────────────────────────────────────
    @st.cache_data
    def load_data():
        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as conn:
            amz      = pd.read_sql("SELECT * FROM amz_orders",    conn)
            shopify  = pd.read_sql("SELECT * FROM shopify_orders", conn)
            products = pd.read_sql("SELECT * FROM products",       conn)
            amz_ads  = pd.read_sql("SELECT * FROM amz_ads",        conn)
            meta_ads = pd.read_sql("SELECT * FROM meta_ads",       conn)
        return amz, shopify, products, amz_ads, meta_ads

    @st.cache_data
    def prepare_data(amz_raw, shopify_raw, products_raw, amz_ads_raw, meta_ads_raw):

        # ── Amazon orders ──────────────────────────────────────────────────────────
        # Columns: order_date, order_type, order_id, sku, seller_type,
        #          sale_price, total_taxes, fee, total_amount
        amz = amz_raw.copy()
        amz["date"]        = pd.to_datetime(amz["order_date"], errors="coerce")
        amz["sku"]         = amz["sku"].astype(str).str.strip()
        amz["amount"]      = pd.to_numeric(amz["total_amount"], errors="coerce").fillna(0)
        amz["channel"]     = "Amazon"
        # seller_type == "Amazon" → FBA (fulfilled by Amazon)
        # seller_type == "Seller" → FMN (fulfilled by merchant)
        amz["sub_channel"] = amz["seller_type"].apply(
            lambda x: "Amazon FBA" if str(x).strip().lower() == "amazon" else "Amazon FMN"
        )

        amz_orders  = amz[amz["order_type"].str.strip().str.lower() == "order"].copy()
        amz_returns = amz[amz["order_type"].str.strip().str.lower().isin(["refund", "return"])].copy()
        amz_returns["amount"] = amz_returns["amount"].abs()

        # ── Shopify orders ─────────────────────────────────────────────────────────
        # Columns (DB): order_id, sku, order_date, order_type, email, total_amount
        shopify = shopify_raw.copy()
        shopify["date"]        = pd.to_datetime(shopify["order_date"], errors="coerce")
        shopify["sku"]         = shopify["sku"].astype(str).str.strip()
        shopify["amount"]      = pd.to_numeric(shopify["total_amount"], errors="coerce").fillna(0)
        shopify["channel"]     = "Shopify"
        shopify["sub_channel"] = "Shopify"

        shop_orders  = shopify[shopify["order_type"].str.strip().str.lower() == "order"].copy()
        shop_returns = shopify[shopify["order_type"].str.strip().str.lower() == "return"].copy()
        shop_returns["amount"] = shop_returns["amount"].abs()

        # ── Unified orders & returns ───────────────────────────────────────────────
        keep = ["date", "sku", "channel", "sub_channel", "amount"]
        orders  = pd.concat([amz_orders[keep],  shop_orders[keep]],  ignore_index=True)
        returns = pd.concat([amz_returns[keep], shop_returns[keep]], ignore_index=True)

        # ── Products ───────────────────────────────────────────────────────────────
        # Columns (DB): sku, product_name, category, price
        products = products_raw.copy()
        products = products.rename(columns={"price": "cost_price"})
        products["sku"]        = products["sku"].astype(str).str.strip()
        products["cost_price"] = pd.to_numeric(products["cost_price"], errors="coerce").fillna(0)

        orders = orders.merge(
            products[["sku", "product_name", "category", "cost_price"]],
            on="sku", how="left"
        )
        orders["cost_price"] = orders["cost_price"].fillna(0)
        orders["margin"]     = orders["amount"] - orders["cost_price"]

        # ── Ads ────────────────────────────────────────────────────────────────────
        # amz_ads columns: sku, country, clicks, ctr, total_cost, cpc,
        #                  purchases, sales, roas
        amz_ads = amz_ads_raw.copy()
        amz_ads["sku"]    = amz_ads["sku"].astype(str).str.strip()
        amz_ads["spend"]  = pd.to_numeric(amz_ads["total_cost"], errors="coerce").fillna(0)
        amz_ads["source"] = "Amazon Ads"

        # meta_ads columns: sku, spend, impressions, clicks
        meta_ads = meta_ads_raw.copy()
        meta_ads["sku"]    = meta_ads["sku"].astype(str).str.strip()
        meta_ads["spend"]  = pd.to_numeric(meta_ads["spend"], errors="coerce").fillna(0)
        meta_ads["source"] = "Meta Ads"

        ads = pd.concat(
            [amz_ads[["sku", "spend", "source"]], meta_ads[["sku", "spend", "source"]]],
            ignore_index=True
        )
        ads_by_sku = (
            ads.groupby("sku")["spend"].sum()
            .reset_index()
            .rename(columns={"spend": "total_ads_spend"})
        )

        return orders, returns, ads, ads_by_sku, products

    def filter_period(df, days):
        if df.empty:
            return df
        cutoff = df["date"].max() - timedelta(days=days)
        return df[df["date"] >= cutoff]

    def fmt_eur(v):
        return f"€{v:,.0f}"

    def delta_str(cur, prev):
        if prev == 0:
            return "N/A", "normal"
        pct = (cur - prev) / abs(prev) * 100
        return f"{pct:+.1f}%", "normal" if pct >= 0 else "inverse"

    COLORS = {"Amazon FBA": "#378ADD", "Amazon FMN": "#1D9E75", "Shopify": "#EF9F27"}

    # ── Load data ─────────────────────────────────────────────────────────────────
    try:
        amz_raw, shopify_raw, products_raw, amz_ads_raw, meta_ads_raw = load_data()
        orders, returns, ads, ads_by_sku, products = prepare_data(
            amz_raw, shopify_raw, products_raw, amz_ads_raw, meta_ads_raw
        )
        data_ok = True
    except Exception as e:
        data_ok = False
        err_msg = str(e)

    # ── Header ────────────────────────────────────────────────────────────────────
    col_title, col_period = st.columns([3, 1])
    with col_title:
        st.markdown("## 📦 E-commerce performance")
        st.markdown('<p class="data-note">Amazon · Shopify · Amazon Ads · Meta Ads</p>',
                    unsafe_allow_html=True)
    with col_period:
        period_days = st.radio("Period", [30, 60, 90],
                            format_func=lambda x: f"Last {x}d", horizontal=True)

    if not data_ok:
        st.error(
            f"Could not load data from the database.\n\n"
            f"Check that DATABASE_URL is set correctly in .env and the database is seeded.\n\n"
            f"Error: {err_msg}"
        )
        st.stop()

    # ── Filter ────────────────────────────────────────────────────────────────────
    orders_cur  = filter_period(orders,  period_days)
    orders_prev = filter_period(orders,  period_days * 2)
    orders_prev = orders_prev[~orders_prev.index.isin(orders_cur.index)]
    returns_cur = filter_period(returns, period_days)

    total_ads      = ads["spend"].sum()
    total_ads_amz  = ads[ads["source"] == "Amazon Ads"]["spend"].sum()
    total_ads_meta = ads[ads["source"] == "Meta Ads"]["spend"].sum()

    sales_cur   = orders_cur["amount"].sum()
    margin_cur  = orders_cur["margin"].sum()
    profit_cur  = margin_cur - total_ads
    returns_val = returns_cur["amount"].sum()

    sales_prev  = orders_prev["amount"].sum()
    margin_prev = orders_prev["margin"].sum()

    # ── KPI Cards ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">KPI summary</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)

    d_sales,  d_sales_dir  = delta_str(sales_cur,  sales_prev)
    d_margin, d_margin_dir = delta_str(margin_cur, margin_prev)

    k1.metric("Total Sales",     fmt_eur(sales_cur),  d_sales,  delta_color=d_sales_dir)
    k2.metric("Total Margin",    fmt_eur(margin_cur), d_margin, delta_color=d_margin_dir)
    k3.metric("Total Ads Spent", fmt_eur(total_ads),
            f"AMZ {fmt_eur(total_ads_amz)} · Meta {fmt_eur(total_ads_meta)}")
    k4.metric("Total Profit",    fmt_eur(profit_cur), "Margin − Ads")
    k5.metric("Returns",         fmt_eur(returns_val),
            f"{len(returns_cur)} orders", delta_color="inverse")

    # ── Channel breakdown ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Channel breakdown</div>', unsafe_allow_html=True)

    chart1, chart2 = st.columns([1.4, 0.6])

    with chart1:
        st.markdown("**Sales by channel — weekly**")
        orders_cur = orders_cur.copy()
        orders_cur["week"] = orders_cur["date"].dt.to_period("W").apply(lambda r: r.start_time)
        weekly = orders_cur.groupby(["week", "sub_channel"])["amount"].sum().reset_index()

        fig_bar = go.Figure()
        for ch in ["Amazon FBA", "Amazon FMN", "Shopify"]:
            d = weekly[weekly["sub_channel"] == ch]
            fig_bar.add_trace(go.Bar(
                x=d["week"], y=d["amount"], name=ch,
                marker_color=COLORS.get(ch, "#ccc"),
                hovertemplate=f"<b>{ch}</b><br>Week: %{{x|%d %b}}<br>€%{{y:,.0f}}<extra></extra>"
            ))
        fig_bar.update_layout(
            barmode="stack", plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0), height=280,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font_size=12),
            xaxis=dict(showgrid=False, tickfont_size=11),
            yaxis=dict(showgrid=True, gridcolor="#f0eeea", tickprefix="€", tickfont_size=11),
            font_family="DM Sans"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart2:
        st.markdown("**Revenue share by channel**")
        ch_totals = orders_cur.groupby("sub_channel")["amount"].sum().reset_index()
        fig_donut = go.Figure(go.Pie(
            labels=ch_totals["sub_channel"],
            values=ch_totals["amount"],
            hole=0.55,
            marker_colors=[COLORS.get(c, "#ccc") for c in ch_totals["sub_channel"]],
            textfont_size=12,
            hovertemplate="<b>%{label}</b><br>€%{value:,.0f} · %{percent}<extra></extra>"
        ))
        fig_donut.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), height=280,
            legend=dict(orientation="v", font_size=11),
            paper_bgcolor="white", font_family="DM Sans"
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── Top 10 products by profit ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Product performance</div>', unsafe_allow_html=True)

    prod = (
        orders_cur.groupby("sku")
        .agg(revenue=("amount", "sum"), margin=("margin", "sum"),
            product_name=("product_name", "first"))
        .reset_index()
    )
    prod = prod.merge(ads_by_sku, on="sku", how="left")
    prod["total_ads_spend"] = prod["total_ads_spend"].fillna(0)
    prod["profit"] = prod["margin"] - prod["total_ads_spend"]
    prod["label"]  = prod.apply(
        lambda r: r["product_name"]
        if pd.notna(r["product_name"]) and str(r["product_name"]) != "nan"
        else r["sku"], axis=1
    )

    top10 = prod.nlargest(10, "profit").sort_values("profit")

    p1, p2 = st.columns([1.6, 0.4])

    with p1:
        st.markdown("**Top 10 products by profit**")
        fig_top = go.Figure()
        fig_top.add_trace(go.Bar(
            y=top10["label"], x=top10["margin"],
            name="Gross margin", orientation="h",
            marker_color="#AFA9EC",
            hovertemplate="<b>%{y}</b><br>Gross margin: €%{x:,.0f}<extra></extra>"
        ))
        fig_top.add_trace(go.Bar(
            y=top10["label"], x=top10["profit"],
            name="Profit after ads", orientation="h",
            marker_color="#534AB7",
            hovertemplate="<b>%{y}</b><br>Profit after ads: €%{x:,.0f}<extra></extra>"
        ))
        fig_top.update_layout(
            barmode="overlay", plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=20, t=10, b=0), height=360,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font_size=12),
            xaxis=dict(showgrid=True, gridcolor="#f0eeea", tickprefix="€", tickfont_size=11),
            yaxis=dict(showgrid=False, tickfont_size=11),
            font_family="DM Sans"
        )
        st.plotly_chart(fig_top, use_container_width=True)
        st.markdown(
            '<p class="data-note">Light bar = gross margin · Dark bar = profit after ads · Gap = ad spend per SKU</p>',
            unsafe_allow_html=True
        )

    with p2:
        st.markdown("**Ads spend by source**")
        ads_src = ads.groupby("source")["spend"].sum().reset_index()
        fig_ads = go.Figure(go.Pie(
            labels=ads_src["source"], values=ads_src["spend"],
            hole=0.5, marker_colors=["#378ADD", "#E24B4A"],
            textfont_size=12,
            hovertemplate="<b>%{label}</b><br>€%{value:,.0f} · %{percent}<extra></extra>"
        ))
        fig_ads.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), height=200,
            paper_bgcolor="white", font_family="DM Sans",
            legend=dict(font_size=11)
        )
        st.plotly_chart(fig_ads, use_container_width=True)

        st.markdown("**ROAS by platform**")
        roas_amz  = orders_cur[orders_cur["channel"] == "Amazon"]["amount"].sum() / max(total_ads_amz,  1)
        roas_meta = orders_cur[orders_cur["channel"] == "Shopify"]["amount"].sum() / max(total_ads_meta, 1)
        st.metric("Amazon Ads ROAS", f"{roas_amz:.1f}x")
        st.metric("Meta Ads ROAS",   f"{roas_meta:.1f}x")

    # ── Returns & data sources ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Returns & data sources</div>', unsafe_allow_html=True)

    ret1, ret2, ret3 = st.columns(3)

    with ret1:
        st.markdown("**Return rate by channel**")
        ret_by_ch   = returns_cur.groupby("sub_channel")["amount"].sum().reset_index()
        sales_by_ch = orders_cur.groupby("sub_channel")["amount"].sum().reset_index()
        merged_ret  = sales_by_ch.merge(ret_by_ch, on="sub_channel", how="left",
                                        suffixes=("_sales", "_returns"))
        merged_ret["return_rate"] = (
            merged_ret["amount_returns"].fillna(0) / merged_ret["amount_sales"] * 100
        ).round(1)

        fig_ret = go.Figure(go.Bar(
            x=merged_ret["sub_channel"],
            y=merged_ret["return_rate"],
            marker_color=[COLORS.get(c, "#ccc") for c in merged_ret["sub_channel"]],
            text=merged_ret["return_rate"].apply(lambda x: f"{x}%"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Return rate: %{y:.1f}%<extra></extra>"
        ))
        fig_ret.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=0, t=20, b=0), height=220,
            yaxis=dict(showgrid=True, gridcolor="#f0eeea",
                    ticksuffix="%", tickfont_size=11),
            xaxis=dict(tickfont_size=11),
            font_family="DM Sans"
        )
        st.plotly_chart(fig_ret, use_container_width=True)

    with ret2:
        st.markdown("**Top returned SKUs**")
        top_ret = (
            returns_cur.groupby("sku")["amount"].sum()
            .nlargest(5).reset_index()
        )
        top_ret.columns = ["SKU", "Returns (€)"]
        top_ret["Returns (€)"] = top_ret["Returns (€)"].apply(lambda x: f"€{x:,.0f}")
        st.dataframe(top_ret, use_container_width=True, hide_index=True)

    with ret3:
        st.markdown("**Data sources**")
        sources = {
            "amz_orders":     f"{len(amz_raw):,} rows",
            "shopify_orders": f"{len(shopify_raw):,} rows",
            "products":       f"{len(products_raw):,} SKUs",
            "amz_ads":        f"{len(amz_ads_raw):,} rows",
            "meta_ads":       f"{len(meta_ads_raw):,} rows",
        }
        for tname, info in sources.items():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:6px 0;
                border-bottom:0.5px solid #f0eeea; font-size:13px;">
                <span style="color:#555; font-family:'DM Mono',monospace;
                    font-size:12px;">{tname}</span>
                <span style="color:#aaa; font-size:12px;">{info}</span>
            </div>""", unsafe_allow_html=True)
