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

risk_assessor_agent = AssistantAgent(
    name="Risk_Assessor",
    model_client=model_client,
    tools=[google_search_tool],
    description="Specialized in risk assessment and portfolio management",
    system_message="""You are a risk assessment specialist. Your role is to:
    1. Identify potential risks to the investment
    2. Assess market volatility and sector risks
    3. Evaluate company-specific risks
    4. Provide risk mitigation strategies
    5. Calculate risk-adjusted returns
    
    Always consider both upside potential and downside risks.""",
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
    performance_tracker.start_call("Team_Analysis")
    
    try:
        stream = team.run_stream(task="Write a comprehensive financial report on Nvidia including technical analysis, fundamental analysis, news sentiment, and risk assessment")
        await Console(stream)
        performance_tracker.end_call("Team_Analysis", success=True)
        
        # Print performance report
        print("\n" + "="*50)
        print(performance_tracker.get_report())
        print("="*50)
        
    except Exception as e:
        performance_tracker.end_call("Team_Analysis", success=False)
        print(f"Error during analysis: {e}")
    
    finally:
        await model_client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())