import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="RetailPulse Dashboard",
    page_icon="🛒",
    layout="wide"
)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    products = pd.read_csv("products.csv")
    sales = pd.read_csv("sales.csv")

    # Convert date columns
    products["date_added"] = pd.to_datetime(products["date_added"], errors="coerce")
    sales["order_date"] = pd.to_datetime(sales["order_date"], errors="coerce")

    return products, sales


products_df, sales_df = load_data()

# -----------------------------
# TITLE
# -----------------------------
st.title("🛒 RetailPulse Dashboard")
st.subheader("Retail and E-commerce Analytics Dashboard")

st.markdown("""
This dashboard helps a retail business monitor sales performance, product inventory,
top-selling categories, payment methods, and low-stock items.
""")

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filter Dashboard")

# Category filter
all_categories = sorted(sales_df["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Select product category",
    all_categories,
    default=all_categories
)

# Payment method filter
all_payment_methods = sorted(sales_df["payment_method"].dropna().unique().tolist())
selected_payments = st.sidebar.multiselect(
    "Select payment method",
    all_payment_methods,
    default=all_payment_methods
)

# Order status filter
all_status = sorted(sales_df["order_status"].dropna().unique().tolist())
selected_status = st.sidebar.multiselect(
    "Select order status",
    all_status,
    default=all_status
)

# Date range filter
min_date = sales_df["order_date"].min()
max_date = sales_df["order_date"].max()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

# Handle date range safely
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = min_date.date()
    end_date = max_date.date()

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_sales = sales_df[
    (sales_df["category"].isin(selected_categories)) &
    (sales_df["payment_method"].isin(selected_payments)) &
    (sales_df["order_status"].isin(selected_status)) &
    (sales_df["order_date"].dt.date >= start_date) &
    (sales_df["order_date"].dt.date <= end_date)
]

# -----------------------------
# KPI CALCULATIONS
# -----------------------------
total_revenue = filtered_sales["total_amount"].sum()
total_orders = filtered_sales["order_id"].nunique()
total_units_sold = filtered_sales["quantity_sold"].sum()
avg_order_value = filtered_sales["total_amount"].mean() if not filtered_sales.empty else 0

# Inventory metrics
total_products = products_df["product_id"].nunique()
low_stock_df = products_df[products_df["stock_quantity"] <= products_df["reorder_level"]]
low_stock_count = low_stock_df.shape[0]

# -----------------------------
# KPI SECTION
# -----------------------------
st.markdown("## Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"KES {total_revenue:,.0f}")
col2.metric("Total Orders", f"{total_orders}")
col3.metric("Units Sold", f"{total_units_sold}")
col4.metric("Average Order Value", f"KES {avg_order_value:,.2f}")

col5, col6 = st.columns(2)
col5.metric("Total Products in Catalog", f"{total_products}")
col6.metric("Low Stock Products", f"{low_stock_count}")

st.divider()

# -----------------------------
# SALES TREND OVER TIME
# -----------------------------
st.markdown("## Sales Trend Over Time")

sales_trend = (
    filtered_sales.groupby("order_date")["total_amount"]
    .sum()
    .reset_index()
    .sort_values("order_date")
)

if not sales_trend.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(sales_trend["order_date"], sales_trend["total_amount"], marker="o")
    ax.set_title("Daily Sales Revenue")
    ax.set_xlabel("Order Date")
    ax.set_ylabel("Revenue (KES)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.warning("No sales data available for the selected filters.")

st.divider()

# -----------------------------
# SALES BY CATEGORY
# -----------------------------
st.markdown("## Sales by Category")

category_sales = (
    filtered_sales.groupby("category")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

if not category_sales.empty:
    fig, ax = plt.subplots(figsize=(8, 4))
    category_sales.plot(kind="bar", ax=ax)
    ax.set_title("Revenue by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Revenue (KES)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No category sales available for the selected filters.")

st.divider()

# -----------------------------
# TOP SELLING PRODUCTS
# -----------------------------
st.markdown("## Top Selling Products")

top_products = (
    filtered_sales.groupby("product_name")
    .agg(
        total_units_sold=("quantity_sold", "sum"),
        total_revenue=("total_amount", "sum")
    )
    .sort_values("total_units_sold", ascending=False)
    .head(10)
    .reset_index()
)

st.dataframe(top_products, width="stretch")

st.divider()

# -----------------------------
# PAYMENT METHOD ANALYSIS
# -----------------------------
st.markdown("## Payment Method Analysis")

payment_summary = (
    filtered_sales.groupby("payment_method")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

if not payment_summary.empty:
    fig, ax = plt.subplots(figsize=(7, 4))
    payment_summary.plot(kind="bar", ax=ax)
    ax.set_title("Revenue by Payment Method")
    ax.set_xlabel("Payment Method")
    ax.set_ylabel("Revenue (KES)")
    plt.xticks(rotation=0)
    st.pyplot(fig)
else:
    st.info("No payment data available for the selected filters.")

st.divider()

# -----------------------------
# ORDER STATUS ANALYSIS
# -----------------------------
st.markdown("## Order Status Summary")

status_summary = (
    filtered_sales.groupby("order_status")["order_id"]
    .count()
    .sort_values(ascending=False)
)

if not status_summary.empty:
    st.dataframe(
        status_summary.reset_index().rename(columns={"order_id": "number_of_orders"}),
        width="stretch"
    )
else:
    st.info("No order status data available for the selected filters.")

st.divider()

# -----------------------------
# INVENTORY ANALYSIS
# -----------------------------
st.markdown("## Inventory Analysis")

inventory_view = products_df.copy()
inventory_view["stock_status"] = inventory_view.apply(
    lambda row: "Low Stock" if row["stock_quantity"] <= row["reorder_level"] else "OK",
    axis=1
)

st.dataframe(inventory_view, width="stretch")

st.markdown("### Low Stock Products")
if not low_stock_df.empty:
    st.dataframe(low_stock_df, width="stretch")
else:
    st.success("No products are currently below the reorder level.")

st.divider()

# -----------------------------
# CATEGORY INVENTORY DISTRIBUTION
# -----------------------------
st.markdown("## Inventory Distribution by Category")

inventory_by_category = (
    products_df.groupby("category")["stock_quantity"]
    .sum()
    .sort_values(ascending=False)
)

if not inventory_by_category.empty:
    fig, ax = plt.subplots(figsize=(8, 4))
    inventory_by_category.plot(kind="bar", ax=ax)
    ax.set_title("Stock Quantity by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Stock Quantity")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No inventory data available.")

st.divider()

# -----------------------------
# MONTHLY REVENUE SUMMARY
# -----------------------------
st.markdown("## Monthly Revenue Summary")

monthly_sales = filtered_sales.copy()
monthly_sales["month"] = monthly_sales["order_date"].dt.to_period("M").astype(str)

monthly_summary = (
    monthly_sales.groupby("month")["total_amount"]
    .sum()
    .reset_index()
)

st.dataframe(monthly_summary, width="stretch")

st.divider()

# -----------------------------
# RAW DATA SECTION
# -----------------------------
st.markdown("## Raw Data Tables")

tab1, tab2 = st.tabs(["Sales Data", "Products Data"])

with tab1:
    st.dataframe(filtered_sales, width="stretch")

with tab2:
    st.dataframe(products_df, width="stretch")

# -----------------------------
# FOOTER / PROJECT SUMMARY
# -----------------------------
st.markdown("---")
st.markdown("""
### Project Summary
This RetailPulse dashboard was developed for the **Retail and E-commerce** business domain.

It supports business decision-making by showing:
- sales trends over time
- best-performing categories and products
- payment method analysis
- order status monitoring
- inventory and low-stock tracking

**Tools used:** Python, Pandas, Streamlit, Matplotlib, CSV datasets
""")