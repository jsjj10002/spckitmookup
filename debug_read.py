
try:
    with open("backend/data/pc_data_dump.sql", "r", encoding="utf-8", errors="ignore") as f:
        print(f"File opened successfully.")
        for i in range(50):
            line = f.readline()
            if not line: break
            print(f"{i}: {line.strip()}")
except Exception as e:
    print(f"Error: {e}")
