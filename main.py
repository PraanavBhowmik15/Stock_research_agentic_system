import autogen
import dotenv
import os
import time
from typing import Dict, List
from dataclasses import dataclass
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from search import google_search
from analyse_stock import analyze_stock

def get_company_info(ticker: str) -> str:
    """
    Get basic company information for a given ticker symbol.
    This helps users verify they have the correct company.
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        
        company_name = info.get('longName', info.get('shortName', 'Unknown Company'))
        sector = info.get('sector', 'Unknown Sector')
        industry = info.get('industry', 'Unknown Industry')
        market_cap = info.get('marketCap', 0)
        
        if market_cap:
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
        else:
            market_cap_str = "Unknown"
        
        return f"Company: {company_name}\nSector: {sector}\nIndustry: {industry}\nMarket Cap: {market_cap_str}"
        
    except Exception as e:
        return f"Could not retrieve company information: {str(e)}"

def validate_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate ticker symbol and return validation result with message.
    """
    if not ticker:
        return False, "❌ Please enter a ticker symbol."
    
    # Remove common suffixes and check if alphanumeric
    clean_ticker = ticker.replace('.', '').replace('-', '').replace('^', '')
    if not clean_ticker.isalnum():
        return False, "❌ Invalid ticker format. Please use only letters and numbers."
    
    # Check length (most tickers are 1-5 characters)
    if len(ticker) > 10:
        return False, "❌ Ticker symbol seems too long. Please check and try again."
    
    return True, "✅ Ticker symbol format is valid."

# Performance tracking
@dataclass
class AgentMetrics:
    name: str
    calls: int = 0
    total_time: float = 0.0
    success_rate: float = 0.0
    last_call: float = 0.0

class AgentPerformanceTracker:
    def __init__(self):
        self.metrics: Dict[str, AgentMetrics] = {}
    
    def start_call(self, agent_name: str):
        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentMetrics(name=agent_name)
        self.metrics[agent_name].calls += 1
        self.metrics[agent_name].last_call = time.time()
    
    def end_call(self, agent_name: str, success: bool = True):
        if agent_name in self.metrics:
            duration = time.time() - self.metrics[agent_name].last_call
            self.metrics[agent_name].total_time += duration
            if success:
                self.metrics[agent_name].success_rate = (
                    (self.metrics[agent_name].success_rate * (self.metrics[agent_name].calls - 1) + 1) 
                    / self.metrics[agent_name].calls
                )
    
    def get_report(self) -> str:
        report = "Agent Performance Report:\n"
        for agent_name, metrics in self.metrics.items():
            avg_time = metrics.total_time / metrics.calls if metrics.calls > 0 else 0
            report += f"\n{agent_name}:\n"
            report += f"  Total calls: {metrics.calls}\n"
            report += f"  Average time: {avg_time:.2f}s\n"
            report += f"  Success rate: {metrics.success_rate:.2%}\n"
        return report

# Initialize tracker
performance_tracker = AgentPerformanceTracker()

conf_list = autogen.config_list_from_dotenv(
    dotenv_file_path=".env",
    model_api_key_map={"gpt-4o": "OPENAI_API_KEY"} 
)

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

google_search_tool = FunctionTool(
    google_search, description="Search Google for information, returns results with a snippet and body content"
)
stock_analysis_tool = FunctionTool(analyze_stock, description="Analyze stock data and generate a plot")

# Enhanced specialized agents with memory and specific roles
technical_analyst_agent = AssistantAgent(
    name="Technical_Analyst",
    model_client=model_client,
    tools=[stock_analysis_tool],
    description="Specialized in technical analysis, chart patterns, and trading indicators",
    system_message="""You are a technical analyst expert. Your role is to:
    1. Analyze stock price patterns and trends
    2. Identify support and resistance levels
    3. Evaluate technical indicators (RSI, MACD, moving averages)
    4. Provide trading signals based on technical analysis
    5. Maintain context of previous analyses for comparison
    
    Always provide specific technical insights with data backing.""",
)

news_researcher_agent = AssistantAgent(
    name="News_Researcher",
    model_client=model_client,
    tools=[google_search_tool],
    description="Specialized in gathering and analyzing financial news and market sentiment",
    system_message="""You are a financial news researcher. Your role is to:
    1. Search for recent news about the target company
    2. Analyze market sentiment from news sources
    3. Identify key events affecting stock performance
    4. Track regulatory changes and industry trends
    5. Provide context for news impact on stock price
    
    Focus on recent, relevant news that could affect stock performance.""",
)

fundamental_analyst_agent = AssistantAgent(
    name="Fundamental_Analyst",
    model_client=model_client,
    tools=[google_search_tool],
    description="Specialized in fundamental analysis, financial ratios, and company valuation",
    system_message="""You are a fundamental analyst expert. Your role is to:
    1. Analyze company financial statements and ratios
    2. Evaluate company valuation metrics (P/E, P/B, ROE)
    3. Assess competitive position and market share
    4. Review earnings reports and growth projections
    5. Provide long-term investment perspective
    
    Focus on fundamental factors that drive long-term value.""",
)

