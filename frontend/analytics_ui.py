import requests
import streamlit as st
from datetime import datetime
import pandas as pd
from fastapi import Response
from hypothesis.internal.charmap import categories
from openpyxl.xml.constants import MIN_ROW

# from jsonschema.benchmarks.const_vs_enum import value

API_URL = "http://localhost:8000/"

def analytics_tab():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", datetime(2024, 8, 1))
    with col2:
        end_date = st.date_input("End Date", datetime(2024,8,5))

    if st.button("Get Analytics"):
        payload = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        response = requests.post(f"{API_URL}/analytics", json=payload)
        response = response.json()

        data = {
            "Category" : list(response.keys()),
            "Total" : [response[category]["total"] for category in response],
            "Percentage" : [response[category]["percentage"] for category in response],
        }

        # df = pd.DataFrame({
        #     "Category" : ["Rent", "Shopping"],
        #     "Total" : [121213, 234],
        #     "Percentage" : [4,6]
        # })

        df = pd.DataFrame(data)
        df_sorted = df.sort_values(by=["Percentage"], ascending=False)

        # df.sorted["Total"] = df.sorted["Total"].astype(float).round(2)
        # df.sorted["Percentage"] = df.sorted["Percentage"].astype(float).round(2)

        df_sorted["Total"] = df_sorted["Total"].astype(float)
        df_sorted["Percentage"] = df_sorted["Percentage"].astype(float)

        styled = df_sorted.style.format({
            "Total" : "{:,.2f}",
            "Percentage" : "{:.2f}"
        })

        st.title("Expense breakdown by category")
        st.bar_chart(data = df_sorted.set_index("Category")["Percentage"])

        st.table(styled)
        # st.write(response)




