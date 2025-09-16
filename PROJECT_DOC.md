## Stock Research Analysis System — Project Documentation

A concise, two-page guide to understand, configure, run, and extend this project. This system uses coordinated AI agents to analyze a stock from multiple angles (technical, fundamental, news, and risk) and produces insights plus charts.

### 1) What This Project Does

- **Multi‑agent analysis**: Orchestrates specialized agents to research a ticker.
- **Data sources**: Yahoo Finance (via `yfinance`) and Google Programmable Search.
- **Outputs**: Console report plus saved charts for price, volatility, drawdown, and Sharpe ratio in `stock_charts/`. Optional PDFs under `reports/`.

### 2) High-Level Architecture

- **Entry point**: `main.py` prompts for a ticker and coordinates the run.
- **Agents** (from `autogen` ecosystem):
  - **Technical_Analyst**: Calls `analyze_stock` to compute indicators and generate charts.
  - **News_Researcher**: Uses Google Custom Search to fetch recent news and snippets.
  - **Fundamental_Analyst**: Uses search to reason about fundamentals/valuation.
  - **Risk_Assessor**: Invokes a risk scoring tool (Alpha, Beta, R-squared inputs) and provides risk guidance.
  - **Report_Synthesizer**: Combines all perspectives into a final recommendation.
- **Team orchestration**: `RoundRobinGroupChat` runs agents in sequence for up to 5 turns.
- **Tools**:
  - `analyze_stock(ticker)` in `analyse_stock.py`: fetches history, computes metrics, and saves charts.
  - `google_search(query)` in `search.py`: Google Custom Search + page text snippet.
  - `calculate_risk_score(alpha, beta, r_squared)` in `main.py`.

Data flow overview:
1. User provides ticker in `main.py` → ticker validated → company info fetched via `yfinance`.
2. Team task created (comprehensive report for ticker).
3. Agents run round‑robin; tools called as needed.
4. Console streams agent outputs; charts saved to `stock_charts/`; performance metrics printed.

### 3) Repository Structure

```
Stock_research/
├─ main.py                 # Multi-agent orchestration, CLI, performance metrics
├─ analyse_stock.py        # Price history, indicators, volatility, drawdown, Sharpe, charts
├─ search.py               # Google Custom Search + lightweight page text capture
├─ financial_report/       # (Optional) Templates or assets for reports
├─ reports/                # Example/generated PDFs
├─ stock_charts/           # Saved PNG charts per ticker
└─ README.md               # Quick overview
```

### 4) Requirements

- **Python**: 3.8+
- **API keys**:
  - `OPENAI_API_KEY` (for agent reasoning via OpenAI model)
  - `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` (for news search)
- **Python packages** (typical): `autogen`, `autogen-agentchat`, `autogen-ext`, `openai`, `yfinance`, `pandas`, `numpy`, `matplotlib`, `requests`, `beautifulsoup4`, `python-dotenv`, `pytz`.

If you don’t have a `requirements.txt`, install with:

```bash
pip install autogen autogen-agentchat autogen-ext openai yfinance pandas numpy matplotlib requests beautifulsoup4 python-dotenv pytz
```

### 5) Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_google_cx_id
```

- Ensure your Google Programmable Search Engine is configured to search the web and not restricted to only specific sites (unless intended).
- The code looks for `.env` in the project root. Keep keys private.

### 6) Running the App (Windows PowerShell)

```powershell
cd C:\Users\<you>\Documents\Ambivo_internship\Stock_research
python .\main.py
```

What you’ll see:
- A CLI with help, input prompt for ticker (e.g., `AAPL`, `MSFT`), and a verification step showing company info.
- Progress messages as agents work, followed by a performance report.
- Charts saved to `stock_charts/` like `AAPL_stockprice.png`, `AAPL_volatility.png`, `AAPL_drawdown.png`, `AAPL_sharpe_ratio.png`, and `AAPL_dashboard.png`.

### 7) Core Components and Logic

- `validate_ticker(ticker)` in `main.py`: basic format checks.
- `get_company_info(ticker)` in `main.py`: uses `yfinance.Ticker.info` to show name, sector, industry, market cap.
- `analyse_stock.py`:
  - Downloads ~1000 days of OHLC history.
  - Computes 50/200‑day moving averages, trend detection, annualized volatility, YTD performance.
  - Computes drawdown series and Sharpe ratio (with 2% annual risk‑free assumption).
  - Saves five charts (price+MAs, rolling volatility, drawdown, rolling Sharpe, 2×2 dashboard).
- `search.py`:
  - Hits Google Custom Search JSON API; for each item, also fetches the page HTML and extracts text (trimmed to `max_chars`).
- `calculate_risk_score` (tool in `main.py`): simple heuristic combining Alpha, Beta, and R‑squared into an overall risk bucket.
- `RoundRobinGroupChat`: runs agents in order for up to 5 turns; `Console(stream)` streams outputs to terminal.

### 8) Outputs

- **Charts** (PNG): Saved under `stock_charts/` per ticker.
- **Console report**: Agent messages culminating in a synthesized recommendation.
- **Performance report**: Call counts, average time, and simple success rate per agent/team.
- **PDFs** (optional): Example PDFs under `reports/` folder.

### 9) Customization Tips

- Change the model or parameters: In `main.py`, update `OpenAIChatCompletionClient(model=...)` or `.env` keys.
- Add indicators: Extend `analyse_stock.py` (e.g., RSI, MACD) and plot in the dashboard.
- Modify agent behavior: Edit each `system_message` in `main.py` to adjust role, focus, or style.
- Adjust search depth: In `search.py`, change `num_results` default or `max_chars` for page text.
- Risk model: Replace `calculate_risk_score` with your own scoring, weights, or thresholds.

### 10) Troubleshooting

- “API key or Search Engine ID not found” (from `search.py`):
  - Ensure `.env` contains `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` and that `python-dotenv` is installed.
  - Verify billing/quotas and that the Custom Search API is enabled in Google Cloud.
- OpenAI errors:
  - Confirm `OPENAI_API_KEY` is valid and environment can reach `api.openai.com`.
  - If you hit model access errors, choose a model your key can access or update config.
- Empty or missing price history:
  - Some tickers or newly listed symbols may not return data; try a different ticker or larger date range.
  - Network or rate‑limit issues with Yahoo Finance can cause empty frames; retry later.
- Charts not appearing:
  - Check write permissions for `stock_charts/`.
  - Ensure `matplotlib` backend works in your environment (headless saving is used via `savefig`).

### 11) Security & Good Practices

- Never commit `.env` with real keys. Add it to `.gitignore`.
- Consider setting environment vars via your shell/CI instead of files for deployment.
- Rate‑limit friendly: `search.py` sleeps between page fetches; keep respectful delays.

### 12) Roadmap Ideas

- Add RSI, MACD, Bollinger Bands, and volume‑based signals.
- Company fundamentals ingestion (10‑K/10‑Q) with ratio calculation and trend tables.
- Portfolio module (position sizing, diversification, risk parity).
- Web UI with interactive charts and saved analyses.
- Live data streaming and alerting.

### 13) Quick FAQ

- **Q: Which tickers work?**
  - Most common US tickers (AAPL, MSFT, GOOGL, NVDA, TSLA, etc.). For others, ensure Yahoo Finance provides data.
- **Q: Where are the results saved?**
  - Charts in `stock_charts/`; any sample PDFs in `reports/`; console shows the narrative report.
- **Q: How long does it take?**
  - Typically 2–5 minutes depending on network, API responses, and plotting time.


