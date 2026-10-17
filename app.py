import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Retail Customer & Sales Analysis",
    page_icon="🛍️",
    layout="wide"
)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🛍️ Smart Retail Customer and Sales Analysis")
st.markdown(
    "### Data Analysis and Visualization using Python"
)

st.divider()

# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

DATA_FOLDER = "dataset"

csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))

if len(csv_files) == 0:
    st.error("❌ No CSV file found inside the dataset folder.")
    st.info("Please place your ecommerce CSV file inside the 'dataset' folder.")
    st.stop()

# Load first CSV file
file_path = csv_files[0]

try:
    df = pd.read_csv(file_path)
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# --------------------------------------------------
# DATASET INFORMATION
# --------------------------------------------------

st.sidebar.header("📊 Dataset Information")

st.sidebar.write("File:")
st.sidebar.write(os.path.basename(file_path))

st.sidebar.write("Rows:")
st.sidebar.write(df.shape[0])

st.sidebar.write("Columns:")
st.sidebar.write(df.shape[1])

# --------------------------------------------------
# CLEAN COLUMN NAMES
# --------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("🔎 Filters")

# Find categorical columns
categorical_columns = df.select_dtypes(
    include=["object", "category"]
).columns.tolist()

selected_filters = {}

for column in categorical_columns[:5]:

    unique_values = df[column].dropna().unique()

    if len(unique_values) <= 50:

        selected_values = st.sidebar.multiselect(
            column.replace("_", " ").title(),
            sorted(unique_values.astype(str))
        )

        if selected_values:
            selected_filters[column] = selected_values

# Apply filters
filtered_df = df.copy()

for column, values in selected_filters.items():

    filtered_df = filtered_df[
        filtered_df[column].astype(str).isin(values)
    ]

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Records",
        f"{len(filtered_df):,}"
    )

# Find possible sales/revenue columns
sales_candidates = [
    "sales",
    "sale",
    "revenue",
    "amount",
    "total_sales",
    "total_amount",
    "price"
]

sales_column = None

for column in sales_candidates:
    if column in filtered_df.columns:
        sales_column = column
        break

if sales_column:

    filtered_df[sales_column] = pd.to_numeric(
        filtered_df[sales_column],
        errors="coerce"
    )

    total_sales = filtered_df[sales_column].sum()

    with col2:
        st.metric(
            "Total Sales",
            f"{total_sales:,.2f}"
        )

    with col3:
        st.metric(
            "Average Sales",
            f"{filtered_df[sales_column].mean():,.2f}"
        )

else:

    with col2:
        st.metric("Total Sales", "N/A")

    with col3:
        st.metric("Average Sales", "N/A")

# Customer column detection
customer_candidates = [
    "customer_id",
    "customerid",
    "customer",
    "customer_name",
    "user_id"
]

customer_column = None

for column in customer_candidates:
    if column in filtered_df.columns:
        customer_column = column
        break

if customer_column:

    customers = filtered_df[customer_column].nunique()

    with col4:
        st.metric(
            "Unique Customers",
            f"{customers:,}"
        )

else:

    with col4:
        st.metric(
            "Unique Customers",
            "N/A"
        )

st.divider()

# --------------------------------------------------
# DATASET PREVIEW
# --------------------------------------------------

st.subheader("📋 Dataset Preview")

st.dataframe(
    filtered_df.head(10),
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# DATASET SUMMARY
# --------------------------------------------------

st.subheader("📊 Dataset Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.write("**Dataset Shape**")

    st.write(
        f"Rows: {filtered_df.shape[0]}"
    )

    st.write(
        f"Columns: {filtered_df.shape[1]}"
    )

with summary_col2:

    st.write("**Missing Values**")

    missing_values = (
        filtered_df.isnull()
        .sum()
        .sort_values(ascending=False)
    )

    st.dataframe(
        missing_values.head(10),
        use_container_width=True
    )

st.divider()

# --------------------------------------------------
# SALES ANALYSIS
# --------------------------------------------------

if sales_column:

    st.subheader("💰 Sales Analysis")

    sales_col1, sales_col2 = st.columns(2)

    # Histogram
    with sales_col1:

        fig = px.histogram(
            filtered_df,
            x=sales_column,
            title="Sales Distribution",
            nbins=30
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # Box plot
    with sales_col2:

        fig = px.box(
            filtered_df,
            y=sales_column,
            title="Sales Value Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# --------------------------------------------------
# CATEGORY ANALYSIS
# --------------------------------------------------

category_candidates = [
    "category",
    "product_category",
    "product_category_name",
    "department",
    "segment"
]

category_column = None

for column in category_candidates:

    if column in filtered_df.columns:

        category_column = column
        break

if category_column and sales_column:

    st.subheader("🛒 Category-wise Sales")

    category_sales = (
        filtered_df
        .groupby(category_column)[sales_column]
        .sum()
        .reset_index()
        .sort_values(
            sales_column,
            ascending=False
        )
    )

    fig = px.bar(
        category_sales.head(15),
        x=category_column,
        y=sales_column,
        title="Top Categories by Sales"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# --------------------------------------------------
# CUSTOMER ANALYSIS
# --------------------------------------------------

if customer_column:

    st.subheader("👥 Customer Analysis")

    customer_frequency = (
        filtered_df
        .groupby(customer_column)
        .size()
        .reset_index(name="orders")
        .sort_values(
            "orders",
            ascending=False
        )
    )

    fig = px.bar(
        customer_frequency.head(10),
        x=customer_column,
        y="orders",
        title="Top Customers by Number of Orders"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# --------------------------------------------------
# NUMERICAL CORRELATION
# --------------------------------------------------

numeric_columns = filtered_df.select_dtypes(
    include=["number"]
).columns.tolist()

if len(numeric_columns) >= 2:

    st.subheader("📈 Numerical Data Analysis")

    correlation = filtered_df[numeric_columns].corr()

    fig = px.imshow(
        correlation,
        text_auto=True,
        title="Correlation Heatmap"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# --------------------------------------------------
# RAW DATA
# --------------------------------------------------

st.divider()

st.subheader("📁 Complete Dataset")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    """
    **Smart Retail Customer and Sales Analysis**

    Developed using:
    - Python
    - Pandas
    - Plotly
    - Streamlit

    **B.Tech Data Science Project**
    """
)