# Monday.com Founder BI Agent (Gemini Powered)

This is an AI Business Intelligence Agent built for founders. It answers natural language questions about your business by fetching live data from Monday.com boards (Deals and Work Orders), cleaning and normalizing the data, and offering actionable insights using Google's Gemini 2.5 Flash model via LangChain.

## Features
- **Live Monday.com Integration:** Connects directly to Monday.com via API. No caching.
- **Data Resilience:** Built-in Pandas logic cleans dirty financial fields, unifies sectors, and handles missing execution dates before passing data to the LLM.
- **Cross-Board Analytics:** Automatically merges Deals and Work Orders to discover execution gaps (e.g. deals won, but projects not started).
- **Agent Action Trace:** See exactly what API calls the agent is making and what cleaning steps it takes directly in the UI.

## Local Setup: Step-By-Step

**Step 1. Configure your `.env` File**
In the root directory of your project (same folder as `streamlit_app.py`), you must have a `.env` file containing your API credentials and Board IDs. 

Your `.env` file should look exactly like this:
```
MONDAY_API_KEY=Your_Monday_API_Key
GEMINI_API_KEY=Your_GEMINI_API_KEY
OPENAI_API_KEY=optional
DEALS_BOARD_ID=Your_DEALS_BOARD_ID
WORK_ORDERS_BOARD_ID=your_WORK_ORDERS_BOARD_ID

```

**Step 2. Install Dependencies**
Open your terminal, navigate to the project directory, and install the required Python packages:
```bash
pip install -r requirements.txt
pip install langchain-google-genai
```

**Step 3. Run the Streamlit App**
Run the following command in your terminal to start the UI:
```bash
streamlit run streamlit_app.py
```

**Step 4. Open in Browser**
Streamlit will automatically open a tab in your browser (usually `http://localhost:8501`). 
1. Check the left sidebar to ensure your configuration is loaded.
2. If the API keys are missing in the sidebar, paste them in and click "Save Configuration".
3. Ask the Agent a question in the chat box at the bottom! Example: *"How is our pipeline looking this quarter?"*

## Architecture Overview
- **`streamlit_app.py`:** The main frontend interface.
- **`app/agent.py`:** Holds the ReAct Langchain logic connecting Gemini to your Data tools.
- **`app/monday_client.py`:** Handles API calls and GraphQL queries to Monday.com.
- **`app/normalize.py`:** Pandas scripts that clean missing data, parse currency, and standardize columns.
- **`app/analytics.py`:** Core functions to calculate pipeline metrics and execution cross-board gaps.

## Deployment Notes
This app is ready to be hosted on Streamlit Community Cloud. Simply connect your GitHub repository, define the API keys in your Streamlit Secrets interface, and point the main file to `streamlit_app.py`.

## Built With
- Python 3
- Streamlit
- LangChain / Google GenAI (Gemini)
- Pandas
- Pandas
