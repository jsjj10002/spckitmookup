import os

def extract_schemas():
    targets = {
        56: "cpu",
        170: "memory",
        200: "motherboard",
        321: "video_card"
    }
    
    # Sort targets to process in order
    sorted_targets = sorted(targets.keys())
    
    input_path = os.path.join("backend", "data", "pc_data_dump.sql")
    output_path = "schemas.txt"
    
    print(f"Reading from {input_path}")
    
    target_idx = 0
    start_line = sorted_targets[target_idx]
    end_line = start_line + 30
    
    try:
        with open(input_path, 'rb') as fin, open(output_path, 'w', encoding='utf-8') as fout:
            current_line_num = 1
            capturing = False
            
            # Optimization: could seek if we knew headers, but lines vary.
            # We iterate.
            for line in fin:
                if target_idx >= len(sorted_targets):
                    break

                if current_line_num == start_line:
                    capturing = True
                    fout.write(f"\n--- Schema for {targets[start_line]} (Line {start_line}) ---\n")

                if capturing:
                    try:
                        decoded = line.decode('utf-8', errors='replace').strip()
                        fout.write(decoded + "\n")
                    except:
                        fout.write("<binary/error>\n")
                    
                    if current_line_num >= end_line:
                        capturing = False
                        target_idx += 1
                        if target_idx < len(sorted_targets):
                            start_line = sorted_targets[target_idx]
                            end_line = start_line + 30
                            
                current_line_num += 1
                
        print("Extraction complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        with open(output_path, 'a') as f:
            f.write(f"\nError: {e}")

if __name__ == "__main__":
    extract_schemas()
