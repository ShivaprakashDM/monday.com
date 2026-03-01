import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from dotenv import load_dotenv
from agent import run_agent_query, action_traces

# Load environment variables (API keys, board IDs)
load_dotenv()

st.set_page_config(
    page_title="Monday.com BI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App State
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar Configuration ---
with st.sidebar:
    st.title("⚙️ Agent Settings")
    st.markdown("Configure your live API connection below.")
    
    # API Keys
    api_key = st.text_input("Monday.com API Key", value=os.getenv("MONDAY_API_KEY", ""), type="password")
    openai_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    
    st.markdown("---")
    
    # Board IDs
    deals_board = st.text_input("Deals Board ID", value=os.getenv("DEALS_BOARD_ID", "123456789"))
    wo_board = st.text_input("Work Orders Board ID", value=os.getenv("WORK_ORDERS_BOARD_ID", "987654321"))
    
    if st.button("Save Configuration"):
        if api_key: os.environ["MONDAY_API_KEY"] = api_key
        if openai_key: os.environ["GEMINI_API_KEY"] = openai_key
        if deals_board: os.environ["DEALS_BOARD_ID"] = deals_board
        if wo_board: os.environ["WORK_ORDERS_BOARD_ID"] = wo_board
        st.success("Configuration saved for this session!")

    st.markdown("---")
    st.markdown("### Suggested Queries")
    st.info('👉 "How is our pipeline looking?"')
    st.info('👉 "Which sector is generating the most revenue?"')
    st.info('👉 "Are there any execution gaps for closed deals?"')


# --- Main UI ---
st.title("🤖 Monday.com Founder BI Agent")
st.markdown("Ask natural language questions to analyze your live Deals and Work Orders boards.")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display the trace if it exists for this assistant response
        if "trace" in msg and msg["trace"]:
            with st.expander("🛠️ View Agent Action Trace", expanded=False):
                for t in msg["trace"]:
                    st.code(t, language="bash")

# Capture User Input
if prompt := st.chat_input("E.g., Which deals are stuck in execution?"):
    
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    if not os.getenv("GEMINI_API_KEY"):
        st.error("Please provide a Gemini API Key in the sidebar to run the agent.")
        st.stop()

    # Agent Processing
    with st.chat_message("assistant"):
        st.markdown("*(Agent is thinking...)*")
        
        try:
            # We don't pass full langchain history here to simplify the prototype, 
            # just the new query. (Could be expanded to pass previous messages).
            response = run_agent_query(prompt)
            
            # Save message and trace history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "trace": action_traces.copy() # Copy the global trace
            })
            
            # Immediately re-render to clear the "thinking" message and show final response properly
            st.rerun()
            
        except Exception as e:
            st.error(f"Agent encountered a fatal error: {str(e)}")
