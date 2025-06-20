import streamlit as st
import requests
import pandas as pd

# Load API key from Streamlit secrets
API_KEY = st.secrets["api_keys"]["alpha_vantage"]
BASE_URL = "https://www.alphavantage.co/query"

# Function names for financials
FUNCTIONS = {
    "Balance Sheet": "BALANCE_SHEET",
    "Cash Flow": "CASH_FLOW",
    "Income Statement": "INCOME_STATEMENT"
}

# Field mappings for each financial statement
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

# Human-readable column name mapping
PRETTY_LABELS = {
    "fiscalDateEnding": "Fiscal Date",
    "totalAssets": "Total Assets",
    "totalLiabilities": "Total Liabilities",
    "totalShareholderEquity": "Total Shareholder Equity",
    "currentAssets": "Current Assets",
    "currentLiabilities": "Current Liabilities",
    "cashAndCashEquivalentsAtCarryingValue": "Cash Equivalents at Carrying Value",
    "shortTermDebt": "Short-Term Debt",
    "longTermDebt": "Long-Term Debt",
    "retainedEarnings": "Retained Earnings",
    "operatingCashflow": "Operating Cash Flow",
    "capitalExpenditures": "Capital Expenditures",
    "netIncome": "Net Income",
    "depreciationDepletionAndAmortization": "Amortization",
    "dividendPayoutCommonStock": "Dividend Payout (Common Stock)",
    "cashflowFromInvestment": "Cash Flow from Investment",
    "cashflowFromFinancing": "Cash Flow from Financing",
    "totalRevenue": "Total Revenue",
    "grossProfit": "Gross Profit",
    "operatingIncome": "Operating Income",
    "ebit": "EBIT",
    "ebitda": "EBITDA",
    "costOfRevenue": "Cost of Revenue",
    "sellingGeneralAndAdministrative": "SG&A",
    "researchAndDevelopment": "R&D",
    "incomeTaxExpense": "Income Tax Expense",
    "interestExpense": "Interest Expense",
    "interestIncome": "Interest Income"
}

# Overview field mapping (used only for overview display)
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

def prettify_columns(df):
    return df.rename(columns=PRETTY_LABELS)

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
    reports = data.get("annualReports", [])
    if not reports:
        return pd.DataFrame()
    keys = KEY_FIELDS[function]
    filtered = [{k: r.get(k, None) for k in keys} for r in reports]
    return pd.DataFrame(filtered)

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
    return {label: data.get(key, None) for key, label in OVERVIEW_FIELDS.items()}

# Streamlit App Layout
st.set_page_config(layout="wide")
st.title("📊 Fundamental Metrics Dashboard")

ticker = st.text_input("Enter stock ticker (e.g., IBM, AAPL, MSFT)", value="IBM").upper()

if st.button("Fetch Fundamentals"):
    # --- Company Overview ---
    st.subheader("Company Overview")
    overview = get_overview(ticker)
    if overview:
        df = pd.DataFrame([overview])
        df = format_large_numbers(df)
        for label, value in df.iloc[0].items():
            col1, col2 = st.columns([0.4, 0.6])
            col1.markdown(f"**{label}**")
            col2.markdown(f"{value}")
    else:
        st.warning("No overview data returned.")

    # --- Financial Statements ---
    for section in FUNCTIONS.keys():
        st.subheader(section)
        df = get_fundamentals(ticker, section)
        if df.empty:
            st.warning(f"No data returned for {section}")
        else:
            df = prettify_columns(df)
            df = format_large_numbers(df)
            st.dataframe(df, use_container_width=True)

