#!/usr/bin/env python3
"""
Stock Screener - Optimized GUI Version (Streamlit)
Matches CLI version logic
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(page_title="Stock Screener", page_icon="📈", layout="wide")

# Predefined stock groups - USA only (reliable with yfinance)
STOCK_GROUPS = {
    "S&P 100": [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'GOOGL', 'GOOG', 'TSLA', 'BRK-B', 'UNH',
        'XOM', 'JNJ', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'LLY', 'ABBV',
        'MRK', 'PEP', 'KO', 'COST', 'AVGO', 'TMO', 'WMT', 'MCD', 'CSCO', 'ACN',
        'ABT', 'DHR', 'BAC', 'DIS', 'VZ', 'ADBE', 'CRM', 'TXN', 'NKE', 'NEE',
        'PM', 'UPS', 'MS', 'RTX', 'HON', 'INTC', 'QCOM', 'ORCL', 'IBM', 'AMD',
        'SBUX', 'T', 'GS', 'BLK', 'AMGN', 'CAT', 'GE', 'LOW', 'SPGI', 'MDT',
        'GILD', 'BKNG', 'ISRG', 'VRTX', 'AXP', 'SYK', 'PLD', 'MMM', 'CVS', 'CHTR',
        'LRCX', 'DE', 'ADP', 'MRSH', 'TJX', 'REGN', 'ZTS', 'CI', 'CME', 'CB',
        'SCHW', 'BDX', 'MO', 'SO', 'DUK', 'CL', 'ETN', 'ITW', 'APD', 'PNC',
        'NSC', 'EOG', 'SHW', 'ICE', 'CSX', 'EMR', 'FCX', 'MAR', 'AON', 'SLB'
    ],
    "Dow 30": [
        'AAPL', 'MSFT', 'UNH', 'JNJ', 'V', 'WMT', 'JPM', 'PG', 'HD', 'MA',
        'DIS', 'NVDA', 'NFLX', 'INTC', 'VZ', 'KO', 'PEP', 'MRK', 'CSCO', 'ABT',
        'CRM', 'ADBE', 'TXN', 'AVGO', 'NKE', 'CMCSA', 'XOM', 'BA', 'IBM', 'MCD'
    ],
    "NASDAQ 100 (Top 50)": [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'GOOGL', 'GOOG', 'TSLA', 'BRK-B', 'AVGO',
        'COST', 'LLY', 'ABBV', 'MRK', 'PEP', 'WMT', 'MCD', 'CSCO', 'ACN', 'ABT',
        'DHR', 'BAC', 'DIS', 'VZ', 'ADBE', 'CRM', 'TXN', 'NKE', 'NEE', 'PM',
        'UPS', 'MS', 'RTX', 'HON', 'INTC', 'QCOM', 'ORCL', 'IBM', 'AMD', 'SBUX',
        'T', 'GS', 'BLK', 'AMGN', 'CAT', 'GE', 'LOW', 'SPGI', 'MDT', 'ISRG'
    ],
    "Tech Giants": [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'META', 'AMZN', 'NVDA', 'TSLA', 'ORCL', 'IBM',
        'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO', 'CRM', 'ADBE', 'NFLX', 'CSCO', 'NOW'
    ],
    "Financials": [
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'USB', 'TFC',
        'AXP', 'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV', 'SPGI', 'ICE', 'CME'
    ],
    "Healthcare": [
        'LLY', 'JNJ', 'UNH', 'ABBV', 'MRK', 'PFE', 'ABT', 'TMO', 'DHR', 'BMY',
        'AMGN', 'GILD', 'ISRG', 'VRTX', 'REGN', 'ZTS', 'CVS', 'CI', 'HCA', 'MCK'
    ],
    "Energy": [
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PSX', 'MPC', 'VLO', 'OXY', 'HES',
        'DVN', 'FANG', 'PXD', 'BKR', 'HAL', 'NOV', 'APA', 'CLR', 'MRO', 'APC'
    ],
    "Dividend Aristocrats": [
        'KO', 'PEP', 'PG', 'VZ', 'T', 'MO', 'PM', 'IBM', 'JNJ', 'XOM',
        'CVX', 'MCD', 'WMT', 'HD', 'LOW', 'BA', 'CAT', 'GE', 'MMM', 'HON'
    ]
}

def calculate_rsi(prices, period=14):
    """Calculate RSI 14 using Wilder's smoothing method"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else None


