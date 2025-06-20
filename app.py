import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- API CONFIG ---
API_KEY = st.secrets["api_keys"]["alpha_vantage"]
BASE_URL = "https://www.alphavantage.co/query"

# --- FINANCIAL STATEMENT FUNCTIONS ---
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

# --- FORMATTERS ---
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

# --- DATA FETCHERS ---
def get_fundamentals(ticker, statement_label):
    params = {
        "function": FUNCTIONS[statement_label],
        "symbol": ticker,
        "apikey": API_KEY
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    reports = data.get("annualReports", [])
    keys = KEY_FIELDS[FUNCTIONS[statement_label]]
    return pd.DataFrame([{k: r.get(k) for k in keys} for r in reports])

def get_overview(ticker):
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    return {label: data.get(key, None) for key, label in OVERVIEW_FIELDS.items()}

# --- PLOTTER ---
def plot_trends(df, x_col, y_cols, title):
    try:
        df[x_col] = pd.to_datetime(df[x_col])
        df = df.sort_values(x_col)
        df_clean = df[[x_col] + y_cols].copy()
        for col in y_cols:
            df_clean[col] = df_clean[col].replace('[\$,B,M,K]', '', regex=True).astype(float)

        pct_changes = {
            col: ((df_clean[col].iloc[-1] - df_clean[col].iloc[0]) / abs(df_clean[col].iloc[0]) * 100)
            if df_clean[col].iloc[0] not in [0, None] else 0
            for col in y_cols
        }

        fig = go.Figure()

        # Bars for the first column
        fig.add_trace(go.Bar(
            x=df_clean[x_col],
            y=df_clean[y_cols[0]],
            name=f"{y_cols[0]} ({pct_changes[y_cols[0]]:+.1f}%)",
            marker_color="rgba(100,150,255,0.6)"
        ))

        # Lines for all columns
        for col in y_cols:
            fig.add_trace(go.Scatter(
                x=df_clean[x_col],
                y=df_clean[col],
                mode="lines+markers",
                name=f"{col} ({pct_changes[col]:+.1f}%)",
                line=dict(width=2)
            ))

        fig.update_layout(
            title=title,
            barmode="overlay",
            xaxis_title="Fiscal Date",
            yaxis_title="Value",
            legend_title="Metric (Δ%)",
            template="plotly_white",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not plot: {title} → {e}")

# --- STREAMLIT UI ---
st.set_page_config(layout="wide")
st.title("📊 Fundamental Metrics Dashboard")

ticker = st.text_input("Enter stock ticker (e.g., IBM, AAPL, MSFT)", value="IBM").upper()

if st.button("Fetch Fundamentals"):
    # Overview
    st.subheader("Company Overview")
    overview = get_overview(ticker)
    if overview:
        overview_df = pd.DataFrame([overview])
        overview_df = format_large_numbers(overview_df)
        for label, value in overview_df.iloc[0].items():
            col1, col2 = st.columns([0.4, 0.6])
            col1.markdown(f"**{label}**")
            col2.markdown(f"{value}")
    else:
        st.warning("No overview data returned.")

    # Statements
    for section in FUNCTIONS.keys():
        st.subheader(section)
        df = get_fundamentals(ticker, section)
        if df.empty:
            st.warning(f"No data returned for {section}")
        else:
            df = prettify_columns(df)
            df = format_large_numbers(df)
            st.dataframe(df, use_container_width=True)

            if section == "Balance Sheet":
                plot_trends(df, "Fiscal Date", ["Total Assets", "Total Liabilities"], "Total Assets vs Liabilities")
            elif section == "Cash Flow":
                plot_trends(df, "Fiscal Date", ["Operating Cash Flow", "Capital Expenditures"], "Cash Flow vs CapEx")
            elif section == "Income Statement":
                plot_trends(df, "Fiscal Date", ["Total Revenue", "Net Income"], "Revenue vs Net Income")