def calculate_risk_score(alpha: float, beta: float, r_squared: float) -> dict:
    """
    Calculate a comprehensive risk score based on Alpha, Beta, and R-Squared metrics.
    
    Args:
        alpha: Alpha value (positive = outperforming benchmark, negative = underperforming)
        beta: Beta value (1 = market volatility, <1 = less volatile, >1 = more volatile)
        r_squared: R-squared value (0-100, higher = more correlated to benchmark)
    
    Returns:
        Dictionary containing risk score and breakdown
    """
    # Risk score calculation (0-100, higher = higher risk)
    risk_score = 0
    
    # Alpha contribution (20% weight)
    if alpha < -0.05:  # Underperforming by more than 5%
        risk_score += 20
    elif alpha < 0:
        risk_score += 10
    elif alpha > 0.05:  # Outperforming by more than 5%
        risk_score += 5
    else:
        risk_score += 8
    
    # Beta contribution (40% weight)
    if beta > 1.5:  # Highly volatile
        risk_score += 40
    elif beta > 1.2:  # More volatile than market
        risk_score += 30
    elif beta > 0.8:  # Around market volatility
        risk_score += 20
    else:  # Less volatile than market
        risk_score += 15
    
    # R-squared contribution (40% weight)
    if r_squared < 30:  # Low correlation to benchmark
        risk_score += 40
    elif r_squared < 50:  # Moderate correlation
        risk_score += 30
    elif r_squared < 70:  # Good correlation
        risk_score += 20
    else:  # High correlation
        risk_score += 15
    
    # Risk level classification
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "overall_risk_score": risk_score,
        "risk_level": risk_level,
        "alpha_contribution": "High risk" if alpha < -0.05 else "Moderate risk" if alpha < 0 else "Low risk",
        "beta_contribution": "High risk" if beta > 1.5 else "Moderate risk" if beta > 1.2 else "Low risk",
        "r_squared_contribution": "High risk" if r_squared < 30 else "Moderate risk" if r_squared < 50 else "Low risk",
        "interpretation": {
            "alpha": f"Alpha of {alpha:.3f} indicates {'outperformance' if alpha > 0 else 'underperformance'} relative to benchmark",
            "beta": f"Beta of {beta:.3f} indicates {'higher' if beta > 1 else 'lower' if beta < 1 else 'market'} volatility",
            "r_squared": f"R-squared of {r_squared:.1f} indicates {'low' if r_squared < 50 else 'moderate' if r_squared < 70 else 'high'} correlation to benchmark"
        }
    }

risk_calculation_tool = FunctionTool(
    calculate_risk_score, 
    description="Calculate comprehensive risk score based on Alpha, Beta, and R-Squared metrics"
)

risk_assessor_agent = AssistantAgent(
    name="Risk_Assessor",
    model_client=model_client,
    tools=[google_search_tool, risk_calculation_tool],
    description="Specialized in risk assessment, portfolio management, and risk scoring",
    system_message="""You are a risk assessment specialist with expertise in quantitative risk metrics. Your role is to:
    1. Calculate comprehensive risk scores using Alpha, Beta, and R-Squared metrics
    2. Identify potential risks to the investment
    3. Assess market volatility and sector risks
    4. Evaluate company-specific risks
    5. Provide risk mitigation strategies
    6. Calculate risk-adjusted returns
    
    When calculating risk scores:
    - Use the calculate_risk_score tool with available Alpha, Beta, and R-Squared data
    - Alpha: Positive values indicate outperformance, negative indicate underperformance
    - Beta: Values >1 indicate higher volatility than market, <1 indicate lower volatility
    - R-Squared: Higher values (closer to 100) indicate stronger correlation to benchmark
    
    Always provide specific risk metrics and actionable risk management recommendations.
    Consider both upside potential and downside risks in your assessment.""",
)

report_synthesizer_agent = AssistantAgent(
    name="Report_Synthesizer",
    model_client=model_client,
    description="Creates comprehensive reports by synthesizing all analyses",
    system_message="""You are a financial report synthesizer. Your role is to:
    1. Combine technical, fundamental, and news analysis
    2. Create comprehensive investment recommendations
    3. Balance different perspectives and timeframes
    4. Provide clear, actionable insights
    5. Include risk assessment in final recommendations
    
    When you complete the comprehensive report, reply with TERMINATE.""",
)

# Enhanced team with specialized agents and performance tracking
team = RoundRobinGroupChat([
    technical_analyst_agent, 
    news_researcher_agent, 
    fundamental_analyst_agent,
    risk_assessor_agent,
    report_synthesizer_agent
], max_turns=5)

