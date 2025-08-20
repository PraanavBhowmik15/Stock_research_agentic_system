def analyze_stock(ticker: str) -> dict:  # type: ignore[type-arg]
    import os
    from datetime import datetime, timedelta

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import yfinance as yf
    from pytz import timezone  # type: ignore

    stock = yf.Ticker(ticker)

    # Get historical data (1 year of data to ensure we have enough for 200-day MA)
    end_date = datetime.now(timezone("UTC"))
    start_date = end_date - timedelta(days=1000)
    hist = stock.history(start=start_date, end=end_date)

    # Ensure we have data
    if hist.empty:
        return {"error": "No historical data available for the specified ticker."}

    # Compute basic statistics and additional metrics
    current_price = stock.info.get("currentPrice", hist["Close"].iloc[-1])
    year_high = stock.info.get("fiftyTwoWeekHigh", hist["High"].max())
    year_low = stock.info.get("fiftyTwoWeekLow", hist["Low"].min())

    # Calculate 50-day and 200-day moving averages
    ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1]
    ma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]

    # Calculate YTD price change and percent change
    ytd_start = datetime(end_date.year, 1, 1, tzinfo=timezone("UTC"))
    ytd_data = hist.loc[ytd_start:]  # type: ignore[misc]
    if not ytd_data.empty:
        price_change = ytd_data["Close"].iloc[-1] - ytd_data["Close"].iloc[0]
        percent_change = (price_change / ytd_data["Close"].iloc[0]) * 100
    else:
        price_change = percent_change = np.nan

    # Determine trend
    if pd.notna(ma_50) and pd.notna(ma_200):
        if ma_50 > ma_200:
            trend = "Upward"
        elif ma_50 < ma_200:
            trend = "Downward"
        else:
            trend = "Neutral"
    else:
        trend = "Insufficient data for trend analysis"

    # Calculate volatility (standard deviation of daily returns)
    daily_returns = hist["Close"].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility

    # Calculate rolling volatility (30-day window)
    rolling_volatility = daily_returns.rolling(window=30).std() * np.sqrt(252)
    
    # Calculate drawdown
    cumulative_returns = (1 + daily_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    
    # Calculate return/risk ratio (Sharpe ratio approximation)
    risk_free_rate = 0.02  # Assuming 2% risk-free rate
    excess_returns = daily_returns - risk_free_rate/252
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / daily_returns.std()
    
    # Calculate rolling Sharpe ratio (30-day window)
    rolling_sharpe = (excess_returns.rolling(window=30).mean() / 
                      daily_returns.rolling(window=30).std()) * np.sqrt(252)

    # Create result dictionary
    result = {
        "ticker": ticker,
        "current_price": current_price,
        "52_week_high": year_high,
        "52_week_low": year_low,
        "50_day_ma": ma_50,
        "200_day_ma": ma_200,
        "ytd_price_change": price_change,
        "ytd_percent_change": percent_change,
        "trend": trend,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": drawdown.min(),
        "current_drawdown": drawdown.iloc[-1]
    }

    # Convert numpy types to Python native types for better JSON serialization
    for key, value in result.items():
        if isinstance(value, np.generic):
            result[key] = value.item()

    # Create directory for charts if it doesn't exist
    os.makedirs("stock_charts", exist_ok=True)

    # 1. Main stock price chart with moving averages
    plt.figure(figsize=(12, 6))
    plt.plot(hist.index, hist["Close"], label="Close Price", linewidth=1.5)
    plt.plot(hist.index, hist["Close"].rolling(window=50).mean(), label="50-day MA", linewidth=1.5)
    plt.plot(hist.index, hist["Close"].rolling(window=200).mean(), label="200-day MA", linewidth=1.5)
    plt.title(f"{ticker} Stock Price Analysis", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Price ($)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plot_file_path = f"stock_charts/{ticker}_stockprice.png"
    plt.savefig(plot_file_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Main chart saved as {plot_file_path}")
    result["plot_file_path"] = plot_file_path

    # 2. Volatility chart
    plt.figure(figsize=(12, 6))
    plt.plot(rolling_volatility.index, rolling_volatility.values, 
             color='red', linewidth=1.5, label='30-Day Rolling Volatility')
    plt.axhline(y=volatility, color='black', linestyle='--', alpha=0.7, 
                label=f'Overall Volatility: {volatility:.2%}')
    plt.title(f"{ticker} Volatility Analysis", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Annualized Volatility", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    volatility_plot_path = f"stock_charts/{ticker}_volatility.png"
    plt.savefig(volatility_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Volatility chart saved as {volatility_plot_path}")
    result["volatility_chart_path"] = volatility_plot_path

    # 3. Drawdown chart
    plt.figure(figsize=(12, 6))
    plt.fill_between(drawdown.index, drawdown.values * 100, 0, 
                     alpha=0.3, color='red', label='Drawdown')
    plt.plot(drawdown.index, drawdown.values * 100, color='red', linewidth=1.5)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    plt.title(f"{ticker} Drawdown Analysis", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Drawdown (%)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    drawdown_plot_path = f"stock_charts/{ticker}_drawdown.png"
    plt.savefig(drawdown_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Drawdown chart saved as {drawdown_plot_path}")
    result["drawdown_chart_path"] = drawdown_plot_path

    # 4. Return/Risk ratio (Sharpe ratio) chart
    plt.figure(figsize=(12, 6))
    plt.plot(rolling_sharpe.index, rolling_sharpe.values, 
             color='green', linewidth=1.5, label='30-Day Rolling Sharpe Ratio')
    plt.axhline(y=sharpe_ratio, color='black', linestyle='--', alpha=0.7, 
                label=f'Overall Sharpe Ratio: {sharpe_ratio:.2f}')
    plt.axhline(y=0, color='red', linestyle='-', alpha=0.5)
    plt.title(f"{ticker} Risk-Adjusted Returns (Sharpe Ratio)", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Sharpe Ratio", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    sharpe_plot_path = f"stock_charts/{ticker}_sharpe_ratio.png"
    plt.savefig(sharpe_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Sharpe ratio chart saved as {sharpe_plot_path}")
    result["sharpe_chart_path"] = sharpe_plot_path

    # 5. Combined metrics dashboard
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Price and moving averages
    ax1.plot(hist.index, hist["Close"], label="Close Price", linewidth=1.5)
    ax1.plot(hist.index, hist["Close"].rolling(window=50).mean(), label="50-day MA", linewidth=1.5)
    ax1.plot(hist.index, hist["Close"].rolling(window=200).mean(), label="200-day MA", linewidth=1.5)
    ax1.set_title("Stock Price & Moving Averages", fontweight='bold')
    ax1.set_ylabel("Price ($)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Volatility
    ax2.plot(rolling_volatility.index, rolling_volatility.values, color='red', linewidth=1.5)
    ax2.axhline(y=volatility, color='black', linestyle='--', alpha=0.7)
    ax2.set_title("Rolling Volatility", fontweight='bold')
    ax2.set_ylabel("Annualized Volatility")
    ax2.grid(True, alpha=0.3)
    
    # Drawdown
    ax3.fill_between(drawdown.index, drawdown.values * 100, 0, alpha=0.3, color='red')
    ax3.plot(drawdown.index, drawdown.values * 100, color='red', linewidth=1.5)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax3.set_title("Drawdown Analysis", fontweight='bold')
    ax3.set_ylabel("Drawdown (%)")
    ax3.grid(True, alpha=0.3)
    
    # Sharpe ratio
    ax4.plot(rolling_sharpe.index, rolling_sharpe.values, color='green', linewidth=1.5)
    ax4.axhline(y=sharpe_ratio, color='black', linestyle='--', alpha=0.7)
    ax4.axhline(y=0, color='red', linestyle='-', alpha=0.5)
    ax4.set_title("Risk-Adjusted Returns", fontweight='bold')
    ax4.set_ylabel("Sharpe Ratio")
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f"{ticker} Comprehensive Analysis Dashboard", fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    dashboard_path = f"stock_charts/{ticker}_dashboard.png"
    plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Dashboard chart saved as {dashboard_path}")
    result["dashboard_chart_path"] = dashboard_path

    return result