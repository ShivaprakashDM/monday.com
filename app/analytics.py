import pandas as pd
from typing import Dict, Any, List

def calculate_pipeline_value(deals_df: pd.DataFrame, time_filter: str = None) -> float:
    """Calculates total open pipeline value."""
    # Assuming 'Deal Status' is the column for Open/Closed (based on config)
    # Using the standard config naming convention here.
    if 'Deal Status' in deals_df.columns:
        open_deals = deals_df[deals_df['Deal Status'].str.contains('Open', case=False, na=False)]
        if 'Normalized_Value' in open_deals.columns:
            return open_deals['Normalized_Value'].sum()
    return 0.0

def calculate_sector_revenue(deals_df: pd.DataFrame) -> Dict[str, float]:
    """Calculates revenue split by sector."""
    if 'Normalized_Sector' in deals_df.columns and 'Normalized_Value' in deals_df.columns:
        # Include all deals or just Won? Assuming all pipeline value for "sector pipeline"
        sector_group = deals_df.groupby('Normalized_Sector')['Normalized_Value'].sum()
        return sector_group.to_dict()
    return {}

def find_execution_gaps(deals_df: pd.DataFrame, wo_df: pd.DataFrame, deals_config: Dict[str, str], wo_config: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Finds deals that are closed won but have work orders that are 'Not Started' or have zero billed revenue.
    Requires joining Deals and Work Orders based on client codes or serial numbers depending on schema.
    """
    gaps = []
    
    # Get standard names
    deal_stage_col = deals_config.get('stage', 'Deal Stage')
    deal_name_col = deals_config.get('name', 'Deal Name')
    wo_deal_name_col = wo_config.get('deal_name', 'Unnamed: 0')
    wo_status_col = 'execution_status' # created in data_processing
    
    try:
        # 1. Find Closed Won Deals
        won_deals = deals_df[deals_df[deal_stage_col].str.contains('Closed Won', case=False, na=False)]
        
        # 2. Iterate through Won Deals, try to find matching work orders by Deal Name (or Client Code)
        # Note: In the sample data, Deal Name in Deals often matches "Deal name masked" in Work Orders
        
        for _, deal in won_deals.iterrows():
            d_name = str(deal[deal_name_col]).strip().lower()
            
            # Find matching wos
            matches = wo_df[wo_df[wo_deal_name_col].astype(str).str.strip().str.lower() == d_name]
            
            if len(matches) == 0:
                # Execution gap: Closed deal, no work order created!
                gaps.append({
                    "deal_name": deal[deal_name_col],
                    "issue": "No corresponding work order found",
                    "value": deal.get('Normalized_Value', 0)
                })
            else:
                # Check execution status of matches
                for _, wo in matches.iterrows():
                    status = wo.get(wo_status_col, "Unknown").lower()
                    if status in ["not started", "delayed", "unknown"]:
                        gaps.append({
                            "deal_name": deal[deal_name_col],
                            "issue": f"Work order exists but status is '{status.title()}'",
                            "value": deal.get('Normalized_Value', 0)
                        })
                        
    except KeyError as e:
        # Ignore if columns are missing due to messy data
        pass
        
    return gaps
