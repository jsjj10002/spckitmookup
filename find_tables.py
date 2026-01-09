
def find_tables(path):
    with open(path, 'rb') as f:
        content = f.read()
    
    # It's 11MB, reading into memory is fine.
    # We'll split by newline.
    lines = content.split(b'\n')
    for i, line in enumerate(lines):
        try:
            line_str = line.decode('utf-8', errors='ignore')
            if line_str.strip().startswith('CREATE TABLE'):
                print(f"Line {i+1}: {line_str.strip()}")
        except:
            pass

find_tables('backend/data/pc_data_dump.sql')
