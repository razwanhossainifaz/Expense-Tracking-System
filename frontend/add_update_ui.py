import requests
import streamlit as st
from datetime import datetime
from fastapi import Response
from hypothesis.internal.charmap import categories
from openpyxl.xml.constants import MIN_ROW

# from jsonschema.benchmarks.const_vs_enum import value

API_URL = "http://localhost:8000/"

def add_update_tab():
    selected_date = st.date_input("Enter Date", datetime(2024,8,2), label_visibility="collapsed")
    response = requests.get(f"{API_URL}/expenses/{selected_date}")

    if response.status_code == 200:
        existing_expenses = response.json()
        # st.write(existing_expenses)
    else:
        st.error("Failed to retrive expenses")
        existing_expenses = []

    categories = ["Rent", "Food", "Shopping", "Entertainment", "Other"]

    MIN_ROW = 5
    num_existing = len(existing_expenses)
    if num_existing == 0:
        total_rows = MIN_ROW
    else:
        total_rows = max(num_existing, MIN_ROW)

    with st.form("expense_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            # st.subheader("Amount")
            st.markdown("<h3 style='text-align: center;'>Amount</h3>", unsafe_allow_html=True)
        with col2:
            # st.subheader("Category")
            st.markdown("<h3 style='text-align: center;'>Category</h3>", unsafe_allow_html=True)
        with col3:
            # st.subheader("Notes")
            st.markdown("<h3 style='text-align: center;'>Notes</h3>", unsafe_allow_html=True)

        expenses = []
        for i in range(total_rows):
            if i < len(existing_expenses):
                # amount = existing_expenses[i]["amount"]
                amount = existing_expenses[i].get("amount", 0.0)
                category = existing_expenses[i].get("category", categories[0])
                notes = existing_expenses[i].get("notes", "")
            else:
                amount = 0.0
                category = "Shopping"
                notes = ""

            key_amount = f"amount_{selected_date}_{i})"
            key_cat = f"category_{selected_date}_{i})"
            key_notes = f"notes_{selected_date}_{i})"

            col1, col2, col3 = st.columns(3)
            with col1:
                amount_input = st.number_input(label="Amount", min_value=0.0, step=1.0,  value=amount, key = key_amount, label_visibility="collapsed")
            with col2:
                category_input = st.selectbox(label="Category", options=categories, index=categories.index(category), key = key_cat, label_visibility="collapsed")
            with col3:
                notes_input = st.text_input(label="Notes", value=notes, key = key_notes, label_visibility="collapsed")

            expenses.append({
                'amount' : amount_input,
                'category' : category_input,
                'notes' : notes_input
            })

        submit_button = st.form_submit_button(label="Submit")
        if submit_button:
            filtered_expenses = [expense for expense in expenses if expense['amount'] > 0]
            requests.post(f"{API_URL}/expenses/{selected_date}", json=filtered_expenses)
            if response.status_code == 200:
                st.success("Expenses undated/submitted successfully")
            else:
                st.error("Failed to undate/submit expenses")
            pass
