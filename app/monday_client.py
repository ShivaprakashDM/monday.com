import os
import requests
import pandas as pd
from typing import Dict, Any, Optional
import json

class MondayClient:
    def __init__(self, api_key: str = None):
        """
        Initialize the Monday.com API client.
        Uses the provided API key or falls back to the MONDAY_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("MONDAY_API_KEY")
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the Monday.com API.
        """
        if not self.api_key:
            raise ValueError("Monday.com API key is missing. Please set MONDAY_API_KEY.")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30 
            )
            response.raise_for_status() 
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"Monday API Error: {json.dumps(data['errors'])}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Monday.com API: {str(e)}")

    def fetch_board_metadata(self, board_id: str) -> Dict[str, str]:
        """
        Fetches the column titles and IDs for a given board.
        Returns a dictionary mapping column_id to title.
        """
        query = """
        query ($boardId: [ID!]) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        variables = {"boardId": [board_id]}
        data = self._execute_query(query, variables)
        
        try:
            columns = data["data"]["boards"][0]["columns"]
            return {col["id"]: col["title"] for col in columns}
        except (KeyError, IndexError):
            raise Exception(f"Could not fetch metadata for board {board_id}. Ensure the ID is numeric and correct.")

    def fetch_board_items(self, board_id: str, limit: int = 500) -> pd.DataFrame:
        """
        Fetches all items from a board, including their column values.
        Handles basic pagination using a limit. Returns a pandas DataFrame.
        """
        # First, let's get the column mappings
        col_mappings = self.fetch_board_metadata(board_id)
        
        query = """
        query ($boardId: [ID!], $limit: Int!) {
            boards(ids: $boardId) {
                items_page(limit: $limit) {
                    cursor
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": [board_id], "limit": limit}
        data = self._execute_query(query, variables)
        
        try:
            items = data["data"]["boards"][0]["items_page"]["items"]
            
            # Format the data into a list of dictionaries for pandas
            formatted_data = []
            for item in items:
                row = {
                    "Item ID": item["id"],
                    "Name": item["name"] # The default first column
                }
                
                # Add all other columns, mapping from their ID to their human-readable Title
                for col_val in item.get("column_values", []):
                    col_id = col_val["id"]
                    # text contains the human readable text for most column types
                    col_text = col_val.get("text", "") 
                    
                    # If text is empty but value exists (like sometimes with numbers), parse the value (which is a JSON string)
                    if not col_text and col_val.get("value"):
                        try:
                            val_json = json.loads(col_val["value"])
                            if isinstance(val_json, dict) and "numeric_value" in val_json:
                                col_text = val_json.get("numeric_value", "")
                        except:
                            pass
                            
                    title = col_mappings.get(col_id, col_id)
                    row[title] = col_text
                    
                formatted_data.append(row)
                
            return pd.DataFrame(formatted_data)
            
        except (KeyError, IndexError) as e:
            raise Exception(f"Could not parse items for board {board_id}. Structure mismatch. {str(e)}")


def load_from_excel_fallback(file_path: str) -> pd.DataFrame:
    """
    Fallback method to load data from the local Excel files provided in the assignment
    if the live API keys are not provided or the boards haven't been created yet.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at {file_path}. Cannot use fallback.")
    return pd.read_excel(file_path)

