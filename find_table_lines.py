
import sys

def find_create_tables(filename):
    print(f"Reading {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if "CREATE TABLE" in line:
                    print(f"{i}: {line.strip()}")
                    sys.stdout.flush()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_create_tables(r"c:\Users\nrtak\Desktop\testing\1\spckitmookup\backend\data\pc_data_dump.sql")
