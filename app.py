import os
import re
from typing import Iterable, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_FOLDER = "dataset"


def normalize_column_name(column_name):
    if column_name is None:
        return "column"
    text = str(column_name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "column"


def choose_dataset_file(data_folder: str):
    if not os.path.isdir(data_folder):
        return None

    csv_files = sorted(
        os.path.join(data_folder, file_name)
        for file_name in os.listdir(data_folder)
        if file_name.lower().endswith(".csv")
    )
    if not csv_files:
        return None

    preferred_order = [
        "sales",
        "orders",
        "customer",
        "retail",
        "ecommerce",
        "data",
    ]

    def score(path):
        name = os.path.basename(path).lower()
        for idx, keyword in enumerate(preferred_order):
            if keyword in name:
                return idx
        return len(preferred_order)

    return min(csv_files, key=score)


def find_matching_column(columns: Iterable[str], aliases):
    normalized = {normalize_column_name(column): column for column in columns}
    alias_set = {normalize_column_name(alias) for alias in aliases}

    for alias in alias_set:
        if alias in normalized:
            return normalized[alias]

    for column in columns:
        normalized_name = normalize_column_name(column)
        for alias in aliases:
            if normalize_column_name(alias) in normalized_name:
                return column
    return None


def is_categorical_like(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        unique_count = series.dropna().nunique()
        return unique_count <= 50 and unique_count < len(series.dropna()) * 0.9
    return True


def get_sales_column(columns):
    sales_aliases = [
        "sales",
        "sale",
        "revenue",
        "amount",
        "total_sales",
        "total_amount",
        "price",
        "item_price",
        "net_sales",
        "total_price",
        "total_revenue",
    ]
    return find_matching_column(columns, sales_aliases)


def get_customer_column(columns):
    customer_aliases = [
        "customer_id",
        "customerid",
        "customer",
        "customer_name",
        "user_id",
        "buyer_id",
        "customer_identifier",
    ]
    return find_matching_column(columns, customer_aliases)


def get_category_column(columns):
    category_aliases = [
        "category",
        "product_category",
        "product_category_name",
        "department",
        "segment",
        "product_name",
        "item_category",
    ]
    return find_matching_column(columns, category_aliases)


def build_filters(df: pd.DataFrame):
    selected_filters = {}
    candidate_columns = [
        column
        for column in df.columns
        if is_categorical_like(df[column]) and df[column].dropna().nunique() <= 50
    ]

    for column in candidate_columns[:5]:
        unique_values = df[column].dropna().astype(str).unique()
        selected_values = st.sidebar.multiselect(
            column.replace("_", " ").title(),
            sorted(unique_values),
        )
        if selected_values:
            selected_filters[column] = selected_values
    return selected_filters


def build_dashboard(df: pd.DataFrame):
    st.sidebar.header("📊 Dataset Information")
    st.sidebar.write("File:")
    st.sidebar.write(os.path.basename(df.attrs.get("source_file", "dataset.csv")))
    st.sidebar.write("Rows:")
    st.sidebar.write(df.shape[0])
    st.sidebar.write("Columns:")
    st.sidebar.write(df.shape[1])

    st.sidebar.header("🔎 Filters")
    selected_filters = build_filters(df)

    filtered_df = df.copy()
    for column, values in selected_filters.items():
        filtered_df = filtered_df[filtered_df[column].astype(str).isin(values)]

    st.subheader("📌 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", f"{len(filtered_df):,}")

    sales_column = get_sales_column(filtered_df.columns)
    if sales_column:
        numeric_sales = pd.to_numeric(filtered_df[sales_column], errors="coerce")
        filtered_df[sales_column] = numeric_sales
        with col2:
            st.metric("Total Sales", f"{numeric_sales.sum():,.2f}")
        with col3:
            st.metric("Average Sales", f"{numeric_sales.mean():,.2f}")
    else:
        with col2:
            st.metric("Total Sales", "N/A")
        with col3:
            st.metric("Average Sales", "N/A")

    customer_column = get_customer_column(filtered_df.columns)
    if customer_column:
        with col4:
            st.metric("Unique Customers", f"{filtered_df[customer_column].nunique():,}")
    else:
        with col4:
            st.metric("Unique Customers", "N/A")

    st.divider()
    st.subheader("📋 Dataset Preview")
    st.dataframe(filtered_df.head(10), use_container_width=True)
    st.divider()

    st.subheader("📊 Dataset Summary")
    summary_col1, summary_col2 = st.columns(2)
    with summary_col1:
        st.write("**Dataset Shape**")
        st.write(f"Rows: {filtered_df.shape[0]}")
        st.write(f"Columns: {filtered_df.shape[1]}")

    with summary_col2:
        st.write("**Missing Values**")
        missing_values = filtered_df.isnull().sum().sort_values(ascending=False)
        st.dataframe(missing_values.head(10), use_container_width=True)

    st.divider()

    if sales_column:
        st.subheader("💰 Sales Analysis")
        sales_col1, sales_col2 = st.columns(2)

        with sales_col1:
            hist = px.histogram(filtered_df, x=sales_column, title="Sales Distribution", nbins=30)
            st.plotly_chart(hist, use_container_width=True)

        with sales_col2:
            box = px.box(filtered_df, y=sales_column, title="Sales Value Distribution")
            st.plotly_chart(box, use_container_width=True)

    category_column = get_category_column(filtered_df.columns)
    if category_column and sales_column:
        st.subheader("🛒 Category-wise Sales")
        category_sales = (
            filtered_df.groupby(category_column, dropna=False)[sales_column]
            .sum()
            .reset_index()
            .sort_values(sales_column, ascending=False)
        )
        category_chart = px.bar(
            category_sales.head(15),
            x=category_column,
            y=sales_column,
            title="Top Categories by Sales",
        )
        st.plotly_chart(category_chart, use_container_width=True)

    if customer_column:
        st.subheader("👥 Customer Analysis")
        customer_frequency = (
            filtered_df.groupby(customer_column, dropna=False)
            .size()
            .reset_index(name="orders")
            .sort_values("orders", ascending=False)
        )
        customer_chart = px.bar(
            customer_frequency.head(10),
            x=customer_column,
            y="orders",
            title="Top Customers by Number of Orders",
        )
        st.plotly_chart(customer_chart, use_container_width=True)

    numeric_columns = filtered_df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_columns) >= 2:
        st.subheader("📈 Numerical Data Analysis")
        correlation = filtered_df[numeric_columns].corr()
        corr_chart = px.imshow(correlation, text_auto=True, title="Correlation Heatmap")
        st.plotly_chart(corr_chart, use_container_width=True)

    st.divider()
    st.subheader("📁 Complete Dataset")
    st.dataframe(filtered_df, use_container_width=True, height=400)

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


def main():
    st.set_page_config(
        page_title="Smart Retail Customer & Sales Analysis",
        page_icon="🛍️",
        layout="wide",
    )
    st.title("🛍️ Smart Retail Customer and Sales Analysis")
    st.markdown("### Data Analysis and Visualization using Python")
    st.divider()

    dataset_path = choose_dataset_file(DATA_FOLDER)
    if dataset_path is None:
        st.error("❌ No CSV file found inside the dataset folder.")
        st.info("Please place your ecommerce CSV file inside the 'dataset' folder.")
        return

    try:
        df = pd.read_csv(dataset_path)
    except Exception as exc:
        st.error(f"Error loading dataset: {exc}")
        return

    df.attrs["source_file"] = os.path.basename(dataset_path)
    df.columns = [normalize_column_name(column) for column in df.columns]
    build_dashboard(df)


if __name__ == "__main__":
    main()
