from pathlib import Path
import os

# Clear terminal for better readability
os.system("clear")

active_folder = Path(__file__).parent.resolve()
print(f"Active folder: {active_folder}")
os.chdir(active_folder)

