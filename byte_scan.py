import os

def scan_file():
    input_path = os.path.join("backend", "data", "pc_data_dump.sql")
    output_path = "found_schemas.txt"
    
    components = [b"CREATE TABLE `cpu`", b"CREATE TABLE `gpu`", b"CREATE TABLE `video_card`", b"CREATE TABLE `motherboard`"]
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write("Scan started...\n")
        
        if not os.path.exists(input_path):
            f_out.write("Input file not found.\n")
            return

        try:
            with open(input_path, "rb") as f_in:
                content = f_in.read()
                f_out.write(f"Read {len(content)} bytes.\n")
                
                for comp in components:
                    idx = content.find(comp)
                    if idx != -1:
                        f_out.write(f"\n--- Found {comp.decode()} at index {idx} ---\n")
                        # Extract next 1000 bytes
                        snippet = content[idx:idx+2000]
                        # stop at first semicolon
                        semicolon = snippet.find(b";")
                        if semicolon != -1:
                            snippet = snippet[:semicolon+1]
                        
                        try:
                            decoded = snippet.decode('utf-8', errors='replace')
                            f_out.write(decoded + "\n")
                        except Exception as e:
                            f_out.write(f"Decoding error: {e}\n")
                    else:
                        f_out.write(f"\n{comp.decode()} NOT FOUND.\n")
                        
        except Exception as e:
            f_out.write(f"Error reading file: {e}\n")

if __name__ == "__main__":
    scan_file()
