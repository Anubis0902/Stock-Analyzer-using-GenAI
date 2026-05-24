
import os 
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
import yfinance as yf
import requests

load_dotenv()

model = None
base_agent = None
agent_executor = None

@tool
def ddg_search(query: str) -> str:
    """Useful for searching the web for latest news, announcements, and general market events."""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except ImportError:
        return "Error: The 'duckduckgo-search' package is missing in this Python environment. Please run `pip install -U duckduckgo-search` to enable web search."
    except Exception as e:
        return f"Error running search: {str(e)}"



@tool

def get_stock_overview(stock_symbol : str) -> str :
    """  Retrieves a high-level overview of a given stock.

    This tool takes a stock symbol as input and returns essential
    information about the company and its stock, such as current price,
    basic financial details, and general company information. It provides
    a quick snapshot useful for initial analysis.

    Parameters:
        symbol (str): Stock ticker symbol (e.g., "TCS.NS", "AAPL").

    Returns:
        dict: A structured response containing:
              - Company name and sector
              - Current stock price and market cap
              - Basic financial metrics
              - General company information

    Use Case:
        Helps a stock analysis agent quickly understand a companyΓÇÖs profile
        before performing deeper fundamental, technical, or news-based analysis."""
    stock_name = yf.Ticker(stock_symbol)
    result = stock_name.info
    return {
        "name": result.get("longName"),
        "sector": result.get("sector"),
        "industry": result.get("industry"),
        "summary": result.get("longBusinessSummary"),
        "current_price": result.get("currentPrice"),
        "previous_close": result.get("previousClose"),
        "day_high": result.get("dayHigh"),
        "day_low": result.get("dayLow"),
        "market_cap": result.get("marketCap"),
        "52w_high": result.get("fiftyTwoWeekHigh"),
        "52w_low": result.get("fiftyTwoWeekLow"),
        "volume": result.get("volume"),
        "avg_volume": result.get("averageVolume"),
        "recommendation": result.get("recommendationKey"),
        "target_price": result.get("targetMeanPrice")
    }


@tool

def analyze_stock(stock_symbol : str ) -> str:
    """ Performs fundamental and technical analysis of a given stock.

    This tool takes a stock symbol as input and provides key insights
    based on both fundamental data (financial health, valuation metrics)
    and technical indicators (price trends, momentum, patterns). It helps
    in evaluating whether a stock is potentially a good buy, hold, or sell.

    Parameters:
        symbol (str): Stock ticker symbol (e.g., "TCS.NS", "AAPL").

    Returns:
        dict: A structured response containing:
              - Fundamental metrics (PE ratio, market cap, earnings, etc.)
              - Technical indicators (moving averages, RSI, trends, etc.)
              - Overall analysis summary for decision-making

    Use Case:
        Helps a stock analysis agent generate informed investment advice
        by combining financial strength and price movement analysis."""
    stock_name = yf.Ticker(stock_symbol)
    result = stock_name.info 
    hist = stock_name.history(period="3mo")

    close_price = hist["Close"]

    trend = "uptrend" if close_price.iloc[-1] > close_price.mean() else "downtrend"

    return {
        "pe_ratio": result.get("trailingPE"),
        "eps": result.get("trailingEps"),
        "revenue_growth": result.get("revenueGrowth"),
        "profit_margin": result.get("profitMargins"),
        "roe": result.get("returnOnEquity"),
        "debt_to_equity": result.get("debtToEquity"),
        "free_cashflow": result.get("freeCashflow"),
        "recent_prices": close_price.tail(10).tolist(),
        "trend": trend
    }


@tool
def get_news(q: str, searchIn: str = "title", from_date: str = None, to_date: str = None, sortBy: str = "publishedAt", language: str = "en") -> dict:
    """ This tool is designed to support stock analysis by retrieving recent and relevant
    news, which can help in making informed investment decisions. The date range can
    be adjusted dynamically to analyze short-term or long-term news trends.

    Parameters:
        q (str): Search query (e.g., company or stock name like "Infosys", "TCS").
        searchIn (str): Fields to search in (e.g., "title", "description", "content").
        from_date (str): Start date for news (format: "YYYY-MM-DD").
        to_date (str): End date for news (format: "YYYY-MM-DD").
        sortBy (str): Sorting method ("relevancy", "popularity", "publishedAt").
        language (str): Language of news articles (e.g., "en").

    Returns:
        dict: JSON response containing news articles, including title, source,
              publication date, and URL.

    Use Case:
        Helps a stock analysis agent understand market sentiment, recent events,
        and news trends affecting a company before giving investment advice.
    """
    api_key = os.environ.get("NEWS_API")
    if not api_key:
        return {"error": "NEWS_API key is not configured in environment variables."}

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": q,
        "searchIn": searchIn,
        "from": from_date,
        "to": to_date,
        "sortBy": sortBy,
        "language": language,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)
    
    return response.json()


