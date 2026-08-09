import os
import sys

# Ensure module path includes instagram-user-details folder
dir_path = os.path.dirname(os.path.abspath(__file__))
sub_path = os.path.join(dir_path, "instagram-user-details")
if sub_path not in sys.path:
    sys.path.insert(0, sub_path)

from main import main

if __name__ == "__main__":
    main()