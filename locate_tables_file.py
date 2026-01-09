
import sys

try:
    with open('tables_found.txt', 'w', encoding='utf-8') as outfile:
        outfile.write("Starting search...\n")
        with open('backend/data/pc_data_dump.sql', 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                if "CREATE TABLE" in line:
                    # Truncate line to avoid huge output
                    short_line = line[:200].strip()
                    outfile.write(f"{i}: {short_line}\n")
        outfile.write("Search complete.\n")
    print("Done")
except Exception as e:
    with open('tables_found.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(f"Error: {e}\n")
