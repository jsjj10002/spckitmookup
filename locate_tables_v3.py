
import sys
import os

print("Script starting...", file=sys.stderr)

try:
    base_dir = os.getcwd()
    sql_path = os.path.join(base_dir, 'backend', 'data', 'pc_data_dump.sql')
    output_path = os.path.join(base_dir, 'tables_found.txt')

    print(f"Reading from: {sql_path}", file=sys.stderr)
    print(f"Writing to: {output_path}", file=sys.stderr)

    if not os.path.exists(sql_path):
        print("Error: SQL file not found!", file=sys.stderr)
        sys.exit(1)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write("Starting search...\n")
        with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                if "CREATE TABLE" in line:
                    short_line = line[:200].strip()
                    outfile.write(f"{i}: {short_line}\n")
                    print(f"Found: {short_line}", file=sys.stderr)
        outfile.write("Search complete.\n")
    print("Done", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    # Try writing error to file too
    try:
        with open('error_log.txt', 'w') as f:
            f.write(str(e))
    except:
        pass
