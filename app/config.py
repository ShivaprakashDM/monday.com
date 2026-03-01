# app/config.py
from typing import Dict, Any

boards: Dict[str, Any] = {
    "deals": {
        "id_env_var": "DEALS_BOARD_ID",
        "columns": {
            "name": "Deal Name",
            "owner": "Owner code",
            "client": "Client Code",
            "status": "Deal Status",
            "close_date_actual": "Close Date (A)",
            "probability": "Closure Probability",
            "value": "Masked Deal value",
            "tentative_close_date": "Tentative Close Date",
            "stage": "Deal Stage",
            "product": "Product deal",
            "sector": "Sector/service",
            "created_date": "Created Date"
        },
        "stages": [
            "B. Sales Qualified Leads",
            "E. Proposal/Commercials Sent",
            "Closed Won",
            "Closed Lost"
        ]
    },
    "work_orders": {
        "id_env_var": "WORK_ORDERS_BOARD_ID",
        "columns": {
            "deal_name": "Unnamed: 0",
            "customer": "Unnamed: 1",
            "serial_number": "Unnamed: 2",
            "nature_of_work": "Unnamed: 3",
            "execution_status": "Unnamed: 5",
            "po_date": "Unnamed: 7",
            "start_date": "Unnamed: 9",
            "end_date": "Unnamed: 10",
            "sector": "Unnamed: 12",
            "type_of_work": "Unnamed: 13",
            "invoice_amount": "Unnamed: 17",
            "billed_value": "Unnamed: 19",
            "collected_amount": "Unnamed: 21",
            "wo_status": "Unnamed: 34",
            "billing_status": "Unnamed: 37"
        }
    }
}
