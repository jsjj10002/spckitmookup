
import os

file_path = r'c:\Users\nrtak\Desktop\testing\1\spckitmookup\backend\data\pc_data_dump.sql'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        stripped = line.strip()
        if stripped.startswith("CREATE TABLE") or stripped.startswith("INSERT INTO") or stripped.startswith("DROP TABLE"):
            print(f"Line {i}: {stripped[:100]}...")
