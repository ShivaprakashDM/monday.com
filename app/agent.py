import os
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

import monday_client
from normalize import process_deals, process_work_orders, load_config
from analytics import calculate_pipeline_value, calculate_sector_revenue, find_execution_gaps

# Define the global configuration for the tools to use
# In a real app, we'd pass this via context vars or dependency injection, but simple globals work for this prototype.
config = load_config()

# Global state for tracing actions in Streamlit
action_traces = []

def log_action(action: str):
    """Logs an action to the global trace list so Streamlit can display it."""
    action_traces.append(action)
    print(f"Agent Action: {action}")

@tool
def fetch_and_analyze_deals(time_period: str = "all") -> Dict[str, Any]:
    """
    Fetches the live Deals board from Monday.com, cleans the data, 
    and returns key pipeline metrics (Total Value, Sector Revenue Breakdown).
    Use this when the user asks about pipeline, deals, revenue, or sales performance.
    
    Args:
        time_period: not implemented yet, just pass "all"
    """
    log_action("Calling Monday.com API: Fetching Deals Board...")
    
    try:
        # Check if we have API Keys
        board_id = os.getenv("DEALS_BOARD_ID", config['boards']['deals'].get('default_id'))
        api_key = os.getenv("MONDAY_API_KEY")
        
        if not api_key:
            log_action("API Key missing. Falling back to local Deals Excel file.")
            df = monday_client.load_from_excel_fallback("Deal funnel Data.xlsx")
        else:
            client = monday_client.MondayClient(api_key)
            df = client.fetch_board_items(board_id)
            
        log_action("Normalizing Deals Data (Handling missing values, currency parsing, sector standardizing)...")
        cleaned_df, qa_notes = process_deals(df, config)
        
        log_action("Running Analytics: Calculating Pipeline and Sector Revenue...")
        total_pipeline = calculate_pipeline_value(cleaned_df)
        sector_revenue = calculate_sector_revenue(cleaned_df)
        
        return {
            "Total Open Pipeline ($)": total_pipeline,
            "Sector Breakdown": sector_revenue,
            "Total Deals Analysed": len(cleaned_df),
            "Data Quality Notes": qa_notes
        }
        
    except Exception as e:
        log_action(f"Error fetching Deals: {str(e)}")
        return {"error": str(e)}

@tool
def fetch_and_analyze_work_orders() -> Dict[str, Any]:
    """
    Fetches the live Work Orders board, cleans it, and returns execution metrics.
    Use this when asked about work order status, execution, delayed projects, or billing.
    """
    log_action("Calling Monday.com API: Fetching Work Orders Board...")
    
    try:
        board_id = os.getenv("WORK_ORDERS_BOARD_ID", config['boards']['work_orders'].get('default_id'))
        api_key = os.getenv("MONDAY_API_KEY")
        
        if not api_key:
            log_action("API Key missing. Falling back to local Work Orders Excel file.")
            df = monday_client.load_from_excel_fallback("Work_Order_Tracker Data.xlsx")
        else:
            client = monday_client.MondayClient(api_key)
            df = client.fetch_board_items(board_id)
            
        log_action("Normalizing Work Orders Data (Financials, Statuses)...")
        cleaned_df, qa_notes = process_work_orders(df, config)
        
        wo_status_col = 'execution_status'
        if wo_status_col in cleaned_df.columns:
            status_counts = cleaned_df[wo_status_col].value_counts().to_dict()
        else:
            status_counts = {"Unknown": len(cleaned_df)}
            
        # Total Billed
        if 'Normalized_Billed_Value' in cleaned_df.columns:
            total_billed = cleaned_df['Normalized_Billed_Value'].sum()
        else:
            total_billed = 0
            
        return {
            "Total Work Orders": len(cleaned_df),
            "Status Breakdown": status_counts,
            "Total Billed Value ($)": total_billed,
            "Data Quality Notes": qa_notes
        }
        
    except Exception as e:
        log_action(f"Error fetching Work Orders: {str(e)}")
        return {"error": str(e)}

