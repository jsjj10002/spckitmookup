
import os

def safe_extract(file_path):
    print(f"Scanning {file_path}...", flush=True)
    if not os.path.exists(file_path):
        print("File not found.")
        return
        
    try:
        with open(file_path, 'rb') as f:
            while True:
                # Read line by line but decoded with replace
                line = f.readline()
                if not line:
                    break
                
                try:
                    line_str = line.decode('utf-8', errors='replace')
                    if "CREATE TABLE" in line_str and ("`cpu`" in line_str or "`gpu`" in line_str or "`motherboard`" in line_str):
                        print(f"FOUND TABLE: {line_str.strip()}", flush=True)
                        # Print next 30 lines
                        for _ in range(40):
                            next_line = f.readline()
                            if not next_line: break
                            s = next_line.decode('utf-8', errors='replace').strip()
                            print(f"  {s}", flush=True)
                            if ";" in s:
                                break
                except Exception:
                    continue
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    safe_extract(os.path.join("backend", "data", "pc_data_dump.sql"))
