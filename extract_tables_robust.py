
import os

base_dir = os.getcwd()
filepath = os.path.join(base_dir, 'backend', 'data', 'pc_data_dump.sql')
output_path = os.path.join(base_dir, 'found_schemas.txt')
log_path = os.path.join(base_dir, 'extraction.log')

def log(msg):
    with open(log_path, 'a') as f:
        f.write(msg + "\n")

log(f"Starting extraction. File: {filepath}")

if not os.path.exists(filepath):
    log("File not found!")
    exit()

try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        with open(output_path, 'w', encoding='utf-8') as out:
            in_table = False
            table_lines = []
            count = 0
            
            for i, line in enumerate(f):
                line_stripped = line.strip()
                
                if line_stripped.startswith('CREATE TABLE'):
                    in_table = True
                    count += 1
                    log(f"Found table at line {i+1}: {line_stripped}")
                    out.write(f"\nFOUND TABLE at line {i+1}\n")
                    table_lines = [line_stripped]
                elif in_table:
                    table_lines.append(line_stripped)
                    if line_stripped.startswith(') ENGINE='):
                        in_table = False
                        out.write("SCHEMA START\n")
                        out.write('\n'.join(table_lines))
                        out.write("\nSCHEMA END\n")
                        out.write("-" * 20 + "\n")

    log(f"Done. Found {count} tables.")
    
except Exception as e:
    log(f"Error: {e}")
