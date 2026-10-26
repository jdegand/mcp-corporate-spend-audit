# Corporate Spend Audit Platform (MCP)

An automated Model Context Protocol (MCP) server engineered using Python and FastMCP to parse, audit, and analyze corporate card datasets (e.g., JPM transaction sets). Built explicitly with an isolated, file-based JSON architecture, this platform bypasses complex server infrastructure to enable instant, zero-dependency prototyping and evaluation.
The system features two core analytical pillars:

* Compliance Engine: A heuristic policy-monitoring layer designed to instantly flag occupational fraud, daily transaction velocity anomalies, blacklisted MCC categories, and split-transaction circumvention tactics.

* Savings Analyzer: A financial optimization matrix that aggregates vendor spend, assesses supplier concentration profiles, and uncovers actionable tail-spend consolidation metrics for executive evaluation.

---

## Project Architecture

```text
mcp-corporate-spend-audit/
├── data/
│   └── corporate_card_transactions.json  # Synthetic JPM card dataset (Read-only)
├── scripts/
│   └── seed_data.py                      # Deterministic synthetic data generator
├── src/
│   └── server.py                         # Core FastMCP Server & tool declarations
├── utils/
│   ├── __init__.py
│   ├── compliance_engine.py              # Logic for split-tx, velocity, and MCC checks
│   └── savings_analyzer.py               # Logic for concentration and vendor consolidation
├── .gitignore                            # Excludes logs, virtual envs, and data.json
└── requirements.txt                      # Project package dependencies
```

---

## Quick Start Setup

### 1. Clone & Set Up Environment

Navigate to your preferred directory, clone the project folder, and spin up an isolated virtual environment:

  ```bash
  cd mcp-corporate-spend-audit
  python -m venv venv          # Use 'python' or 'python3' based on OS
  source venv/bin/activate          # On Windows use: venv\Scripts\activate
  ```

### 2. Install Dependencies

Install the required analytical and protocol libraries via pip:

  ```bash
  pip install -r requirements.txt
  ```

### 3. Generate the Synthetic Dataset

Run the data seeding script to create a fresh, randomized corporate transaction profile populated with real compliance violation traps (split-transactions, velocity bypasses, and blacklisted MCC categories):

  ```bash
  python scripts/seed_data.py
  ```

*This drops `corporate_card_transactions.json` safely inside your local `data/` folder.*

---

## MCP Tool Suite Capabilities

Once connected to an LLM client, the platform exposes the following robust corporate governance tools:

### Policy Compliance Tools

* `check_all_compliance_violations`: Runs the global diagnostic check across all rule paradigms simultaneously.
* `get_daily_velocity_alerts`: Surfaces cardholders hitting excessive swipe milestones within a single calendar date.
* `check_mcc_blacklist`: Scans category vectors against explicit restricted industries (Casinos, Pawn Shops, etc.).
* `get_split_transactions`: Catches users placing multiple sub-threshold charges on a single day at one vendor to bypass corporate capital authorization rules (e.g., three $1,850 charges to skip a $5,000 protocol ceiling).
* `get_weekend_violations`: Triggers alerts on non-travel personnel logging weekend charges.

### Financial Analytics Tools

* `get_vendor_concentration_analysis`: Groups, sums, and calculates gross wallet-share percentages per merchant name to mathematically establish volume leverage.
* `get_vendor_consolidation_opportunities`: Flags high-fragmentation verticals and models an automated 12% savings index map if tail-spend is funneled into a primary preferred vendor contract.
* `get_departmental_spend_summary`: Generates high-level departmental budgeting run-rates.

---

## Claude Desktop Integration

To link this audit framework directly into your **Claude Desktop** client, copy the configuration block below into your local app properties file.

### File Location

* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Matrix

Open your `claude_desktop_config.json` and append the following server key under the `"mcpServers"` object. **Ensure you replace `/ABSOLUTE/PATH/TO/` with your exact machine project directory root.**

