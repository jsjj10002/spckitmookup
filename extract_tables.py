
import re
import os

filepath = r'backend\data\pc_data_dump.sql'
print(f"Checking file: {os.path.abspath(filepath)}")

if not os.path.exists(filepath):
    print("File not found!")
    exit()

try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        print(f"File read, size: {len(content)} types")
        
        # Regex to capture table name and the content inside valid parentheses
        # This generic regex expects typical mysqldump format: CREATE TABLE `name` (...);
        # We stop at matching generic closing, or just simple split.
        
        # Let's iterate line by line to be safer against massive single lines
        f.seek(0)
        
        in_table = False
        current_table = None
        current_schema = []
        
        for line in f:
            line_strip = line.strip()
            if line_strip.startswith('CREATE TABLE'):
                in_table = True
                current_table = line_strip.split('`')[1] if '`' in line_strip else 'unknown'
                print(f"FOUND TABLE: {current_table}")
                print(line_strip)
            elif in_table:
                if line_strip.startswith(') ENGINE='):
                    in_table = False
                    print(line_strip)
                    print("-" * 30)
                else:
                    print(line_strip)
            
except Exception as e:
    print(f"Error: {e}")
