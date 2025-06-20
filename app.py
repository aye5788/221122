import streamlit as st
import requests
import pandas as pd

# Load API key from secrets
API_KEY = st.secrets["api_keys"]["alpha_vantage"]
BASE_URL = "https://www.alphavantage.co/query"

FUNCTIONS = {
    "Balance Sheet": "BALANCE_SHEET",
    "Cash Flow": "CASH_FLOW",
    "Income Statement": "INCOME_STATEMENT"
}

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

# Custom column name mapping for pretty display
COLUMN_LABELS = {
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

def format_large_numbers(df):
    def _format(val):
        try:
            val = float(val)
            if abs(val) >= 1e9:
                return f"{val/1e9:.2f}B"
            elif abs(val) >= 1e6:
                return f"{val/1e6:.2f}M"
            elif abs(val) >= 1e3:
                return f"{val/1e3:.2f}K"
            else:
                return f"{val:.0f}"
        except:
            return val
    return df.applymap(_format)

# Apply the custom labels
def prettify_columns(df):
    return df.rename(columns=COLUMN_LABELS)

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
    df = pd.DataFrame(filtered)
    return df

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Fundamental Metrics Dashboard")

ticker = st.text_input("Enter stock ticker (e.g., IBM, AAPL, MSFT)", value="IBM").upper()

if st.button("Fetch Fundamentals"):
    for statement in FUNCTIONS.keys():
        st.subheader(statement)
        df = get_fundamentals(ticker, statement)
        if df.empty:
            st.warning(f"No data returned for {statement}")
        else:
            df = format_large_numbers(df)
            df = prettify_columns(df)
            st.dataframe(df, use_container_width=True)

