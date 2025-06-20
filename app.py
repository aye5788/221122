import streamlit as st
import requests
import pandas as pd

# Load secret key
API_KEY = st.secrets["api_keys"]["alpha_vantage"]

# Define endpoints and fields to extract
BASE_URL = "https://www.alphavantage.co/query"
FUNCTIONS = {
    "Balance Sheet": "BALANCE_SHEET",
    "Cash Flow": "CASH_FLOW",
    "Income Statement": "INCOME_STATEMENT"
}

# Define the key fields for each statement
KEY_FIELDS = {
    "BALANCE_SHEET": [
        "fiscalDateEnding", "totalAssets", "totalLiabilities", "totalShareholderEquity",
        "currentAssets", "currentLiabilities", "cashAndCashEquivalentsAtCarryingValue",
        "shortTermDebt", "longTermDebt", "retainedEarnings"
    ],
    "CASH_FLOW": [
        "fiscalDateEnding", "operatingCashflow", "capitalExpenditures", "netIncome",
        "depreciationDepletionAndAmortization", "dividendPayoutCommonStock",
        "cashflowFromInvestment", "cashflowFromFinancing"
    ],
    "INCOME_STATEMENT": [
        "fiscalDateEnding", "totalRevenue", "grossProfit", "operatingIncome", "netIncome",
        "ebit", "ebitda", "costOfRevenue", "sellingGeneralAndAdministrative",
        "researchAndDevelopment", "incomeTaxExpense", "interestExpense", "interestIncome",
        "depreciationAndAmortization"
    ]
}

# Function to pull and filter data
def get_fundamentals(ticker, statement_type):
    params = {
        "function": FUNCTIONS[statement_type],
        "symbol": ticker,
        "apikey": API_KEY
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    annuals = data.get("annualReports", [])
    if not annuals:
        return pd.DataFrame()
    # Keep only selected fields
    records = [{k: report.get(k) for k in KEY_FIELDS[FUNCTIONS[statement_type]]} for report in annuals]
    return pd.DataFrame(records)

# Streamlit UI
st.title("📊 Fundamental Metrics Dashboard")
ticker = st.text_input("Enter a stock ticker (e.g., IBM, AAPL)", value="IBM")

if st.button("Fetch Fundamentals"):
    for statement in FUNCTIONS.keys():
        st.subheader(statement)
        df = get_fundamentals(ticker, statement)
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning(f"No data returned for {statement}")
