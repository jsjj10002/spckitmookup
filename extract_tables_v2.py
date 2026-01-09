
import sys
import os

filepath = r'backend\data\pc_data_dump.sql'
print(f"Reading {filepath}...", flush=True)

if not os.path.exists(filepath):
    print("File not found!", flush=True)
    exit()

try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        in_table = False
        table_lines = []
        
        for i, line in enumerate(f):
            # Print progress every 50 lines because we suspect few total lines
            if i % 50 == 0:
                print(f"Processing line {i}...", flush=True)
            
            line_stripped = line.strip()
            
            if line_stripped.startswith('CREATE TABLE'):
                in_table = True
                print(f"\nFOUND TABLE at line {i+1}", flush=True)
                table_lines = [line_stripped]
            elif in_table:
                table_lines.append(line_stripped)
                if line_stripped.startswith(') ENGINE='):
                    in_table = False
                    print("SCHEMA START", flush=True)
                    print('\n'.join(table_lines))
                    print("SCHEMA END", flush=True)
                    print("-" * 20, flush=True)

except Exception as e:
    print(f"Error: {e}", flush=True)

print("Done.", flush=True)
