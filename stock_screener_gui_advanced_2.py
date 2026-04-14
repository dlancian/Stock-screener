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

def get_financial_data(ticker_symbol):
    """Get all financial data for a ticker - matches CLI version"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Get D/E from balance sheet (same as CLI)
        debt_to_equity = None
        try:
            bs = ticker.balance_sheet
            if not bs.empty:
                total_debt = None
                total_equity = None
                for row in ['Total Debt', 'Short Long Term Debt', 'Long Term Debt', 'TotalLiabilities']:
                    if row in bs.index:
                        total_debt = bs.loc[row].iloc[0]
                        if hasattr(total_debt, 'item'):
                            total_debt = total_debt.item()
                        break
                for row in ['Total Stockholder Equity', 'Stockholders Equity', 'Total Equity']:
                    if row in bs.index:
                        total_equity = bs.loc[row].iloc[0]
                        if hasattr(total_equity, 'item'):
                            total_equity = total_equity.item()
                        break
                if total_debt and total_equity and total_equity > 0:
                    debt_to_equity = total_debt / total_equity
        except:
            pass
        
        if not debt_to_equity or debt_to_equity > 100:
            debt_to_equity = info.get('debtToEquity', 0)
        
        if not debt_to_equity or debt_to_equity > 100:
            debt_to_equity = 0
        
        # Dividend yield - yfinance returns as percentage (e.g., 2.5 for 2.5%), default to 0 if not found
        dividend_yield = info.get('dividendYield', 0) or 0
        
        # P/E ratio - default to 0 if not found
        pe_ratio = info.get('trailingPE', 0) or 0
        forward_pe = info.get('forwardPE', None)
        
        # Net Profit Margin
        net_profit_margin = info.get('profitMargins', None)
        
        # Return on Invested Capital (ROIC)
        roic = info.get('returnOnEquity', None)  # If ROIC not directly available, use ROE as proxy
        
        # Company name, sector, industry
        company_name = info.get('longName', None) or info.get('shortName', None)
        sector = info.get('sector', None)
        industry = info.get('industry', None)
        
        # Analyst recommendation
        recommendation = info.get('recommendationKey', None)
        rec_map = {'strongBuy': 'Strong Buy', 'buy': 'Buy', 'hold': 'Hold', 'sell': 'Sell', 'strongSell': 'Strong Sell'}
        recommendation = rec_map.get(recommendation, recommendation)
        
        # Get price history for RSI
        hist = ticker.history(period="1y")
        if hist.empty or len(hist) < 30:
            return None
        rsi = calculate_rsi(hist['Close'])
        
        # Get net income TTM
        net_income_ttm = []
        try:
            income = ticker.quarterly_income_stmt
            if not income.empty:
                ni_key = None
                for key in ['Net Income', 'NetIncome', 'Net profit', 'NetIncomeAvailabletoCommon']:
                    if key in income.index:
                        ni_key = key
                        break
                if ni_key:
                    for col in income.columns[:4]:
                        ni = income.loc[ni_key, col]
                        if ni and hasattr(ni, 'item'):
                            ni = ni.item()
                        if ni and ni > 0:
                            net_income_ttm.append(ni)
        except:
            net_income_ttm = []
        
        net_income_total = sum(net_income_ttm) if net_income_ttm else None
        
        # Get revenue for YoY growth calculation
        revenue_current = None
        revenue_previous = None
        try:
            inc_stmt = ticker.income_stmt
            if not inc_stmt.empty:
                for key in ['Total Revenue', 'Operating Revenue', 'Revenue']:
                    if key in inc_stmt.index:
                        rev_key = key
                        # Current year (most recent)
                        if len(inc_stmt.columns) > 0:
                            revenue_current = inc_stmt.loc[rev_key, inc_stmt.columns[0]]
                            if revenue_current and hasattr(revenue_current, 'item'):
                                revenue_current = revenue_current.item()
                        # Previous year
                        if len(inc_stmt.columns) > 1:
                            revenue_previous = inc_stmt.loc[rev_key, inc_stmt.columns[1]]
                            if revenue_previous and hasattr(revenue_previous, 'item'):
                                revenue_previous = revenue_previous.item()
                        break
        except:
            pass
        
        revenue_growth = None
        if revenue_current and revenue_previous and revenue_previous > 0:
            revenue_growth = ((revenue_current - revenue_previous) / revenue_previous) * 100
        
        # Get net income for YoY growth calculation
        ni_current = None
        ni_previous = None
        try:
            inc_stmt = ticker.income_stmt
            if not inc_stmt.empty:
                ni_key = None
                for key in ['Net Income', 'NetIncome', 'Net profit', 'NetIncomeAvailabletoCommon']:
                    if key in inc_stmt.index:
                        ni_key = key
                        break
                if ni_key:
                    if len(inc_stmt.columns) > 0:
                        ni_current = inc_stmt.loc[ni_key, inc_stmt.columns[0]]
                        if ni_current and hasattr(ni_current, 'item'):
                            ni_current = ni_current.item()
                    if len(inc_stmt.columns) > 1:
                        ni_previous = inc_stmt.loc[ni_key, inc_stmt.columns[1]]
                        if ni_previous and hasattr(ni_previous, 'item'):
                            ni_previous = ni_previous.item()
        except:
            pass
        
        net_income_growth = None
        if ni_current and ni_previous and ni_previous > 0:
            net_income_growth = ((ni_current - ni_previous) / ni_previous) * 100
        
        return {
            'Ticker': ticker_symbol,
            'Company Name': company_name,
            'Price': round(hist['Close'].iloc[-1], 2),
            'RSI14': round(rsi, 2) if rsi else None,
            # Dividend % - force to 0 if not found
        'Dividend %': dividend_yield if dividend_yield is not None else 0,
            'D/E': round(debt_to_equity, 2) if debt_to_equity else None,
            'P/E': pe_ratio,
            'Forward P/E': forward_pe,
            'Expected Earnings Growth Rate (G)': round(((pe_ratio / forward_pe) - 1) * 100, 2) if pe_ratio and forward_pe and forward_pe != 0 else None,
            'Net Margin %': round(net_profit_margin * 100, 2) if net_profit_margin else None,
            'Recommendation': recommendation,
            'Net Income TTM': round(net_income_total / 1e9, 2) if net_income_total else None,
            '1 Yr. % Change in Total Revenue': round(revenue_growth, 2) if revenue_growth else None,
            '1 Yr. % Change in Net Income': round(net_income_growth, 2) if net_income_growth else None,
            'ROIC %': round(roic * 100, 2) if roic else None,
            'Sector': sector,
            'Industry': industry,
        }
    except Exception as e:
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
            results.append({'Ticker': ticker, 'Company Name': ticker, 'Price': None, 'RSI14': None, 'Dividend %': None, 'D/E': None, 'P/E': None, 'Net Margin %': None, 'Recommendation': None, 'Net Income TTM': None})
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
    
    # Sidebar filters
    st.sidebar.markdown("---")
    st.sidebar.header("Filter Criteria")
    
    rsi_max = st.sidebar.slider("RSI14 (max)", 20, 80, 45)
    div_min = st.sidebar.slider("Dividend Yield % (min)", 0.0, 10.0, 2.0, step=0.5)
    de_max = st.sidebar.slider("Debt/Equity (max)", 0.1, 3.0, 1.0, step=0.1)
    pe_max = st.sidebar.slider("P/E Ratio (max)", 0, 100, 50, step=1)
    rev_growth_min = st.sidebar.slider("1 Yr. Revenue Growth % (min)", -50, 100, 0, step=1)
    ni_growth_min = st.sidebar.slider("1 Yr. Net Income Growth % (min)", -50, 100, 0, step=1)
    roic_min = st.sidebar.slider("ROIC % (min)", 0, 50, 0, step=1)
    ni_min = st.sidebar.slider("Net Income TTM min ($B)", 0, 50, 0, step=1)
    
    show_all = st.sidebar.checkbox("Show all stocks", value=True)
    
    # Fetch data
    with st.spinner("Fetching stock data..."):
        df = fetch_all_data(tickers)
    
    # Separate stocks with no company name (data not found)
    df_not_found = df[df['Company Name'].isna() | (df['Company Name'] == df['Ticker'])]
    df_found = df[~(df['Company Name'].isna() | (df['Company Name'] == df['Ticker']))]
    
    # Ensure all columns exist
    for col in ['1 Yr. % Change in Total Revenue', '1 Yr. % Change in Net Income', 'ROIC %']:
        if col not in df_found.columns:
            df_found[col] = None
    
    # Apply filters (excluding sector/industry from filtering)
    df_found['Meets Criteria'] = (
        (df_found['RSI14'].notna()) & (df_found['RSI14'] < rsi_max) &
        (df_found['Dividend %'] >= div_min) &
        (df_found['D/E'] < de_max) &
        (df_found['P/E'] < pe_max) &
        ((df_found['1 Yr. % Change in Total Revenue'].isna()) | (df_found['1 Yr. % Change in Total Revenue'] >= rev_growth_min)) &
        ((df_found['1 Yr. % Change in Net Income'].isna()) | (df_found['1 Yr. % Change in Net Income'] >= ni_growth_min)) &
        ((df_found['ROIC %'].isna()) | (df_found['ROIC %'] >= roic_min)) &
        ((df_found['Net Income TTM'].isna()) | (df_found['Net Income TTM'] >= ni_min))
    )
    
    # Ensure Sector and Industry columns exist
    if 'Sector' not in df_found.columns:
        df_found['Sector'] = None
    if 'Industry' not in df_found.columns:
        df_found['Industry'] = None
    
    qualifying_count = df_found['Meets Criteria'].sum()
    
    if not show_all:
        df_found = df_found[df_found['Meets Criteria']]
    
    # Display
    st.subheader(f"Results: {len(df_found)} stocks ({qualifying_count} qualify)")
    
    # Format for display
    display_df = df_found.copy()
    display_df['Dividend %'] = display_df['Dividend %'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    display_df['Net Margin %'] = display_df['Net Margin %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['D/E'] = display_df['D/E'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    display_df['P/E'] = display_df['P/E'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    display_df['Forward P/E'] = display_df['Forward P/E'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    display_df['Expected Earnings Growth Rate (G)'] = display_df['Expected Earnings Growth Rate (G)'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
    display_df['Net Income TTM'] = display_df['Net Income TTM'].apply(lambda x: f"${x:.1f}B" if pd.notna(x) else "-")
    display_df['1 Yr. % Change in Total Revenue'] = display_df['1 Yr. % Change in Total Revenue'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['1 Yr. % Change in Net Income'] = display_df['1 Yr. % Change in Net Income'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['ROIC %'] = display_df['ROIC %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    display_df['Sector'] = display_df['Sector'].fillna("-")
    display_df['Industry'] = display_df['Industry'].fillna("-")
    
    # Show table
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=600
    )
    
    # Export
    st.subheader("📥 Export")
    col1, col2 = st.columns(2)
    
    # Combine found and not found for export
    df_export = pd.concat([df_found, df_not_found], ignore_index=True)
    
    with col1:
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📊 Download CSV",
            csv,
            "stocks.csv",
            "text/csv"
        )
    
    with col2:
        json_data = df_export.to_json(orient='records', indent=2)
        st.download_button(
            "📋 Download JSON",
            json_data,
            "stocks.json",
            "application/json"
        )
    
    # Stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Summary")
    st.sidebar.write(f"✅ Qualifying: **{qualifying_count}**")
    st.sidebar.write(f"📊 Total: **{len(df_found)}**")
    st.sidebar.write(f"📈 Filters: RSI<{rsi_max}, Div>{div_min}%, D/E<{de_max}, P/E<{pe_max}, RevGrowth>{rev_growth_min}%, NIGrowth>{ni_growth_min}%, ROIC>{roic_min}%, NI>${ni_min}B")
    
    # Show stocks with no data found
    if not df_not_found.empty:
        st.subheader("⚠️ Stocks with no data found")
        st.write(", ".join(df_not_found['Ticker'].tolist()))

if __name__ == "__main__":
    main()