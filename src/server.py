import os
import sys
import json  # Added missing json import required for inspecting data
from mcp.server.mcpserver import MCPServer

# Ensure the root project directory is added to Python path for seamless relative importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.compliance_engine import ComplianceEngine
from utils.savings_analyzer import SavingsAnalyzer

# Initialize Server Engine
server = MCPServer(
    "Corporate-Spend-Audit-Platform",
    version="1.0.0",
    description="Automated MCP audit platform tracking JPM corporate card policy compliance and tail-spend consolidation analytics."
)

# You could set filepath with an environment variable for more flexible versus directly editing
DATA_PATH = os.getenv("TRANSACTION_DATA_PATH", "data/corporate_card_transactions.json")

# Instantiate singleton engine adapters pointed to the JSON database
def get_compliance_engine() -> ComplianceEngine:
    return ComplianceEngine(DATA_PATH)

def get_savings_analyzer() -> SavingsAnalyzer:
    return SavingsAnalyzer(DATA_PATH)


# ==============================================================================
# MCP TOOL REGISTRATIONS: POLICY COMPLIANCE
# ==============================================================================

@server.tool()
def check_all_compliance_violations() -> dict:
    """
    Executes a comprehensive, full-suite compliance audit.
    Returns categorized lists for daily velocity, blacklisted MCCs, split-transactions, and weekend anomalies.
    """
    engine = get_compliance_engine()
    return engine.run_all_checks()


@server.tool()
def get_daily_velocity_alerts(max_transactions: int = 3) -> list:
    """
    Tracks daily transaction velocity per user.
    Flags cardholders who generate an excessive count of total transactions within 
    a single calendar day across all vendors.
    
    Args:
        max_transactions (int): Maximum allowed daily swipes per user before flagging (Defaults to 3).
    """
    engine = get_compliance_engine()
    return engine.detect_high_daily_velocity(max_transactions_per_day=max_transactions)


@server.tool()
def check_mcc_blacklist(forbidden_categories: list = None) -> list:
    """
    Cross-checks corporate transactions against an explicit array of blacklisted or high-risk 
    Merchant Category Codes (MCCs).
    
    Args:
        forbidden_categories (list, optional): Specific phrases to block (e.g., ["Casino", "Restricted"]).
                                               Defaults to a built-in risk array if empty.
    """
    engine = get_compliance_engine()
    return engine.detect_mcc_blacklist_matches(blacklist=forbidden_categories)


@server.tool()
def get_split_transactions(threshold: float = 5000.0) -> list:
    """
    Scans for split-transaction policy circumventing strategies.
    Identifies if a cardholder grouped separate charges on a single day at one vendor
    to deliberately stay beneath a mandatory procurement authorization ceiling.
    
    Args:
        threshold (float): The single transaction spending limit (Defaults to 5000.0).
    """
    engine = get_compliance_engine()
    return engine.detect_split_transactions(threshold=threshold)


@server.tool()
def get_weekend_violations() -> list:
    """
    Isolates corporate transactions occurring over weekends (Saturdays/Sundays).
    Filters out and permits Sales and Operations staff, highlighting un-flagged departments 
    (like Tech or Finance) showing suspicious weekend activity.
    """
    engine = get_compliance_engine()
    return engine.detect_weekend_violations()


# ==============================================================================
# MCP TOOL REGISTRATIONS: FINANCIAL ANALYTICS
# ==============================================================================

@server.tool()
def get_vendor_concentration_analysis() -> list:
    """
    Aggregates total corporate card spend by individual vendor names.
    Outputs metrics sorted by absolute transaction volume along with percentage split values 
    relative to global enterprise spend to mathematically demonstrate supplier concentration.
    """
    analyzer = get_savings_analyzer()
    return analyzer.get_vendor_concentration_analysis()


@server.tool()
def get_vendor_consolidation_opportunities(limit: int = 3) -> list:
    """
    Evaluates fragmentation trends where spend leaked across multiple suppliers in a given vertical.
    Calculates exact metrics for fragmented tail-spend and outputs actionable 12% optimization metrics.
    
    Args:
        limit (int): Maximum number of top opportunities to return (Defaults to 3).
    """
    analyzer = get_savings_analyzer()
    return analyzer.get_vendor_consolidation_opportunities(top_n_categories=limit)


@server.tool()
def get_departmental_spend_summary() -> list:
    """
    Aggregates full corporate exposure profile matrix by corporate department.
    Yields total expenditure vectors, overall counts, and localized mean transaction sizing profiles.
    """
    analyzer = get_savings_analyzer()
    return analyzer.get_departmental_spend_summary()


# ==============================================================================
# MCP TOOL REGISTRATIONS: LEDGER REFLECTION & INVENTORY
# ==============================================================================

@server.tool()
def inspect_data_dictionary() -> dict:
    """
    Dynamically interrogates the active data payload to provide the AI with up-to-date
    categorical values, vendor maps, and structural shapes currently in the database.
    """
    if not os.path.exists(DATA_PATH):
        return {"error": f"Database file at {DATA_PATH} not initialized yet."}
        
    try:
        with open(DATA_PATH, "r") as f:
            payload = json.load(f)
            
        # Target the explicit top-level key defined in seed data wrapper mapping
        records = payload.get("transactions", [])
            
        if not records:
            return {"error": "Database 'transactions' wrapper key is missing or empty."}
            
        sample_record = records[0]
        live_schema = {key: type(value).__name__ for key, value in sample_record.items()}
        
        distinct_categories = sorted(list(set(r.get("category") for r in records if r.get("category"))))
        distinct_statuses = sorted(list(set(r.get("status") for r in records if r.get("status"))))
        
        return {
            "database_file": DATA_PATH,
            "total_record_count": len(records),
            "inferred_schema": live_schema,
            "active_domain_values": {
                "categories": distinct_categories,
                "statuses": distinct_statuses
            }
        }
    except Exception as e:
        return {"error": f"Failed to parse live system metadata: {str(e)}"}


# ==============================================================================
# SERVER BOOTSTRAP INITIALIZATION
# ==============================================================================

def bootstrap_data_environment():
    """
    Validates data directories and automatically triggers the seed generation
    pipeline if local ledger files are missing or uninitialized.
    """
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    
    if not os.path.exists(DATA_PATH):
        print(f"[*] Target ledger '{DATA_PATH}' not found. Initializing seed generation...", file=sys.stderr)
        
        try:
            from scripts.seed_data import generate_synthetic_transactions, save_to_json, save_to_sqlite, NUM_RECORDS
            
            # 1. Generate the raw mock dataset array
            mock_data = generate_synthetic_transactions(NUM_RECORDS)
            
            # 2. Force it to save exactly to the DATA_PATH your server expects
            save_to_json(mock_data, DATA_PATH)
            
            # 3. Derive the DB path safely by replacing the extension
            sqlite_path = DATA_PATH.replace(".json", ".db")
            save_to_sqlite(mock_data, sqlite_path)
            
            print("[+] Sandbox ledger generation complete.", file=sys.stderr)
            
        except ImportError as e:
            print(f"[!] Error: Could not import 'seed_data.py'. Trace: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"[!] Critical bootstrap failure: {str(e)}", file=sys.stderr)
    else:
        print(f"[+] Active transaction ledger found at '{DATA_PATH}'. Skipping seed stage.", file=sys.stderr)


if __name__ == "__main__":
    bootstrap_data_environment()
    server.run(transport="stdio")