@tool
def fetch_execution_gaps() -> Dict[str, Any]:
    """
    Cross-board analysis: Fetches BOTH Deals and Work Orders to find Closed-Won Deals 
    that either have no Work Order created, or the Work Order is 'Not Started'.
    Use this when asked about execution gaps, stuck deals, or handoff issues.
    """
    log_action("Cross-Board Query Initiated: Fetching Deals AND Work Orders...")
    
    deals_data = fetch_and_analyze_deals.invoke({"time_period": "all"})
    wo_data = fetch_and_analyze_work_orders.invoke({})
    
    # Actually perform the pandas join
    try:
        api_key = os.getenv("MONDAY_API_KEY")
        if not api_key:
            d_df = monday_client.load_from_excel_fallback("Deal funnel Data.xlsx")
            w_df = monday_client.load_from_excel_fallback("Work_Order_Tracker Data.xlsx")
        else:
            d_board = os.getenv("DEALS_BOARD_ID")
            w_board = os.getenv("WORK_ORDERS_BOARD_ID")
            client = monday_client.MondayClient(api_key)
            d_df = client.fetch_board_items(d_board)
            w_df = client.fetch_board_items(w_board)
            
        d_clean, _ = process_deals(d_df, config)
        w_clean, _ = process_work_orders(w_df, config)
        
        log_action("Joining Deals and Work Orders on Deal Name...")
        gaps = find_execution_gaps(d_clean, w_clean, config['boards']['deals']['columns'], config['boards']['work_orders']['columns'])
        
        return {
            "Total Execution Gaps Found": len(gaps),
            "Gaps Detail": gaps,
            "Note": "Execution gaps refer to deals marked as closed-won without a corresponding active work order."
        }
        
    except Exception as e:
        log_action(f"Error during cross-board analysis: {str(e)}")
        return {"error": str(e)}

# Initialize the LLM
def get_agent():
    api_key = os.getenv("GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, api_key=api_key)
    
    # Bind tools to the LLM
    tools = [fetch_and_analyze_deals, fetch_and_analyze_work_orders, fetch_execution_gaps]
    llm_with_tools = llm.bind_tools(tools)
    
    return llm_with_tools, tools

def run_agent_query(query: str, chat_history: List[Any] = None) -> str:
    """
    Main entry point for Streamlit to pass a query to the Langchain Agent.
    """
    # Reset traces for this run
    global action_traces
    action_traces = []
    
    if chat_history is None:
        chat_history = []
        
    system_prompt = SystemMessage(content='''You are an AI Business Intelligence Agent for startup founders.
    Your job is to answer business questions by analyzing data from monday.com boards (Deals and Work Orders).
    
    RULES:
    - ALWAYS use the provided tools to fetch live data to answer the query. Do not make up numbers.
    - Data may contain inconsistencies. The tools handle cleaning, but pay attention to the "Data Quality Notes" returned.
    
    OUTPUT FORMAT REQUIREMENTS:
    You MUST output your final answer strictly in the following format (use markdown headers):
    
    ### Insight Summary
    [A brief, 1-2 sentence executive summary of the answer]
    
    ### Key Metrics
    [Bullet points of the top-level numbers pulled from the data]
    
    ### Sector Performance
    [Breakdown of the relevant metrics by sector, if applicable. If not, say "N/A for this query"]
    
    ### Pipeline Health / Execution Status
    [Commentary on stuck deals, execution gaps, or general health based on the data]
    
    ### Data Quality Notes
    [List any caveats, missing data, or normalizations performed during this analysis. Use the QA notes returned by the tools.]
    ''')
    
    messages = [system_prompt] + chat_history + [HumanMessage(content=query)]
    
    llm_with_tools, tools = get_agent()
    
    # Manual tool-calling loop (ReAct style)
    while True:
        log_action("LLM is reasoning...")
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if not response.tool_calls:
            # LLM is done, return the final text
            log_action("LLM finished generating Insight Report.")
            
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from list of blocks
                text_parts = []
                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                return "\n".join(text_parts) if text_parts else str(content)
            else:
                return str(content)
            
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the actual tool function
            tool_func = next((t for t in tools if t.name == tool_name), None)
            if tool_func:
                log_action(f"Agent Action: Executing Tool `{tool_name}` with args: {tool_args}")
                tool_output = tool_func.invoke(tool_args)
                
                # Append the tool message to history so the LLM can read it
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(tool_output),
                    name=tool_name,
                    tool_call_id=tool_call["id"]
                ))