```json
{
  "mcpServers": {
    "corporate-spend-audit": {
      "command": "python",
      "args": [
        "src/server.py"
      ],
      "cwd": "/ABSOLUTE/PATH/TO/mcp-corporate-spend-audit",
      "env": {
        "TRANSACTION_DATA_PATH": "data/corporate_card_transactions.json"
      }
    }
  }
}
```

> **Pro-Tip:** Completely quit Claude Desktop (via the Mac menu bar or Windows tray) and launch it fresh to let the client build your active tool map. Look for the small plug icon or hammer tool inside the text input container to begin asking compliance questions!

### Manual Testing

```bash
npx @modelcontextprotocol/inspector python server.py
```

### Verification Checklist

Here is your complete verification checklist to systematically test the MCP server using the @modelcontextprotocol/inspector web interface.
Apply these steps in order to guarantee that your compliance thresholds, financial aggregators, and dynamic data profiling methods operate flawlessly before attaching the server to an LLM client like Claude Desktop.

Phase 1: Environment & Boot Validation

Run the inspector from your project root:

```bash
npx @modelcontextprotocol/inspector python3 src/server.py
```

• Process Boot Verification: The console does not crash with a SyntaxError or ImportError. It should display a local URL (e.g., `http://localhost:3000`).
• Stream Integrity: No regular data strings or unhandled warnings are leaking into stdout. (All boot logs must show up on the stderr stream channel).
• Lazy-Seed Generation:
    • If data/corporate_card_transactions.json was deleted prior to execution, verify the file is recreated on launch.
    • Verify the folder contains both the .json ledger and the .db SQLite tracking file.

Phase 2: Ledger Reflection Functional Checks

Open the web inspector UI in your browser and select the inspect_data_dictionary tool from the dropdown panel.
• Record Capacity Verification: The key total_record_count returns an exact value equal to your configuration specification (120).
• Schema Extraction Resolution: The field inferred_schema explicitly maps fields to type classifications:
  • "amount": "float" or "int"
  • "transaction_id": "str"
  • "date_time": "str"
• Domain Constraint Auditing: The active_domain_values list maps all 5 categories from your configuration seed array, explicitly containing ["Entertainment", "Fuel", "Restricted", "Retail", "Travel"].

Phase 3: Compliance Logic Assertions

Run these tools individually to confirm your algorithm catches the seed data injections:
• check_mcc_blacklist:
  • Must flag exactly 3 violations from the restricted seed group.
  • Must explicitly identify Ken Rogers (Casino), Michael Chang (Pawn Shop), and Elena Rostova (Diamonds).
• get_split_transactions:
  • Must flag Steven Yu for bypassing procurement authorization limits at the Apple Store.
  • Verify that the grouped charges are consolidated on the same day and sum up over the $5000.00 ceiling limit.
• get_weekend_violations:
  • Must flag Amira Patel (Head of Engineering) for her Sunday charge at the Ritz-Carlton.
  • Confirm that Sales and Operations staff entries on weekends are correctly ignored and omitted by the tool's filter.
• get_daily_velocity_alerts:
  • Call with max_transactions=3. Verify that it flags cardholders who exceeded 3 swipes in a single calendar day.

Phase 4: Financial Analytics Core Checks

Verify that the SavingsAnalyzer engine parses data matrices accurately without raising a KeyError or returning empty results:
• get_vendor_concentration_analysis:
  • Returns an array sorted in descending order by raw transaction volume.
  • Contains calculated floating-point percentage values mapping supplier concentration relative to your total operational budget.
• get_departmental_spend_summary:
  • Correctly groups metrics into distinct buckets for Sales, Operations, Technology, Marketing, and Finance.
  • Verifies localized tracking vectors, showing total expenditure sum, overall ticket counts, and mean transaction sizing.
• get_vendor_consolidation_opportunities:
  • Outputs the correct number of records specified by your execution limit parameter (defaults to 3).

Phase 5: Complete Pipeline Synthesis

• check_all_compliance_violations:
  • Run the comprehensive suite engine check.
  • Verify that the returned JSON payload maps out structural dictionary keys for all categories (velocity alerts, blacklist matches, split transactions, and weekend violations) simultaneously.
