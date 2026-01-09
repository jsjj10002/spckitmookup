
import os
import sys

file_path = r'c:\Users\nrtak\Desktop\testing\1\spckitmookup\backend\data\pc_data_dump.sql'

print(f"Starting scan of {file_path}", flush=True)
if not os.path.exists(file_path):
    print(f"File not found: {file_path}", flush=True)
    exit(1)

try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        line_num = 0
        for line in f:
            line_num += 1
            stripped = line.strip()
            if stripped.upper().startswith("CREATE TABLE"):
                print(f"Line {line_num}: {stripped[:200]}", flush=True)
            elif stripped.upper().startswith("INSERT INTO"):
                 # Just mention it exists
                 if line_num % 1000 == 0:
                     print(f"Processing line {line_num}...", flush=True)
    print("Done", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
