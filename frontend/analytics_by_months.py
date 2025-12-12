import requests
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import io

API_URL = "http://localhost:8000"  # no trailing slash

st.set_page_config(page_title="Monthly Analytics", layout="wide")

def month_start_end(year: int, month: int):
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)
    return start, end

def months_between(start_date: date, end_date: date):
    """Yield (year, month) pairs from start_date's month up to end_date's month inclusive."""
    y, m = start_date.year, start_date.month
    while (y < end_date.year) or (y == end_date.year and m <= end_date.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1

def call_analytics_api(start_date: date, end_date: date):
    payload = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    try:
        resp = requests.post(f"{API_URL}/analytics/", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API request failed for {payload['start_date']} -> {payload['end_date']}: {e}")
        return None

def build_monthly_dataframe(start_date: date, end_date: date):
    # Collect results per month
    month_labels = []
    month_results = []  # list of dicts: {category: total, ...}

    for y, m in months_between(start_date, end_date):
        start, end = month_start_end(y, m)
        label = start.strftime("%b %Y")
        month_labels.append(label)

        data = call_analytics_api(start, end)
        if data is None:
            # return None to indicate failure
            return None

        # convert {"Food": {"total": 100, "percentage": 50}, ...} --> {"Food": 100, ...}
        totals = {cat: payload["total"] for cat, payload in data.items()}
        month_results.append(totals)

    # Make combined DataFrame: rows = categories, cols = months
    # first collect all categories
    categories = sorted({cat for d in month_results for cat in d.keys()})
    df = pd.DataFrame(index=categories, columns=month_labels).fillna(0.0)

    for label, res in zip(month_labels, month_results):
        for cat, total in res.items():
            df.at[cat, label] = float(total)

    # Add a "Total" row/column if desired. We'll also produce monthly totals series
    monthly_totals = df.sum(axis=0)
    df.index.name = "Category"
    return df, monthly_totals

def to_excel_bytes(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Monthly Breakdown")
    return output.getvalue()

# --- UI ---
def analytics_by_month_ui():
    st.title("Expense analytics — month by month")

    col1, col2, col3 = st.columns([1,1,2])

    with col1:
        start_month = st.date_input("Start month (pick any day within month)", value=datetime(2024, 8, 1))
    with col2:
        end_month = st.date_input("End month (pick any day within month)", value=datetime(2024, 8, 5))

    with col3:
        view_percent = st.checkbox("Show each month's percentage (per-month %) instead of absolute totals", value=False)
        show_stack = st.checkbox("Show stacked bar chart by category", value=True)
        show_table = st.checkbox("Show table", value=True)

    if st.button("Get monthly analytics"):
        # normalize start/end to first/last day of month
        s_date = date(start_month.year, start_month.month, 1)
        last_day = calendar.monthrange(end_month.year, end_month.month)[1]
        e_date = date(end_month.year, end_month.month, last_day)

        if s_date > e_date:
            st.error("Start month must be before or equal to end month.")
        else:
            with st.spinner("Fetching analytics for each month..."):
                result = build_monthly_dataframe(s_date, e_date)

            if result is None:
                st.error("One or more API calls failed. See messages above.")
            else:
                df, monthly_totals = result

                if view_percent:
                    # convert each column to percentage of that month's total
                    df_percent = df.div(monthly_totals, axis=1).fillna(0) * 100
                    display_df = df_percent.round(2)
                    st.subheader("Monthly breakdown (percent of month total)")
                else:
                    display_df = df.round(2)
                    st.subheader("Monthly breakdown (absolute totals)")

                if show_table:
                    st.dataframe(display_df)

                # Line chart: total expenses per month
                st.subheader("Total expense per month")
                totals_df = pd.DataFrame({
                    "month": monthly_totals.index,
                    "total": monthly_totals.values
                })
                totals_df = totals_df.set_index("month")
                st.line_chart(totals_df)

                if show_stack:
                    # Stacked bar using Altair
                    try:
                        import altair as alt
                        long = display_df.reset_index().melt(id_vars="Category", var_name="Month", value_name="Value")
                        chart = (
                            alt.Chart(long)
                            .mark_bar()
                            .encode(
                                x=alt.X("Month:N", sort=monthly_totals.index.tolist()),
                                y=alt.Y("Value:Q"),
                                color=alt.Color("Category:N"),
                                tooltip=["Category", "Month", "Value"]
                            )
                            .properties(width=900, height=400)
                        )
                        st.altair_chart(chart, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not render stacked chart with Altair: {e}")

                # Download as Excel
                excel_bytes = to_excel_bytes(display_df)
                st.download_button(
                    label="Download monthly breakdown as Excel",
                    data=excel_bytes,
                    file_name="monthly_breakdown.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.success("Done.")
