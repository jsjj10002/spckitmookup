
filepath = 'backend/data/pc_data_dump.sql'
try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            if 'CREATE TABLE' in line:
                print(f"Line {i}: {line.strip()}")
                # Print the schema which follows
                # Assuming schema is short lines like `id int...`
            elif len(line) < 200 and ('`' in line or 'PRIMARY KEY' in line or 'ENGINE=' in line) and not 'INSERT INTO' in line:
                print(f"Line {i}: {line.strip()}")
except Exception as e:
    print(e)
