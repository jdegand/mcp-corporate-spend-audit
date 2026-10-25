import json
import pandas as pd

class SavingsAnalyzer:
    def __init__(self, data_path: str):
        """Initializes the savings analysis engine and loads transaction history."""
        self.data_path = data_path
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Loads transactional records into a structured Pandas DataFrame."""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data.get("transactions", []))
            if not df.empty:
                df['amount'] = df['amount'].astype(float)
            return df
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading analytics source data: {e}")
            return pd.DataFrame()

    def get_vendor_concentration_analysis(self) -> list:
        """
        NEW: Aggregates total spend by individual vendor names.
        Sorts the suppliers by gross expenditure volume and injects percentage splits
        relative to total corporate layout to mathematically prove wallet concentration.
        """
        if self.df.empty:
            return []

        # Calculate overall global spend across the entire enterprise profile
        total_enterprise_spend = self.df['amount'].sum()
        
        if total_enterprise_spend == 0:
            return []

        # Aggregate total volume, transactions, and lookups by unique merchant names
        vendor_summary = self.df.groupby('vendor').agg(
            total_spend=('amount', 'sum'),
            transaction_count=('amount', 'count')
        ).reset_index()

        # Calculate concentrations / percentage wallet splits
        vendor_summary['percentage_of_total_spend'] = (vendor_summary['total_spend'] / total_enterprise_spend * 100).round(2)
        vendor_summary['total_spend'] = vendor_summary['total_spend'].round(2)

        # Sort by total volume descending to surface dominant vendors immediately
        sorted_summary = vendor_summary.sort_values(by='total_spend', ascending=False)

        return sorted_summary.to_dict(orient='records')

    def get_vendor_consolidation_opportunities(self, top_n_categories: int = 3) -> list:
        """
        Analyzes categories with high fragmentation (lots of distinct vendors)
        and calculates potential savings if spend was consolidated to the top vendor 
        at a conservative target rate of 12%.
        """
        if self.df.empty:
            return []

        # Group data by category and vendor to get total aggregate spend per vendor
        vendor_spend = self.df.groupby(['category', 'vendor'])['amount'].sum().reset_index()
        
        # Calculate total spend per broad category
        category_spend = self.df.groupby('category')['amount'].sum().reset_index()
        category_spend.columns = ['category', 'total_category_spend']

        # Count how many unique vendors exist in each category
        vendor_counts = self.df.groupby('category')['vendor'].nunique().reset_index()
        vendor_counts.columns = ['category', 'unique_vendor_count']

        # Merge summary metrics
        summary = pd.merge(category_spend, vendor_counts, on='category')
        
        # Filter out 'Restricted' categories as they shouldn't be optimized/consolidated
        summary = summary[summary['category'].str.lower() != 'restricted']
        
        # Find the primary (highest spend) vendor for each category to use as the consolidation anchor
        top_vendors = vendor_spend.sort_values(['category', 'amount'], ascending=[True, False]).groupby('category').first().reset_index()
        top_vendors.columns = ['category', 'top_vendor', 'top_vendor_spend']
        
        summary = pd.merge(summary, top_vendors, on='category')

        opportunities = []
        # Process categories showing fragmentation (more than 1 vendor)
        for _, row in summary[summary['unique_vendor_count'] > 1].iterrows():
            cat = row['category']
            total_spend = row['total_category_spend']
            top_vendor = row['top_vendor']
            top_spend = row['top_vendor_spend']
            
            # Fragmented spend is everything NOT going to your top vendor
            fragmented_spend = total_spend - top_spend
            
            # Standard corporate forecasting assumption: 12% savings via volume procurement
            estimated_savings = round(fragmented_spend * 0.12, 2)
            
            opportunities.append({
                "category": cat,
                "unique_vendors_identified": int(row['unique_vendor_count']),
                "total_category_spend": round(total_spend, 2),
                "recommended_primary_vendor": top_vendor,
                "fragmented_tail_spend": round(fragmented_spend, 2),
                "estimated_consolidation_savings_12pct": estimated_savings,
                "rationalization_strategy": f"Consolidate tail spend from alternative vendors in the '{cat}' category directly into {top_vendor} contracts to capture volume discounts."
            })
            
        # Sort opportunities by highest potential savings first
        opportunities = sorted(opportunities, key=lambda x: x['estimated_consolidation_savings_12pct'], reverse=True)
        return opportunities[:top_n_categories]

    def get_departmental_spend_summary(self) -> list:
        """Generates aggregate spend profiles across all business divisions."""
        if self.df.empty:
            return []

        dept_summary = self.df.groupby('department').agg(
            total_expenditure=('amount', 'sum'),
            transaction_count=('amount', 'count'),
            average_transaction_value=('amount', 'mean')
        ).reset_index()

        # Clean decimal places
        dept_summary['total_expenditure'] = dept_summary['total_expenditure'].round(2)
        dept_summary['average_transaction_value'] = dept_summary['average_transaction_value'].round(2)
        
        return dept_summary.sort_values(by='total_expenditure', ascending=False).to_dict(orient='records')

if __name__ == "__main__":
    # Quick standalone testing context
    analyzer = SavingsAnalyzer("data/corporate_card_transactions.json")
    print("--- CORPORATE SAVINGS METRICS RUN ---")
    print("\n[Vendor Concentration Breakdown]:")
    print(json.dumps(analyzer.get_vendor_concentration_analysis()[:5], indent=2))
