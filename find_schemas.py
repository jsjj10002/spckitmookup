
import os

def find_create_tables(file_path, output_path):
    print(f"Scanning {file_path}...", flush=True)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            with open(output_path, "w", encoding="utf-8") as out:
                for i, line in enumerate(f, 1):
                    if "CREATE TABLE" in line:
                        out.write(f"{i}: {line.strip()}\n")
                        print(f"Found: {line.strip()}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(f"Error: {e}\n")

if __name__ == "__main__":
    find_create_tables("backend/data/pc_data_dump.sql", "schemas_found.txt")
