"""
test_v3_verification.py - 兼容转发至 v4 验收测试
"""

import sys
from pathlib import Path

pet_root = Path(__file__).resolve().parent.parent
if str(pet_root) not in sys.path:
    sys.path.insert(0, str(pet_root))

from tests.test_v4_verification import run_tests

if __name__ == "__main__":
    run_tests()

