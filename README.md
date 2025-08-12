# Stock Research Project

A comprehensive stock analysis tool that leverages AI agents to provide detailed financial analysis, technical insights, and investment recommendations.

## 🚀 Features

### Multi-Agent Analysis System
- **Technical Analyst Agent**: Specializes in technical analysis, chart patterns, and trading indicators
- **News Researcher Agent**: Gathers and analyzes financial news and market sentiment
- **Fundamental Analyst Agent**: Analyzes financial statements, ratios, and company valuation
- **Risk Assessor Agent**: Evaluates investment risks and provides mitigation strategies
- **Report Synthesizer Agent**: Combines all analyses into comprehensive investment reports

### Stock Analysis Capabilities
- Real-time stock data retrieval using Yahoo Finance API
- Technical indicators (50-day and 200-day moving averages)
- Price trend analysis and volatility calculations
- YTD performance metrics
- Interactive stock price charts with moving averages

### Research Tools
- Google Custom Search integration for financial news
- Web scraping for detailed content analysis
- Performance tracking and metrics for all agents

## 📁 Project Structure

```
Stock_research/
├── main.py                 # Main application with multi-agent system
├── analyse_stock.py        # Stock data analysis and chart generation
├── search.py              # Google search and web scraping functionality
├── financial_report/      # Financial report templates
├── reports/               # Generated financial reports (PDF)
├── stock_charts/          # Stock price charts and visualizations
└── README.md              # This file
```

## 🛠️ Prerequisites

- Python 3.8+
- OpenAI API key
- Google Custom Search API key and Search Engine ID
- Required Python packages (see Installation section)

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Stock_research
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root with:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
   ```

## 🔧 Dependencies

The project requires the following Python packages:
- `autogen` - Multi-agent conversation framework
- `yfinance` - Yahoo Finance data access
- `matplotlib` - Chart generation
- `pandas` - Data manipulation
- `numpy` - Numerical computations
- `requests` - HTTP requests
- `beautifulsoup4` - Web scraping
- `python-dotenv` - Environment variable management

## 🚀 Usage

### Running the Main Application

```bash
python main.py
```

This will start the multi-agent analysis system and generate a comprehensive financial report for Nvidia (NVDA).

### Individual Stock Analysis

```python
from analyse_stock import analyze_stock

# Analyze a specific stock
result = analyze_stock("AAPL")
print(result)
```

### Web Search Functionality

```python
from search import google_search

# Search for financial information
results = google_search("Apple earnings report 2024", num_results=3)
print(results)
```

## 📊 Output

### Generated Reports
- **Financial Reports**: Comprehensive PDF reports stored in the `reports/` directory
- **Stock Charts**: Interactive price charts saved as PNG files in `stock_charts/`
- **Performance Metrics**: Agent performance tracking and analysis reports

### Sample Output Structure
```json
{
  "ticker": "NVDA",
  "current_price": 450.25,
  "52_week_high": 500.00,
  "52_week_low": 200.50,
  "50_day_ma": 425.30,
  "200_day_ma": 380.15,
  "ytd_price_change": 150.75,
  "ytd_percent_change": 50.25,
  "trend": "Upward",
  "volatility": 0.35,
  "plot_file_path": "stock_charts/NVDA_stockprice.png"
}
```

## 🔍 API Configuration

### OpenAI API
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Add to your `.env` file

### Google Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Custom Search API
3. Create credentials (API key)
4. Set up Custom Search Engine at [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
5. Add both to your `.env` file

## 📈 Features in Detail

### Technical Analysis
- Moving average calculations (50-day, 200-day)
- Trend identification and analysis
- Volatility calculations
- Support and resistance level identification

### Fundamental Analysis
- Financial ratio analysis
- Company valuation metrics
- Earnings report analysis
- Growth projections

### Risk Assessment
- Market volatility analysis
- Sector-specific risks
- Company-specific risk factors
- Risk-adjusted return calculations

### News Sentiment Analysis
- Recent financial news gathering
- Market sentiment evaluation
- Regulatory change tracking
- Industry trend analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It should not be considered as financial advice. Always consult with qualified financial professionals before making investment decisions.

## 🆘 Support

If you encounter any issues or have questions:
1. Check the existing issues in the repository
2. Create a new issue with detailed information
3. Include error messages and system information

## 🔮 Future Enhancements

- [ ] Additional technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Portfolio analysis and optimization
- [ ] Real-time market data streaming
- [ ] Machine learning-based price prediction models
- [ ] Integration with additional financial data sources
- [ ] Web-based user interface
- [ ] Mobile application support

---

**Note**: Make sure to keep your API keys secure and never commit them to version control. The `.env` file is already included in `.gitignore` for security.
