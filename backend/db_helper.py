import mysql.connector
from contextlib import contextmanager
from logging_setup import setup_logger

logger = setup_logger('db_helper')

@contextmanager
def get_db_cursor(commit = False):
    connection = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "root",
        database = "expense_manager"
    )
    cursor = connection.cursor(dictionary=True)
    yield cursor

    if commit:
        connection.commit()

    cursor.close()
    connection.close()

def fetch_all_record():
    with get_db_cursor() as cursor:
        cursor.execute("select * from expenses")
        expenses = cursor.fetchall() # give result in tuple format
        for expense in expenses:
            print(expense)
        return expenses

def fetch_expenses_for_date(expense_date):
    logger.info(f"fetch_expenses_for_date: {expense_date}")
    with get_db_cursor() as cursor:
        cursor.execute("select * from expenses where expense_date = %s", (expense_date,))
        expenses = cursor.fetchall()  # give result in tuple format
        for expense in expenses:
            print(expense)
        return expenses

def insert_expense(expense_date, amount, category, notes):
    logger.info(f"insert_expense called with date : {expense_date}, amount : {amount}, category : {category}, notes : {notes}")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "insert into expenses (expense_date, amount, category, notes) values (%s, %s, %s, %s)",
            (expense_date, amount, category, notes)
        )

def delete_expenses_for_date(expense_date):
    logger.info(f"fetch_expenses_for_date: {expense_date}")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "delete from expenses where expense_date = %s", (expense_date,)
        )
        print("Expenses deleted successfully")

def fetch_expense_summary(start_date, end_date):
    logger.info(f"fetch_expense_summary called with start_date : {start_date}, end_date : {end_date}")
    with get_db_cursor() as cursor:
        cursor.execute(
            '''SELECT category, sum(amount) as total
            FROM expenses
            WHERE expense_date
            BETWEEN %s and %s
            GROUP BY category ''',
            (start_date, end_date)
        )
        data = cursor.fetchall()
        return data

if __name__ == "__main__":
    # fetch_all_record()

    # print("---- Expenses for 12/05 ----")
    # insert_expense("2025-12-05", 500, "Kacchi", "Treat By Razwan")
    # expenses = fetch_expenses_for_date("2025-12-05")
    # print(expenses)
    # print("---- Delete for 12/05 ----")
    # delete_expenses_for_date("2025-12-05")
    # fetch_expenses_for_date("2025-12-01")
    # print("---- Again fetch Expenses for 08/20 ----")
    # fetch_expenses_for_date("2025-12-01")
    expenses = fetch_expenses_for_date("2024-09-30")
    print(expenses)
    summary = fetch_expense_summary("2024-08-01", "2024-08-05")
    for record in summary:
        print(record)