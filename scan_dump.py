
import re

def scan_sql_dump(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if "CREATE TABLE" in line:
                match = re.search(r"CREATE TABLE [`']?(\w+)[`']?", line)
                if match:
                    print(f"Line {i+1}: {match.group(1)}")
                else:
                    print(f"Line {i+1}: CREATE TABLE (no name found)")

scan_sql_dump('backend/data/pc_data_dump.sql')