async def main():
    # Get user input for stock ticker
    print("="*60)
    print("🚀 STOCK RESEARCH ANALYSIS SYSTEM")
    print("="*60)
    print("💡 Type 'help' for available commands or 'quit' to exit")
    print("📚 This system analyzes stocks using AI agents for:")
    print("   • Technical Analysis (charts, patterns, indicators)")
    print("   • Fundamental Analysis (financial ratios, valuation)")
    print("   • News Sentiment Analysis (market sentiment, events)")
    print("   • Risk Assessment (volatility, drawdown, Sharpe ratio)")
    print("   • Comprehensive Investment Recommendations")
    print("="*60)
    
    while True:
        try:
            # Get stock ticker from user
            ticker = input("\n📈 Enter stock ticker symbol (e.g., AAPL, MSFT, GOOGL) or 'quit' to exit: ").strip().upper()
            
            if ticker.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using the Stock Research Analysis System!")
                break
            
            if ticker.lower() in ['help', 'h', '?']:
                print("\n" + "="*60)
                print("📚 HELP MENU")
                print("="*60)
                print("📈 COMMANDS:")
                print("   • Enter any stock ticker (e.g., AAPL, MSFT, GOOGL)")
                print("   • 'help' or 'h' - Show this help menu")
                print("   • 'quit' or 'q' - Exit the program")
                print("\n📊 ANALYSIS INCLUDES:")
                print("   • Technical Analysis: Price patterns, moving averages, volatility")
                print("   • Fundamental Analysis: Financial ratios, company valuation")
                print("   • News Analysis: Market sentiment, recent events")
                print("   • Risk Assessment: Alpha, Beta, R-squared, Sharpe ratio")
                print("   • Charts: Stock price, volatility, drawdown, risk-adjusted returns")
                print("\n💡 TIPS:")
                print("   • Use standard ticker symbols (e.g., AAPL not Apple Inc.)")
                print("   • Analysis may take 2-5 minutes depending on complexity")
                print("   • All charts are saved in the 'stock_charts' folder")
                print("="*60)
                continue
            
            # Validate ticker format
            is_valid, validation_msg = validate_ticker(ticker)
            if not is_valid:
                print(validation_msg)
                continue
            
            # Show company information for confirmation
            print(f"\n🔍 Verifying ticker symbol: {ticker}")
            company_info = get_company_info(ticker)
            print(f"\n📋 Company Information:")
            print(company_info)
            
            # Ask user to confirm
            confirm = input(f"\n✅ Is this the company you want to analyze? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes', 'yeah', 'sure', '']:
                print("🔄 Please enter the correct ticker symbol.")
                continue
            
            print(f"\n🔍 Starting comprehensive analysis of {ticker}...")
            print("🤖 AI Agents are now working:")
            print("   📊 Technical Analyst: Analyzing price patterns and indicators")
            print("   📰 News Researcher: Gathering market sentiment and events")
            print("   💰 Fundamental Analyst: Evaluating financial metrics")
            print("   ⚠️  Risk Assessor: Calculating risk scores and metrics")
            print("   📋 Report Synthesizer: Creating comprehensive recommendations")
            print("\n⏳ Analysis in progress... This may take 2-5 minutes...")
            
            # Start performance tracking
            performance_tracker.start_call("Team_Analysis")
            
            try:
                # Create dynamic task with user's ticker
                task = f"Write a comprehensive financial report on {ticker} including technical analysis, fundamental analysis, news sentiment, and risk assessment"
                
                stream = team.run_stream(task=task)
                await Console(stream)
                performance_tracker.end_call("Team_Analysis", success=True)
                
                # Print performance report
                print("\n" + "="*50)
                print("📊 PERFORMANCE REPORT")
                print("="*50)
                print(performance_tracker.get_report())
                print("="*50)
                
                # Ask if user wants to analyze another stock
                another = input(f"\n🔍 Would you like to analyze another stock? (y/n): ").strip().lower()
                if another not in ['y', 'yes', 'yeah', 'sure']:
                    print("\n👋 Thank you for using the Stock Research Analysis System!")
                    break
                    
            except Exception as e:
                performance_tracker.end_call("Team_Analysis", success=False)
                print(f"\n❌ Error during analysis of {ticker}: {e}")
                print("💡 Please check if the ticker symbol is correct and try again.")
                
                # Ask if user wants to try another stock
                retry = input(f"\n🔄 Would you like to try another stock? (y/n): ").strip().lower()
                if retry not in ['y', 'yes', 'yeah', 'sure']:
                    print("\n👋 Thank you for using the Stock Research Analysis System!")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n👋 Analysis interrupted. Thank you for using the Stock Research Analysis System!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("💡 Please try again or contact support if the issue persists.")
    
    # Close the model client
    await model_client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())