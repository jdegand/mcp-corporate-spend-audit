import json
import sqlite3
import random
from datetime import datetime, timedelta

# --- CONFIGURATION & SEED ARRAYS ---
NUM_RECORDS = 120  # Increased slightly to make room for injected test cases
JSON_FILENAME = "data/corporate_card_transactions.json"
SQLITE_FILENAME = "data/corporate_card_transactions.db" 


NAMES = [
    "Sarah Jenkins", "Michael Chang", "Amira Patel", "David Ross", 
    "Elena Rostova", "Marcus Vance", "Chloe Beauchamp", "Kenji Sato", 
    "Ken Rogers", "Steven Yu"
]

TITLES_DEPTS = [
    ("VP of Sales", "Sales"),
    ("Regional Director", "Operations"),
    ("Head of Engineering", "Technology"),
    ("Marketing Lead", "Marketing"),
    ("Senior Account Executive", "Sales"),
    ("Procurement Manager", "Finance")
]

# Added high-risk high-end retail and restricted categories to the pool
CATEGORIES_VENDORS = {
    "Travel": ["Ritz-Carlton", "Uber", "Delta Air Lines", "Airbnb"],
    "Entertainment": ["Topgolf", "Ticketmaster", "Client Dinner - Steakhouse", "Broadway NYC"],
    "Fuel": ["JPMorgan Fleet Fuel", "Shell Oil", "ExxonMobil"],
    "Retail": ["Amazon Business", "Staples", "Apple Store", "Best Buy Enterprise"],
    "Restricted": ["Golden Nugget Casino", "EZPAWN", "Luxury Diamonds Inc", "Grand Bazaar Electronics"]
}

STATUSES = ["Pending", "Approved", "Flagged"]

def generate_synthetic_transactions(count=120):
    """Generates synthetic records laced with explicit policy violations for LLM testing."""
    transactions = []
    start_date = datetime.now() - timedelta(days=90)
    
    # --- PHASE 1: GENERATE STANDARD CONTEXT DATA ---
    for i in range(1, count - 15 + 1):  # Save the last 15 slots for injected violations
        tx_id = f"TXN-{1000 + i}"
        name = random.choice(NAMES)
        title, department = random.choice(TITLES_DEPTS)
        
        # Pull from normal categories for standard noise
        category = random.choice(["Travel", "Entertainment", "Fuel", "Retail"])
        vendor = random.choice(CATEGORIES_VENDORS[category])
        
        if category == "Travel":
            amount = round(random.uniform(150.00, 1200.00), 2)
        elif category == "Entertainment":
            amount = round(random.uniform(80.00, 400.00), 2)
        elif category == "Fuel":
            amount = round(random.uniform(35.00, 120.00), 2)
        else:
            amount = round(random.uniform(15.00, 500.00), 2)
            
        # Random dates
        random_days = random.randint(0, 90)
        random_hours = random.randint(9, 17)  # Normal working hours
        random_minutes = random.randint(0, 59)
        tx_time = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        transactions.append({
            "transaction_id": tx_id,
            "cardholder_name": name,
            "title": title,
            "department": department,
            "vendor": vendor,
            "amount": amount,
            "date_time": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "status": "Approved" if random.random() > 0.15 else "Pending"
        })

    # --- PHASE 2: INJECT MUST-HAVE TEST CASES (VIOLATIONS) ---
    current_index = len(transactions) + 1
    
    # 1. Split-Transaction Violation (Bypassing $5000 Single Purchase Limit)
    # Steven Yu (Procurement) makes three $1,850 charges at Apple Store on the same day
    split_date = start_date + timedelta(days=15, hours=10)
    for _ in range(3):
        transactions.append({
            "transaction_id": f"TXN-{1000 + current_index}",
            "cardholder_name": "Steven Yu",
            "title": "Procurement Manager",
            "department": "Finance",
            "vendor": "Apple Store",
            "amount": 1850.00,  # 3x = $5,550 total
            "date_time": split_date.strftime("%Y-%m-%d %H:%M:%S"),
            "category": "Retail",
            "status": "Pending"
        })
        current_index += 1
        split_date += timedelta(minutes=45) # Clustered timestamps
        
    # 2. Weekend/Holiday Violation
    # Head of Engineering (not an active weekend traveler) charging a Ritz-Carlton on a Sunday
    sunday_date = start_date
    while sunday_date.weekday() != 6: # Find the first Sunday in the timeline
        sunday_date += timedelta(days=1)
    sunday_tx_time = sunday_date.replace(hour=23, minute=14)
    
    transactions.append({
        "transaction_id": f"TXN-{1000 + current_index}",
        "cardholder_name": "Amira Patel",
        "title": "Head of Engineering",
        "department": "Technology",
        "vendor": "Ritz-Carlton",
        "amount": 850.00,
        "date_time": sunday_tx_time.strftime("%Y-%m-%d %H:%M:%S"),
        "category": "Travel",
        "status": "Pending"
    })
    current_index += 1

    # 3. Restricted Category Violation (Casino, Pawn Shop, Luxury Jewels)
    restricted_vios = [
        ("Ken Rogers", "Marketing Lead", "Marketing", "Golden Nugget Casino", 450.00, "Restricted"),
        ("Michael Chang", "Regional Director", "Operations", "EZPAWN", 120.00, "Restricted"),
        ("Elena Rostova", "Senior Account Executive", "Sales", "Luxury Diamonds Inc", 3200.00, "Restricted")
    ]
    for name, title, dept, vendor, amt, cat in restricted_vios:
        random_vio_date = start_date + timedelta(days=random.randint(20, 50), hours=14)
        transactions.append({
            "transaction_id": f"TXN-{1000 + current_index}",
            "cardholder_name": name,
            "title": title,
            "department": dept,
            "vendor": vendor,
            "amount": amt,
            "date_time": random_vio_date.strftime("%Y-%m-%d %H:%M:%S"),
            "category": cat,
            "status": "Flagged"  # Pre-flagging some restricted ones to see if LLM identifies why
        })
        current_index += 1

    # Shuffle everything so the violations are hidden naturally in the list structure
    random.shuffle(transactions)
    return transactions

def save_to_json(data, filename):
    """Saves the data cleanly to a local JSON file."""
    output = {"transactions": data}
    with open(filename, "w") as f:
        json.dump(output, f, indent=4)
    print(f" Saved {len(data)} records to JSON: '{filename}'")

def save_to_sqlite(data, filename):
    """Saves the data into a local structured SQLite database."""
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            cardholder_name TEXT,
            title TEXT,
            department TEXT,
            vendor TEXT,
            amount REAL,
            date_time TEXT,
            category TEXT,
            status TEXT
        )
    """)
    
    cursor.execute("DELETE FROM transactions")
    
    insert_query = """
        INSERT INTO transactions VALUES (
            :transaction_id, :cardholder_name, :title, :department, 
            :vendor, :amount, :date_time, :category, :status
        )
    """
    cursor.executemany(insert_query, data)
    
    conn.commit()
    conn.close()
    print(f" Saved {len(data)} records to SQLite: '{filename}'")

if __name__ == "__main__":
    print("Generating synthetic dataset with policy rules applied...")
    mock_data = generate_synthetic_transactions(NUM_RECORDS)
    save_to_json(mock_data, JSON_FILENAME)
    save_to_sqlite(mock_data, SQLITE_FILENAME)
