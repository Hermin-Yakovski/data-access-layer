#!/usr/bin/env python3
"""
Basic usage examples for the data-access-layer package.

This script demonstrates how to use all available handlers to read and write data.
"""

from pathlib import Path
from dal import JsonHandler, CsvHandler, PklHandler, XlsxHandler

# Create a sample data directory
data_dir = Path("examples/data")
output_dir = Path("examples/output")
data_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

# Sample data
sample_users = [
    {"name": "Alice", "age": 30, "city": "New York"},
    {"name": "Bob", "age": 25, "city": "Los Angeles"},
    {"name": "Charlie", "age": 35, "city": "Chicago"},
    {"name": "Diana", "age": 28, "city": "Houston"},
]

print("=" * 60)
print("Data Access Layer - Basic Usage Examples")
print("=" * 60)

# ============================================================================
# JSON Handler Examples
# ============================================================================
print("\n1. JSON Handler Examples")
print("-" * 60)

json_handler = JsonHandler(indent=2)

# Store data
json_handler.store(
    data=sample_users,
    path=output_dir,
    table="users.json",
    overwrite=True
)
print(f"[OK] Stored data to {output_dir / 'users.json'}")

# Fetch all data
all_users = json_handler.fetch(path=output_dir, table="users.json")
print(f"[OK] Fetched {len(all_users)} users from JSON")

# Fetch with filter (users over 30)
filtered_users = json_handler.fetch(
    path=output_dir,
    table="users.json",
    filter_=lambda row: row["age"] > 30
)
print(f"[OK] Fetched {len(filtered_users)} users over 30 years old")

# Fetch with column selection
user_names = json_handler.fetch(
    path=output_dir,
    table="users.json",
    cols=["name", "age"]
)
print(f"[OK] Fetched name and age for {len(user_names)} users")

# ============================================================================
# CSV Handler Examples
# ============================================================================
print("\n2. CSV Handler Examples")
print("-" * 60)

csv_handler = CsvHandler(delimiter=',', encoding='utf-8')

# Store data
csv_handler.store(
    data=sample_users,
    path=output_dir,
    table="users.csv",
    overwrite=True
)
print(f"[OK] Stored data to {output_dir / 'users.csv'}")

# Fetch all data
all_users = csv_handler.fetch(path=output_dir, table="users.csv")
print(f"[OK] Fetched {len(all_users)} users from CSV")

# Fetch with limit (first 2 users)
limited_users = csv_handler.fetch(
    path=output_dir,
    table="users.csv",
    limit=2
)
print(f"[OK] Fetched first {len(limited_users)} users from CSV")

# ============================================================================
# Pickle Handler Examples
# ============================================================================
print("\n3. Pickle Handler Examples")
print("-" * 60)

pkl_handler = PklHandler(protocol=4)

# Store data
pkl_handler.store(
    data=sample_users,
    path=output_dir,
    table="users.pkl",
    overwrite=True
)
print(f"[OK] Stored data to {output_dir / 'users.pkl'}")

# Fetch all data
all_users = pkl_handler.fetch(path=output_dir, table="users.pkl")
print(f"[OK] Fetched {len(all_users)} users from Pickle")

# ============================================================================
# Excel XLSX Handler Examples
# ============================================================================
print("\n4. Excel XLSX Handler Examples")
print("-" * 60)

xlsx_handler = XlsxHandler(sheet_name='Users', header_row=0)

# Store data
xlsx_handler.store(
    data=sample_users,
    path=output_dir,
    table="users.xlsx",
    overwrite=True
)
print(f"[OK] Stored data to {output_dir / 'users.xlsx'}")

# Fetch all data
all_users = xlsx_handler.fetch(path=output_dir, table="users.xlsx")
print(f"[OK] Fetched {len(all_users)} users from XLSX")

# ============================================================================
# Advanced Examples
# ============================================================================
print("\n5. Advanced Examples")
print("-" * 60)

# Complex filtering and column selection
# Filter by users under 30, limit to 2 results
result = json_handler.fetch(
    path=output_dir,
    table="users.json",
    filter_=lambda row: row["age"] < 30,  # Filter by age
    limit=2  # Maximum 2 results
)
print(f"[OK] Complex query: {len(result)} users under 30")
for user in result:
    print(f"  - {user['name']}, age {user['age']}, from {user['city']}")

# Append mode
new_users = [
    {"name": "Eve", "age": 32, "city": "Phoenix"},
    {"name": "Frank", "age": 27, "city": "Philadelphia"},
]
json_handler.store(
    data=new_users,
    path=output_dir,
    table="users_append.json",
    overwrite=True  # First write
)
json_handler.store(
    data=[{"name": "Grace", "age": 29, "city": "San Antonio"}],
    path=output_dir,
    table="users_append.json",
    overwrite=False  # Append mode
)
appended_users = json_handler.fetch(path=output_dir, table="users_append.json")
print(f"[OK] Append mode: {len(appended_users)} total users after append")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("All handlers provide a consistent API:")
print("  - fetch(path, table, cols, filter_, limit, strict)")
print("  - store(data, path, table, cols, filter_, limit, overwrite, strict)")
print("\nSupported formats:")
print("  - JSON (JsonHandler)")
print("  - CSV (CsvHandler)")
print("  - Pickle (PklHandler)")
print("  - Excel XLSX (XlsxHandler)")
print("\nOutput files created in:")
print(f"  {output_dir.absolute()}")
print("=" * 60)
