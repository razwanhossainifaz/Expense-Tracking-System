import requests
import streamlit as st
from datetime import datetime
from fastapi import Response
from hypothesis.internal.charmap import categories
from openpyxl.xml.constants import MIN_ROW
from add_update_ui import add_update_tab
from analytics_ui import analytics_tab

# from jsonschema.benchmarks.const_vs_enum import value

API_URL = "http://localhost:8000/"

st.title('Expense Tracking System')

tab1, tab2 = st.tabs(["Add/Update" , "Analytics"])

with tab1:
    add_update_tab()
with tab2:
    analytics_tab()