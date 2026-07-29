import subprocess
import sys
import unittest
from pathlib import Path


class ProductSpineV1ContractTests(unittest.TestCase):
    def test_static_product_boundary_gate(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "validate_product_spine_v1.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("product-spine-v1", result.stdout)


if __name__ == "__main__":
    unittest.main()
