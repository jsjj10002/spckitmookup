
import sys

def scan_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                # Print line number and first 100 chars
                preview = line[:100].strip()
                if "CREATE TABLE" in preview:
                    print(f"Line {i}: {preview}", flush=True)
                elif "INSERT INTO" in preview:
                    print(f"Line {i}: {preview} ... (Length: {len(line)})", flush=True)
                else:
                    # Print interesting lines (short ones that might be headers or checking constraints)
                    if len(line.strip()) > 0 and len(line) < 200:
                         print(f"Line {i}: {preview}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scan_file(sys.argv[1])
    else:
        print("Usage: python scan_structure.py <filepath>")
