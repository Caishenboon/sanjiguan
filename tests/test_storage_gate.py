import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StorageGateTests(unittest.TestCase):
    def test_backend_must_be_explicit(self):
        env = dict(os.environ, APP_ENV="development")
        env.pop("STORAGE_BACKEND", None)
        result = subprocess.run(
            [sys.executable, "-c", "import apps.api.app.main"],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("storage_backend_must_be_explicit", result.stderr)

    def test_memory_backend_rejected_in_production(self):
        env = dict(os.environ, APP_ENV="production", STORAGE_BACKEND="memory")
        result = subprocess.run(
            [sys.executable, "-c", "import apps.api.app.main"],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("memory_backend_forbidden_in_production", result.stderr)
