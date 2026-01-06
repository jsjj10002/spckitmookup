
import os
from pathlib import Path

def extract():
    # Relative path from this script (backend/) to data/
    base_dir = Path(__file__).parent.parent
    sql_path = base_dir / "backend" / "data" / "pc_data_dump.sql"
    output_path = base_dir / "backend" / "found_schemas.py"
    
    print(f"Reading {sql_path}")
    
    schemas = {}
    targets = [b"CREATE TABLE `cpu`", b"CREATE TABLE `gpu`", b"CREATE TABLE `video_card`", b"CREATE TABLE `motherboard`", b"CREATE TABLE `memory`"]
    
    try:
        with open(sql_path, "rb") as f:
            content = f.read()
            
        for t in targets:
            start_idx = content.find(t)
            if start_idx != -1:
                # Find the closing semicolon
                end_idx = content.find(b";", start_idx)
                if end_idx != -1:
                    schema_bytes = content[start_idx:end_idx+1]
                    try:
                        schema_str = schema_bytes.decode('utf-8', errors='replace')
                        name = t.decode().replace("CREATE TABLE ", "").strip("`")
                        schemas[name] = schema_str
                    except:
                        pass
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Extracted Schemas\n\n")
            for k, v in schemas.items():
                f.write(f"{k}_schema = \"\"\"\n{v}\n\"\"\"\n\n")
                
        print(f"Wrote to {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        with open(output_path, "w") as f:
            f.write(f"# Error: {e}")

if __name__ == "__main__":
    extract()
