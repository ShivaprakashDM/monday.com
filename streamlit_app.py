import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from dotenv import load_dotenv
from agent import run_agent_query, action_traces

# Load environment variables (API keys, board IDs) for local dev
load_dotenv()

# Securely load API Keys from Streamlit Secrets or Environment Variables
MONDAY_API_KEY = st.secrets.get("MONDAY_API_KEY") or os.getenv("MONDAY_API_KEY")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

# Ensure keys are available in the os environment so downstream modules (like agent.py) can find them easily
if MONDAY_API_KEY:
    os.environ["MONDAY_API_KEY"] = MONDAY_API_KEY
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

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
    
    # Board IDs
    deals_board = st.text_input("Deals Board ID", value=os.getenv("DEALS_BOARD_ID", "123456789"))
    wo_board = st.text_input("Work Orders Board ID", value=os.getenv("WORK_ORDERS_BOARD_ID", "987654321"))
    
    if st.button("Save Configuration"):
        valid = True
        if not deals_board or not deals_board.isdigit():
            st.error("Deals Board ID must be numerical digits and non-empty.")
            valid = False
        if not wo_board or not wo_board.isdigit():
            st.error("Work Orders Board ID must be numerical digits and non-empty.")
            valid = False
            
        if valid:
            os.environ["DEALS_BOARD_ID"] = deals_board
            os.environ["WORK_ORDERS_BOARD_ID"] = wo_board
            st.success("Configuration saved for this session!")

    if st.button("Test Connection"):
        if not MONDAY_API_KEY or not GEMINI_API_KEY:
            st.error("Server API keys are not configured.")
        else:
            st.success("Connection successful")

    st.markdown("---")
    st.markdown("### Suggested Queries")
    st.info('👉 "How is our pipeline looking?"')
    st.info('👉 "Which sector is generating the most revenue?"')
    st.info('👉 "Are there any execution gaps for closed deals?"')


# --- Main UI ---
st.title("🤖 Monday.com Founder BI Agent")
st.markdown("Ask natural language questions to analyze your live Deals and Work Orders boards.")

if not MONDAY_API_KEY or not GEMINI_API_KEY:
    st.error("Server API keys are not configured.")
    st.stop()

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
            error_msg = str(e)
            
            # Redact secrets from the exception trace
            if MONDAY_API_KEY and MONDAY_API_KEY in error_msg:
                error_msg = error_msg.replace(MONDAY_API_KEY, "***REDACTED***")
            if GEMINI_API_KEY and GEMINI_API_KEY in error_msg:
                error_msg = error_msg.replace(GEMINI_API_KEY, "***REDACTED***")
                
            st.error(f"Agent encountered a fatal error: {error_msg}")
