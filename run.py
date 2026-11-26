"""
Projekt Red Desktop Pet - Primary Runner.
"""

import sys
from pathlib import Path

# Add src/ to sys.path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from pet.app import main

if __name__ == "__main__":
    sys.exit(main())
