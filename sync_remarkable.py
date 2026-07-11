import sys
import os

# Add local folder to path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from remarkable_sync.sync import sync

if __name__ == "__main__":
    sync()