def calc_yoy_growth(annual_stmt, row_keys):
    """
    Calculate YoY % growth using the annual income statement.
    Compares the most recent fiscal year (column 0) vs the prior year (column 1).
    yfinance annual income_stmt reliably returns 4 years of data, so this is
    far more robust than trying to sum 8 quarters from quarterly_income_stmt
    (which only provides ~4 quarters).
    row_keys: list of possible row label names to try in order.
    """
    try:
        if annual_stmt is None or annual_stmt.empty:
            return None

        # Find whichever row key exists
        key = None
        for k in row_keys:
            if k in annual_stmt.index:
                key = k
                break
        if key is None:
            return None

        row = annual_stmt.loc[key]
        # Drop NaN and convert to float, keeping column order (newest first)
        values = [float(v) for v in row.values if v is not None and not pd.isna(v)]

        if len(values) < 2:
            return None

        current_year = values[0]   # most recent fiscal year
        prior_year   = values[1]   # one year prior

        if prior_year == 0:
            return None

        growth = ((current_year - prior_year) / abs(prior_year)) * 100
        return round(growth, 2)
    except Exception:
        return None


def get_financial_data(ticker_symbol):
    """Get all financial data for a ticker - matches CLI version"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # ── Debt / Equity ─────────────────────────────────────────────────────
        # Always default to 0; only override if we get a clean, plausible value.
        debt_to_equity = 0
        try:
            bs = ticker.balance_sheet
            if not bs.empty:
                total_debt = None
                total_equity = None
                for row in ['Total Debt', 'Short Long Term Debt', 'Long Term Debt', 'TotalLiabilities']:
                    if row in bs.index:
                        val = bs.loc[row].iloc[0]
                        total_debt = val.item() if hasattr(val, 'item') else float(val)
                        break
                for row in ['Total Stockholder Equity', 'Stockholders Equity', 'Total Equity']:
                    if row in bs.index:
                        val = bs.loc[row].iloc[0]
                        total_equity = val.item() if hasattr(val, 'item') else float(val)
                        break
                if total_debt is not None and total_equity and total_equity > 0:
                    candidate = total_debt / total_equity
                    if 0 <= candidate <= 100:
                        debt_to_equity = candidate
        except Exception:
            pass

        # Fallback to yfinance info field if balance-sheet attempt left us at 0
        if debt_to_equity == 0:
            raw_de = info.get('debtToEquity', None)
            if raw_de is not None:
                try:
                    candidate = float(raw_de)
                    if 0 <= candidate <= 100:
                        debt_to_equity = candidate
                except (TypeError, ValueError):
                    pass

        # ── P/E Ratio ─────────────────────────────────────────────────────────
        # Default to 0 when not available or not a valid positive number.
        raw_pe = info.get('trailingPE', None)
        try:
            pe_ratio = float(raw_pe) if raw_pe is not None else 0
            if pe_ratio < 0 or not pd.notna(pe_ratio):
                pe_ratio = 0
        except (TypeError, ValueError):
            pe_ratio = 0

        forward_pe = info.get('forwardPE', None)
        if forward_pe is not None:
            try:
                forward_pe = float(forward_pe)
                if not pd.notna(forward_pe):
                    forward_pe = None
            except (TypeError, ValueError):
                forward_pe = None

        # ── Other info fields ─────────────────────────────────────────────────
        dividend_yield    = info.get('dividendYield', 0) or 0
        net_profit_margin = info.get('profitMargins', None)
        company_name      = info.get('longName', None) or info.get('shortName', None)
        sector            = info.get('sector', None)
        industry          = info.get('industry', None)

        rec_map = {
            'strongBuy': 'Strong Buy', 'buy': 'Buy',
            'hold': 'Hold', 'sell': 'Sell', 'strongSell': 'Strong Sell'
        }
        recommendation = rec_map.get(info.get('recommendationKey', None), info.get('recommendationKey', None))

        # ── Price history / RSI ───────────────────────────────────────────────
        hist = ticker.history(period="1y")
        if hist.empty or len(hist) < 30:
            return None
        rsi = calculate_rsi(hist['Close'])

        # ── Quarterly income statement (Net Income TTM only) ───────────────
        quarterly_income = None
        try:
            quarterly_income = ticker.quarterly_income_stmt
        except Exception:
            pass

        # Net Income TTM (sum of last 4 quarters)
        net_income_ttm_total = None
        try:
            if quarterly_income is not None and not quarterly_income.empty:
                ni_key = None
                for key in ['Net Income', 'NetIncome', 'Net profit', 'NetIncomeAvailabletoCommon']:
                    if key in quarterly_income.index:
                        ni_key = key
                        break
                if ni_key:
                    quarters = []
                    for col in quarterly_income.columns[:4]:
                        ni = quarterly_income.loc[ni_key, col]
                        if ni is not None and not pd.isna(ni):
                            v = ni.item() if hasattr(ni, 'item') else float(ni)
                            if v > 0:
                                quarters.append(v)
                    if quarters:
                        net_income_ttm_total = sum(quarters)
        except Exception:
            pass

        # ── Annual income statement (YoY growth: most recent vs prior year) ──
        # ticker.income_stmt returns columns newest->oldest, typically 4 years.
        # Much more reliable than aggregating 8 quarterly rows (only ~4 available).
        annual_income = None
        try:
            annual_income = ticker.income_stmt
        except Exception:
            pass

        # ── YoY % Change: Total Revenue ──────────────────────────────────────
        revenue_yoy = calc_yoy_growth(
            annual_income,
            ['Total Revenue', 'TotalRevenue', 'Revenue', 'Net Revenue']
        )

        # ── YoY % Change: Net Income ──────────────────────────────────────────
        ni_yoy = calc_yoy_growth(
            annual_income,
            ['Net Income', 'NetIncome', 'Net profit', 'NetIncomeAvailabletoCommon']
        )

        # ── Expected earnings growth from PE vs forward PE ────────────────────
        expected_growth = None
        if pe_ratio and forward_pe and forward_pe != 0:
            expected_growth = round(((pe_ratio / forward_pe) - 1) * 100, 2)

        return {
            'Ticker':                           ticker_symbol,
            'Company Name':                     company_name,
            'Price':                            round(hist['Close'].iloc[-1], 2),
            'RSI14':                            round(rsi, 2) if rsi else None,
            'Dividend %':                       dividend_yield,
            'D/E':                              round(debt_to_equity, 2),
            'P/E':                              pe_ratio,
            'Forward P/E':                      forward_pe,
            'Expected Earnings Growth Rate (G)': expected_growth,
            'Net Margin %':                     round(net_profit_margin * 100, 2) if net_profit_margin else None,
            'Recommendation':                   recommendation,
            'Net Income TTM':                   round(net_income_ttm_total / 1e9, 2) if net_income_ttm_total else None,
            '1Y Revenue Growth %':              revenue_yoy,
            '1Y Net Income Growth %':           ni_yoy,
            'Sector':                           sector,
            'Industry':                         industry,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600)
def fetch_all_data(tickers):
    """Fetch data for all tickers"""
    results = []
    progress_bar = st.progress(0)

    for i, ticker in enumerate(tickers):
        data = get_financial_data(ticker)
        if data:
            results.append(data)
        else:
            results.append({
                'Ticker': ticker, 'Company Name': ticker,
                'Price': None, 'RSI14': None, 'Dividend %': None,
                'D/E': None, 'P/E': None, 'Net Margin %': None,
                'Recommendation': None, 'Net Income TTM': None,
                '1Y Revenue Growth %': None, '1Y Net Income Growth %': None,
            })
        progress_bar.progress((i + 1) / len(tickers))

    progress_bar.empty()
    return pd.DataFrame(results)


def main():
    st.title("📈 Stock Screener")

    # Stock group selector
    st.sidebar.header("📊 Stock Group")
    selected_group = st.sidebar.selectbox(
        "Select stock group:",
        options=list(STOCK_GROUPS.keys()),
        index=0
    )

    tickers = STOCK_GROUPS[selected_group]
    st.markdown(f"**{selected_group}** - {len(tickers)} stocks")

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.header("Filter Criteria")

    rsi_max        = st.sidebar.slider("RSI14 (max)",                    20,    80,   45)
    div_min        = st.sidebar.slider("Dividend Yield % (min)",          0.0,  10.0,  2.0, step=0.5)
    de_max         = st.sidebar.slider("Debt/Equity (max)",               0.1,   3.0,  1.0, step=0.1)
    pe_max         = st.sidebar.slider("P/E Ratio (max)",                 0,   100,   50,  step=1)
    ni_min         = st.sidebar.slider("Net Income TTM min ($B)",         0,    50,    0,  step=1)
    rev_growth_min = st.sidebar.slider("1Y Revenue Growth % (min)",     -50,   100,    0,  step=1)
    ni_growth_min  = st.sidebar.slider("1Y Net Income Growth % (min)",  -50,   100,    0,  step=1)

    show_all = st.sidebar.checkbox("Show all stocks", value=True)

    # ── Fetch data ────────────────────────────────────────────────────────────
    with st.spinner("Fetching stock data..."):
        df = fetch_all_data(tickers)

    # Separate stocks with no data found
    df_not_found = df[df['Company Name'].isna() | (df['Company Name'] == df['Ticker'])]
    df_found     = df[~(df['Company Name'].isna() | (df['Company Name'] == df['Ticker']))].copy()

    # Ensure optional columns exist
    for col in ['Sector', 'Industry', '1Y Revenue Growth %', '1Y Net Income Growth %',
                'Forward P/E', 'Expected Earnings Growth Rate (G)']:
        if col not in df_found.columns:
            df_found[col] = None

    # ── Apply filters ─────────────────────────────────────────────────────────
    df_found['Meets Criteria'] = (
        (df_found['RSI14'].notna())         & (df_found['RSI14'] < rsi_max) &
        (df_found['Dividend %'] >= div_min) &
        (df_found['D/E'].notna())           & (df_found['D/E'] < de_max) &
        ((df_found['P/E'].isna())           | (df_found['P/E'] < pe_max)) &
        ((df_found['Net Income TTM'].isna())| (df_found['Net Income TTM'] >= ni_min)) &
        # Revenue growth: only filter rows where the metric is available
        ((df_found['1Y Revenue Growth %'].isna()) | (df_found['1Y Revenue Growth %'] >= rev_growth_min)) &
        # Net income growth: only filter rows where the metric is available
        ((df_found['1Y Net Income Growth %'].isna()) | (df_found['1Y Net Income Growth %'] >= ni_growth_min))
    )

    qualifying_count = df_found['Meets Criteria'].sum()

    if not show_all:
        df_found = df_found[df_found['Meets Criteria']]

    # ── Format for display ────────────────────────────────────────────────────
    st.subheader(f"Results: {len(df_found)} stocks ({qualifying_count} qualify)")

    display_df = df_found.copy()
    display_df['Dividend %']                      = display_df['Dividend %'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    display_df['Net Margin %']                    = display_df['Net Margin %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['D/E']                             = display_df['D/E'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    display_df['P/E']                             = display_df['P/E'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    display_df['Forward P/E']                     = display_df['Forward P/E'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    display_df['Expected Earnings Growth Rate (G)']= display_df['Expected Earnings Growth Rate (G)'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['Price']                           = display_df['Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
    display_df['Net Income TTM']                  = display_df['Net Income TTM'].apply(lambda x: f"${x:.1f}B" if pd.notna(x) else "-")
    display_df['1Y Revenue Growth %']             = display_df['1Y Revenue Growth %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['1Y Net Income Growth %']          = display_df['1Y Net Income Growth %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['Sector']                          = display_df['Sector'].fillna("-")
    display_df['Industry']                        = display_df['Industry'].fillna("-")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )

    # ── Export ────────────────────────────────────────────────────────────────
    st.subheader("📥 Export")
    col1, col2 = st.columns(2)

    df_export = pd.concat([df_found, df_not_found], ignore_index=True)

    with col1:
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📊 Download CSV", csv, "stocks.csv", "text/csv")

    with col2:
        json_data = df_export.to_json(orient='records', indent=2)
        st.download_button("📋 Download JSON", json_data, "stocks.json", "application/json")

    # ── Sidebar summary ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Summary")
    st.sidebar.write(f"✅ Qualifying: **{qualifying_count}**")
    st.sidebar.write(f"📊 Total: **{len(df_found)}**")
    st.sidebar.write(
        f"📈 Filters: RSI<{rsi_max}, Div>{div_min}%, D/E<{de_max}, "
        f"P/E<{pe_max}, NI>${ni_min}B, "
        f"RevGrowth>{rev_growth_min}%, NIGrowth>{ni_growth_min}%"
    )

    # ── Stocks with no data ───────────────────────────────────────────────────
    if not df_not_found.empty:
        st.subheader("⚠️ Stocks with no data found")
        st.write(", ".join(df_not_found['Ticker'].tolist()))


if __name__ == "__main__":
    main()
