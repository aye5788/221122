import streamlit as st
import requests
import pandas as pd

# Load API key from Streamlit secrets
API_KEY = st.secrets["api_keys"]["alpha_vantage"]
BASE_URL = "https://www.alphavantage.co/query"

# Functions for statements
FUNCTIONS = {
    "Balance Sheet": "BALANCE_SHEET",
    "Cash Flow": "CASH_FLOW",
    "Income Statement": "INCOME_STATEMENT"
}

# Whitelisted fields for each statement
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

# Overview fields to extract and display first
OVERVIEW_FIELDS = {
    "Name": "Company Name",
    "Exchange": "Exchange",
    "Sector": "Sector",
    "Industry": "Industry",
    "MarketCapitalization": "Market Cap",
    "PERatio": "P/E Ratio",
    "PEGRatio": "PEG Ratio",
    "DividendPerShare": "Dividend/Share",
    "DividendYield": "Dividend Yield",
    "EPS": "EPS",
    "RevenuePerShareTTM": "Revenue/Share",
    "ProfitMargin": "Profit Margin",
    "ReturnOnEquityTTM": "ROE",
    "SharesOutstanding": "Shares Outstanding",
    "Beta": "Beta",
    "52WeekHigh": "52-Week High",
    "52WeekLow": "52-Week Low",
    "EVToEBITDA": "EV/EBITDA",
    "PriceToBookRatio": "Price/Book",
    "PriceToSalesRatioTTM": "Price/Sales"
}

# Format large numbers for better readability
def format_large_numbers(df):
    def _format(val):
        try:
            val = float(val)
            if abs(val) >= 1e9:
                return f"{val / 1e9:.2f}B"
            elif abs(val) >= 1e6:
                return f"{val / 1e6:.2f}M"
            elif abs(val) >= 1e3:
                return f"{val / 1e3:.2f}K"
            else:
                return f"{val:.2f}"
        except:
            return val
    return df.applymap(_format)

# Apply custom labels
def prettify_columns(df, label_map):
    return df.rename(columns=label_map)

# Pull data for a financial statement
def get_fundamentals(ticker, statement_label):
    function = FUNCTIONS[statement_label]
    params = {
        "function": function,
        "symbol": ticker,
        "apikey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()
    annual_reports = data.get("annualReports", [])
    if not annual_reports:
        return pd.DataFrame()

    key_list = KEY_FIELDS[function]
    filtered = [{k: report.get(k, None) for k in key_list} for report in annual_reports]
    return pd.DataFrame(filtered)

# Pull overview metrics
def get_overview(ticker):
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        return {}

    data = response.json()
    filtered = {label: data.get(key, None) for key, label in OVERVIEW_FIELDS.items()}
    return filtered

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Fundamental Metrics Dashboard")

ticker = st.text_input("Enter stock ticker (e.g., IBM, AAPL, MSFT)", value="IBM").upper()

if st.button("Fetch Fundamentals"):
    # --- Overview Section ---
    st.subheader("Company Overview")
    overview = get_overview(ticker)
    if overview:
        overview_df = pd.DataFrame([overview])
        overview_df = format_large_numbers(overview_df)
        st.dataframe(overview_df, use_container_width=True)
    else:
        st.warning("No overview data returned.")

    # --- Financial Statements ---
    for statement in FUNCTIONS.keys():
        st.subheader(statement)
        df = get_fundamentals(ticker, statement)
        if df.empty:
            st.warning(f"No data returned for {statement}")
        else:
            df = format_large_numbers(df)
            df = prettify_columns(df, {k: v for k, v in OVERVIEW_FIELDS.items() if k in df.columns})
            st.dataframe(df, use_container_width=True)

