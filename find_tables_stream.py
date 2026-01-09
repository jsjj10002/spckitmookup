
import sys

filepath = 'backend/data/pc_data_dump.sql'
try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        line_num = 0
        for line in f:
            line_num += 1
            if 'CREATE TABLE' in line:
                print(f"Line {line_num}: {line.strip()}")
                # Print schema
                for _ in range(20):
                     next_line = next(f, None)
                     line_num += 1
                     if next_line:
                         print(f"  {next_line.strip()}")
                         if 'ENGINE=' in next_line:
                             break
                     else:
                         break
                print("-" * 20)
                sys.stdout.flush()
except Exception as e:
    print(f"Error: {e}")
