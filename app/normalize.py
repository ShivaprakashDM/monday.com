import pandas as pd
import yaml
import os
from typing import Dict, Any, Tuple
import logging

# Configure logging for Data Quality Notes
logger = logging.getLogger("monday_bi_agent")
logger.setLevel(logging.INFO)

def load_config() -> Dict[str, Any]:
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def clean_currency(value: Any) -> float:
    """
    Normalizes a currency value to a float. Handles string formats with commas, spaces, currency symbols etc.
    Returns 0.0 if not parsable.
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
        
    val_str = str(value).replace(',', '').replace('₹', '').replace('Rs', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def clean_sector(sector: Any) -> str:
    """
    Normalizes sector names (e.g. 'Mining ', 'mining', '  MINING  ' -> 'Mining')
    """
    if pd.isna(sector) or sector is None:
        return "Unknown"
    return str(sector).strip().title()

def process_deals(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, list]:
    """
    Cleans the deals dataframe based on config mappings.
    Returns the cleaned DataFrame and a list of Data Quality Notes.
    """
    qa_notes = []
    deals_cfg = config['boards']['deals']['columns']
    
    # Check for missing critical columns
    missing_cols = [col for col in deals_cfg.values() if col not in df.columns]
    if missing_cols:
        qa_notes.append(f"WARNING: Missing expected columns in Deals board: {missing_cols}")
    
    # 1. Normalize Sector
    sector_col = deals_cfg.get('sector')
    if sector_col in df.columns:
        initial_unknowns = df[sector_col].isna().sum()
        if initial_unknowns > 0:
            qa_notes.append(f"INFO: Normalized {initial_unknowns} null sectors to 'Unknown' in Deals.")
        df['Normalized_Sector'] = df[sector_col].apply(clean_sector)
    
    # 2. Normalize Revenue / Value
    val_col = deals_cfg.get('value')
    if val_col in df.columns:
        df['Normalized_Value'] = df[val_col].apply(clean_currency)
        zero_count = (df['Normalized_Value'] == 0).sum()
        if zero_count > 0:
            qa_notes.append(f"INFO: {zero_count} deals had missing or unparsable revenue values and were treated as $0.")
            
    # 3. Handle Dates
    date_col = deals_cfg.get('created_date')
    if date_col in df.columns:
        df['Normalized_Created_Date'] = pd.to_datetime(df[date_col], errors='coerce')
        
    close_col = deals_cfg.get('tentative_close_date')
    if close_col in df.columns:
        df['Normalized_Close_Date'] = pd.to_datetime(df[close_col], errors='coerce')

    return df, qa_notes


def process_work_orders(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, list]:
    """
    Cleans the work orders dataframe based on config mappings.
    Returns the cleaned DataFrame and a list of Data Quality Notes.
    """
    qa_notes = []
    wo_cfg = config['boards']['work_orders']['columns']
    
    # Missing columns
    missing_cols = [col for col in wo_cfg.values() if col not in df.columns]
    if missing_cols:
        qa_notes.append(f"WARNING: Missing expected columns in Work Orders board: {missing_cols}")

    # 1. Normalize Sector (for cross-board filtering if needed)
    sector_col = wo_cfg.get('sector')
    if sector_col in df.columns:
        df['Normalized_Sector'] = df[sector_col].apply(clean_sector)
        
    # 2. Normalize Financials
    invoice_col = wo_cfg.get('invoice_amount')
    if invoice_col in df.columns:
        df['Normalized_Invoice_Amount'] = df[invoice_col].apply(clean_currency)
        
    billed_col = wo_cfg.get('billed_value')
    if billed_col in df.columns:
        df['Normalized_Billed_Value'] = df[billed_col].apply(clean_currency)
        
    collected_col = wo_cfg.get('collected_amount')
    if collected_col in df.columns:
        df['Normalized_Collected_Amount'] = df[collected_col].apply(clean_currency)

    # 3. Status
    exec_status = wo_cfg.get('execution_status')
    if exec_status in df.columns:
        df['execution_status'] = df[exec_status].fillna("Unknown").astype(str)
        
    return df, qa_notes
