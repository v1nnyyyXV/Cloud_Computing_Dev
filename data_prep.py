import pandas as pd

# -----------------------------
# LOAD DATA
# -----------------------------
products = pd.read_csv("products.csv")
sales = pd.read_csv("sales.csv")

# -----------------------------
# CLEAN COLUMN NAMES
# -----------------------------
products.columns = products.columns.str.strip().str.lower().str.replace(" ", "_")
sales.columns = sales.columns.str.strip().str.lower().str.replace(" ", "_")

# -----------------------------
# CLEAN PRODUCTS DATA
# -----------------------------
# Remove duplicate rows
products = products.drop_duplicates()

# Ensure required product columns exist
required_product_cols = [
    "product_id", "product_name", "category",
    "price", "stock_quantity", "reorder_level", "date_added"
]

for col in required_product_cols:
    if col not in products.columns:
        products[col] = None

# Convert data types
products["price"] = pd.to_numeric(products["price"], errors="coerce").fillna(0)
products["stock_quantity"] = pd.to_numeric(products["stock_quantity"], errors="coerce").fillna(0).astype(int)
products["reorder_level"] = pd.to_numeric(products["reorder_level"], errors="coerce").fillna(0).astype(int)
products["date_added"] = pd.to_datetime(products["date_added"], errors="coerce")

# Fill missing text values
products["product_name"] = products["product_name"].fillna("Unknown Product")
products["category"] = products["category"].fillna("Unknown Category")

# -----------------------------
# CLEAN SALES DATA
# -----------------------------
# Remove duplicate rows
sales = sales.drop_duplicates()

# Ensure required sales columns exist
required_sales_cols = [
    "order_id", "order_date", "product_id", "product_name",
    "category", "quantity_sold", "total_amount",
    "payment_method", "order_status"
]

for col in required_sales_cols:
    if col not in sales.columns:
        sales[col] = None

# Convert data types
sales["order_date"] = pd.to_datetime(sales["order_date"], errors="coerce")
sales["quantity_sold"] = pd.to_numeric(sales["quantity_sold"], errors="coerce").fillna(0).astype(int)
sales["total_amount"] = pd.to_numeric(sales["total_amount"], errors="coerce").fillna(0)

# Fill missing text values
sales["product_name"] = sales["product_name"].fillna("Unknown Product")
sales["category"] = sales["category"].fillna("Unknown Category")
sales["payment_method"] = sales["payment_method"].fillna("Unknown")
sales["order_status"] = sales["order_status"].fillna("Pending")

# -----------------------------
# OPTIONAL: MERGE PRODUCT INFO INTO SALES
# This helps fill missing product_name/category if product_id exists
# -----------------------------
product_lookup = products[["product_id", "product_name", "category", "price"]].drop_duplicates()

sales = sales.merge(
    product_lookup,
    on="product_id",
    how="left",
    suffixes=("", "_from_products")
)

# Fill missing product_name/category from products table
sales["product_name"] = sales["product_name"].where(
    sales["product_name"].notna() & (sales["product_name"] != "Unknown Product"),
    sales["product_name_from_products"]
)

sales["category"] = sales["category"].where(
    sales["category"].notna() & (sales["category"] != "Unknown Category"),
    sales["category_from_products"]
)

# If total_amount is missing or 0, calculate it using quantity_sold * price
sales["total_amount"] = sales["total_amount"].where(
    sales["total_amount"] > 0,
    sales["quantity_sold"] * sales["price"]
)

# Drop helper columns
drop_cols = ["product_name_from_products", "category_from_products", "price"]
sales = sales.drop(columns=[col for col in drop_cols if col in sales.columns])

# -----------------------------
# FINAL COLUMN ORDER
# -----------------------------
products = products[
    [
        "product_id",
        "product_name",
        "category",
        "price",
        "stock_quantity",
        "reorder_level",
        "date_added"
    ]
]

sales = sales[
    [
        "order_id",
        "order_date",
        "product_id",
        "product_name",
        "category",
        "quantity_sold",
        "total_amount",
        "payment_method",
        "order_status"
    ]
]

# -----------------------------
# SAVE CLEANED FILES
# -----------------------------
products.to_csv("products_cleaned.csv", index=False)
sales.to_csv("sales_cleaned.csv", index=False)

print("Data preparation complete.")
print("Saved cleaned files:")
print("- products_cleaned.csv")
print("- sales_cleaned.csv")