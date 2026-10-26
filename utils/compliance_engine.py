import json
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

class ComplianceEngine:
    def __init__(self, data_path: str):
        """Initializes the engine and loads the JSON transaction data into a Pandas DataFrame."""
        self.data_path = data_path
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Loads data from the corporate JSON file and structures timestamps."""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(data.get("transactions", []))
            
            if not df.empty:
                # Enforce chronological types
                df['date_time'] = pd.to_datetime(df['date_time'])
                df['amount'] = df['amount'].astype(float)
                # Extract date alone for daily matching metrics
                df['date_only'] = df['date_time'].dt.date
                
            return df
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading transaction database: {e}")
            return pd.DataFrame()

    def detect_high_daily_velocity(self, max_transactions_per_day: int = 3) -> list:
        """
        NEW: Tracks Daily transaction velocity per user.
        Flags when a single cardholder generates more than the allowed threshold 
        of total transactions within a single calendar day across ALL vendors.
        """
        if self.df.empty:
            return []

        # Count total transactions per cardholder per day
        velocity_counts = self.df.groupby(['cardholder_name', 'date_only'])['transaction_id'].transform('count')
        
        # Filter dataframe rows matching high-velocity threshold violations
        violations = self.df[velocity_counts > max_transactions_per_day]
        return violations.drop(columns=['date_only']).to_dict(orient='records')

    def detect_mcc_blacklist_matches(self, blacklist: Optional[List[str]] = None) -> list:
        """
        UPDATED: Enforces explicit MCC blacklist matching.
        Cross-checks corporate transactions against an array of forbidden 
        or high-risk categories.
        """
        if self.df.empty:
            return []
            
        if blacklist is None:
            # Fallback list capturing our generated target profiles
            blacklist = ["restricted", "casino", "pawn shop", "jewelry"]

        # Convert blacklist phrases to lowercase for resilient case-insensitive matching
        blacklist_lower = [item.lower() for item in blacklist]
        
        # Check if the category string is present in the blacklist array
        is_blacklisted = self.df['category'].str.lower().isin(blacklist_lower)
        
        violations = self.df[is_blacklisted]
        return violations.drop(columns=['date_only']).to_dict(orient='records')

    def detect_split_transactions(self, threshold: float = 5000.0) -> list:
        """
        Flags when a user makes multiple charges at the same vendor on the same day 
        where individual charges are under the threshold, but the aggregate sum exceeds it.
        """
        if self.df.empty:
            return []

        grouped = self.df.groupby(['cardholder_name', 'vendor', 'date_only'])
        flagged_txn_ids = set()

        for (name, vendor, date), group in grouped:
            if len(group) > 1:
                total_daily_spend = group['amount'].sum()
                all_under_threshold = (group['amount'] < threshold).all()
                
                if total_daily_spend > threshold and all_under_threshold:
                    flagged_txn_ids.update(group['transaction_id'].tolist())

        result_df = self.df[self.df['transaction_id'].isin(flagged_txn_ids)]
        return result_df.drop(columns=['date_only']).to_dict(orient='records')

    def detect_weekend_violations(self) -> list:
        """
        Identifies transactions occurring on Saturday (5) or Sunday (6)
        for employees who are NOT in Sales or Operations.
        """
        if self.df.empty:
            return []

        exempt_departments = ['Sales', 'Operations']
        is_weekend = self.df['date_time'].dt.weekday.isin([5, 6])
        is_not_exempt = ~self.df['department'].isin(exempt_departments)
        
        violations = self.df[is_weekend & is_not_exempt]
        return violations.drop(columns=['date_only']).to_dict(orient='records')

    def run_all_checks(self) -> dict:
        """Executes full suite compliance monitoring matching all Step 4 parameters."""
        return {
            "daily_velocity_violations": self.detect_high_daily_velocity(),
            "mcc_blacklist_alerts": self.detect_mcc_blacklist_matches(),
            "split_transactions": self.detect_split_transactions(),
            "weekend_violations": self.detect_weekend_violations()
        }

if __name__ == "__main__":
    engine = ComplianceEngine("data/corporate_card_transactions.json")
    all_alerts = engine.run_all_checks()
    
    print("--- COMPLIANCE ENGINE RUN RESULT ---")
    print(f"Daily Velocity Violations: {len(all_alerts['daily_velocity_violations'])}")
    print(f"MCC Blacklist Matches Found: {len(all_alerts['mcc_blacklist_alerts'])}")
    print(f"Split Transactions Found: {len(all_alerts['split_transactions'])}")
    print(f"Weekend Violations Found: {len(all_alerts['weekend_violations'])}")
