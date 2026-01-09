
import sys
import os

filepath = r'backend\data\pc_data_dump.sql'
output_path = r'found_schemas.txt'

try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f, open(output_path, 'w', encoding='utf-8') as out:
        in_table = False
        table_lines = []
        
        for i, line in enumerate(f):
            line_stripped = line.strip()
            
            if line_stripped.startswith('CREATE TABLE'):
                in_table = True
                out.write(f"FOUND TABLE at line {i+1}\n")
                table_lines = [line_stripped]
            elif in_table:
                table_lines.append(line_stripped)
                if line_stripped.startswith(') ENGINE='):
                    in_table = False
                    out.write("SCHEMA START\n")
                    out.write('\n'.join(table_lines))
                    out.write("\nSCHEMA END\n")
                    out.write("-" * 20 + "\n")

except Exception as e:
    with open(output_path, 'a') as out:
        out.write(f"Error: {e}\n")
