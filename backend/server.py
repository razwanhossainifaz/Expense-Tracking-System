# from fastapi import FastAPI, HTTPException, Path
# from datetime import date, timedelta, datetime
# import db_helper
# import calendar
# from typing import List, Dict, Any
# from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
from datetime import date, datetime
import calendar
import db_helper

app = FastAPI()

class Expense(BaseModel):
    # expense_date: date
    amount : float
    category : str
    notes : str

class Daterange(BaseModel):
    start_date : date
    end_date : date

# # --------- helpers ----------
# def _to_iso(d: date) -> str:
#     """Return YYYY-MM-DD string for date object."""
#     return d.isoformat()
#
def month_start_end(year: int, month: int) -> Tuple[date, date]:
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last

def months_between(start_date: date, end_date: date):
    """Yield (year, month) tuples from start_date's month up to end_date's month inclusive."""
    y, m = start_date.year, start_date.month
    while (y < end_date.year) or (y == end_date.year and m <= end_date.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1
#
def build_breakdown_from_db(start: date, end: date) -> Dict[str, Dict[str, Any]]:
    """
    Query db_helper.fetch_expense_summary and convert result to:
    { category: {"total": float, "percentage": float}, ... }
    """
    # Ensure we send ISO strings to db_helper
    data = db_helper.fetch_expense_summary(_to_iso(start), _to_iso(end))
    if data is None:
        return None

    # data is expected as list of dicts like [{"category": "Food", "total": 120.0}, ...]
    total_sum = sum(row.get("total", 0) for row in data)
    breakdown: Dict[str, Dict[str, Any]] = {}
    for row in data:
        cat = row.get("category", "Uncategorized")
        total = float(row.get("total", 0) or 0)
        percentage = round((total / total_sum) * 100, 2) if total_sum != 0 else 0.0
        breakdown[cat] = {"total": total, "percentage": percentage}
    return breakdown

@app.get("/expenses/{expense_date}", response_model = List[Expense])

def get_expenses(expense_date: date):
    expenses = db_helper.fetch_expenses_for_date(expense_date)
    if expenses is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve expense from the database")
    return expenses

@app.post("/expenses/{expense_date}")

def add_or_update_expense(expense_date: date, expenses: List[Expense]):
    db_helper.delete_expenses_for_date(expense_date)
    for expense in expenses:
        db_helper.insert_expense(expense_date, expense.amount, expense.category, expense.notes)
    return {"message" : "Expenses updated successfully"}

@app.post("/analytics/")

def get_analytics(date_range: Daterange):
    data = db_helper.fetch_expense_summary(date_range.start_date, date_range.end_date)
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve expense summary from the database")
    total = 0
    total = sum([row["total"] for row in data])

    breakdown = {}

    for row in data:
        percentage = round((row['total']/total) * 100, 2) if total != 0 else 0
        breakdown[row['category']] = {
            'total': row['total'],
            "percentage": percentage
        }
    return breakdown

@app.post("/analytics/monthly")
def get_analytics_monthly(date_range: Daterange):
    """
    Return month-by-month breakdown between start_date and end_date inclusive.

    Response format:
    {
      "2024-08": {
         "Food": {"total": 100.0, "percentage": 25.0},
         "Rent": {"total": 300.0, "percentage": 75.0}
      },
      "2024-09": { ... },
      ...
    }
    """
    start = date(date_range.start_date.year, date_range.start_date.month, 1)
    last_day = calendar.monthrange(date_range.end_date.year, date_range.end_date.month)[1]
    end = date(date_range.end_date.year, date_range.end_date.month, last_day)

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    response: Dict[str, Dict[str, Any]] = {}

    try:
        for y, m in months_between(start, end):
            s, e = month_start_end(y, m)
            label = s.strftime("%Y-%m")
            breakdown = build_breakdown_from_db(s, e)
            # If DB call failed, return error (you can decide to skip instead)
            if breakdown is None:
                raise HTTPException(status_code=500, detail=f"Failed to fetch analytics for {label}")
            response[label] = breakdown
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error while building monthly analytics: {e}")

    return response

# optional simple root endpoint
@app.get("/")
def root():
    return {"message": "Expense Manager API is running"}