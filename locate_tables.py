
import sys

print("Starting search...", flush=True)
try:
    with open('backend/data/pc_data_dump.sql', 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if "CREATE TABLE" in line:
                print(f"FOUND_TABLE: Line {i}: {line[:100].strip()}", flush=True)
    print("Search complete.", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