system_prompt="""
You are a highly specialized financial analyst and investment research assistant. Your sole purpose is to provide stock prices, corporate insights, technical trend analysis, and fundamental metrics using your integrated tools.

=== Scope Restrictions (CRITICAL) ===
- You ONLY answer questions related to financial markets, stocks, investing, public companies, macroeconomics, and business news.
- If the user asks an irrelevant question (e.g., general knowledge, math, coding, cooking recipes, creative writing, science, etc.), you MUST politely decline to answer.
- Refusal template: "I specialize strictly in stock market analysis, company evaluations, and investment insights. Please ask a question related to public companies, financial metrics, or stock trends (e.g., 'Analyze TCS fundamentals' or 'Should I buy Nvidia?')."
- Simple greetings (like "hi", "hello") are allowed. Respond politely, and invite the user to ask a financial or stock market question.

=== Rules & Execution Workflow ===
1. **Identify and Map:** Extract the company name or stock mentioned. Map it to the correct Yahoo Finance ticker symbol (always suffix Indian stocks with `.NS` for NSE, e.g., `TCS.NS`, `INFY.NS`).
2. **Retrieve Data:** Fetch price, metrics, news, and technical trends. Always prioritize Yahoo Finance overview and analysis tools over search tools for stock prices.
3. **Analyze:** Evaluate the 3-month moving average trend (uptrend/downtrend) and key financial ratios.
4. **Draft Professional Response:** Structure the report using the premium format below.

=== Response Format (VERY IMPORTANT) ===
Always format your final output as a premium stock research report with the following structure:

# 📊 Stock Report: [Company Name] ([Ticker])

---

### 📈 Stock Summary
- **Current Price:** ₹[price] or $[price]
- **3-Month Trend:** [Use 📈 **Uptrend (Increasing)** or 📉 **Downtrend (Decreasing)** based on moving average]
- **Market Cap:** [market cap]
- **52-Week Range:** [low] - [high]

### 💡 Quick Insight
- *[Provide a concise, 1-2 sentence professional insight explaining what is driving the stock's current price movement or market sentiment.]*

### 📰 Recent News & Sentiment (Only if news tool or search tool was used and returned relevant data)
- *[Headline/Bullet 1]*
- *[Headline/Bullet 2]*

### 🔬 Financial Indicators & Valuation (Only if analysis tool was used)
| Indicator | Value | Meaning & Context |
| :--- | :--- | :--- |
| **P/E Ratio** | [pe] | [Briefly explain if high, low, or reasonable] |
| **EPS** | [eps] | [Briefly explain the earnings per share efficiency] |
| **ROE** | [roe] | [Briefly explain the return on equity performance] |
| **Debt to Equity** | [debt] | [Briefly explain the company's leverage risk] |
| **Free Cash Flow** | [fcf] | [Briefly explain the cash availability] |

### 🎯 Investment Advice & Outlook
- **Recommendation:** [Use one of: 🟢 **BUY** | 🟡 **HOLD** | 🔴 **SELL**]
- **Rationale:** [A solid, easy-to-understand logical reasoning based on the fundamental metrics and technical trends retrieved above.]

> ⚠️ **CRUCIAL FINANCIAL DISCLAIMER:**
> **Do not place trades or make real-world investment decisions based solely on this automated recommendation.** This report is generated by an AI assistant for general educational and informational purposes only. It is not certified financial advice and does not take into account your personal financial situation, risk tolerance, or investment goals.
> 
> All investments involve substantial risk of loss. Before making any investment decisions, you must perform your own independent research, verify all financial metrics, and consult with a certified financial advisor or registered investment broker.

=== Styling Guidelines ===
- Keep spacing consistent and use clean tables.
- Keep bullet points practical and short.
- Never use financial jargon without context.
- Keep the overall style premium and highly readable.
"""

tools = [get_stock_overview, analyze_stock, get_news, ddg_search]

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

class AgentWrapper:
    def __init__(self):
        self._last_api_key = None
        
    def invoke(self, input_dict):
        # Gracefully handle missing GROQ_API_KEY when the chat is run, instead of crashing the import
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Please enter your Groq API Key in the sidebar or add it to a `.env` file.")

        messages = input_dict.get("messages", [])
        if not messages:
            return {"messages": []}
            
        last_msg = messages[-1]
        user_content = last_msg.get("content") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
        
        # Lazy initialization of the agent executor to prevent import-time crashes, with support for live key switching
        global model, base_agent, agent_executor
        if agent_executor is None or self._last_api_key != api_key:
            model = ChatGroq(model='llama-3.3-70b-versatile', groq_api_key=api_key)
            base_agent = create_tool_calling_agent(model, tools, prompt)
            agent_executor = AgentExecutor(agent=base_agent, tools=tools, verbose=True)
            self._last_api_key = api_key
            
        result = agent_executor.invoke({"input": user_content, "chat_history": []})
        output_text = result.get("output", "")
        
        new_messages = []
        for m in messages:
            if isinstance(m, dict):
                role = m.get("role")
                content = m.get("content")
                if role == "user":
                    new_messages.append(HumanMessage(content=content))
                else:
                    new_messages.append(AIMessage(content=content))
            else:
                new_messages.append(m)
                
        new_messages.append(AIMessage(content=output_text))
        return {"messages": new_messages}

agent = AgentWrapper()


if __name__ == '__main__':
    response = agent.invoke({"messages": [{"role": "user", "content": "should i buy wipro , check for some news in past 24 hours related to it also mention it explicitly" }]})
    response


    print(response['messages'][-1].content)








