
import os

file_path = r'c:\Users\nrtak\Desktop\testing\1\spckitmookup\backend\data\pc_data_dump.sql'
output_path = r'c:\Users\nrtak\Desktop\testing\1\spckitmookup\sql_structure.txt'

try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f, open(output_path, 'w', encoding='utf-8') as out:
        line_num = 0
        for line in f:
            line_num += 1
            stripped = line.strip()
            if stripped.upper().startswith("CREATE TABLE"):
                out.write(f"Line {line_num}: {stripped[:200]}\n")
            elif stripped.upper().startswith("INSERT INTO") and len(stripped) < 200:
                 # Only print short inserts to avoid noise, or just skip inserts
                 pass
    print("Done")
except Exception as e:
    print(f"Error: {e}")
