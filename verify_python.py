
import os
import sys

print("Hello from stdout")
with open("verify_out.txt", "w") as f:
    f.write(f"Hello from file. Python version: {sys.version}")
