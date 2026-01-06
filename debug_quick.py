import os

print("Hello from debug_quick.py", flush=True)

file_path = os.path.join("backend", "data", "pc_data_dump.sql")
print(f"Checking {file_path}", flush=True)

if os.path.exists(file_path):
    print(f"File exists. Size: {os.path.getsize(file_path)} bytes", flush=True)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(100)
            print(f"First 100 bytes: {header}", flush=True)
    except Exception as e:
        print(f"Error reading file: {e}", flush=True)
else:
    print("File does not exist.", flush=True)
