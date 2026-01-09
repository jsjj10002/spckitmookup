
import os

filepath = 'backend/data/pc_data_dump.sql'
try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if 'CREATE TABLE' in line:
            print(f"Line {i+1}: {line.strip()}")
            # Print next few lines to see columns
            for j in range(1, 15):
                if i+j < len(lines):
                    print(f"  {lines[i+j].strip()}")
                else:
                    break
            print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
