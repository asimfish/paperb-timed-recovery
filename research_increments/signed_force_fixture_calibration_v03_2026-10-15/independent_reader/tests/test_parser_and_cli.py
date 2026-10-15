import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"code"))
from audit_fixture import Rejected, parse


class ParserAndCLITests(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_rejected(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(Rejected):
                parse(text)

    def test_cli_requires_external_request_digest_before_reading_native(self):
        code = Path(__file__).resolve().parents[1]/"code"/"audit_fixture.py"
        with tempfile.TemporaryDirectory(prefix="paperb_reader_synthetic_refusal_") as temp:
            root = Path(temp)
            request = root/"REQUEST.json"
            request.write_text('{"explicitly_synthetic":true}\n')
            out = root/"output"
            result = subprocess.run([sys.executable, "-B", str(code), "--request", str(request),
                "--request-sha256", "0"*64, "--reader-freeze-sha256", "0"*64,
                "--output", str(out)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 3)
            self.assertIn("external root request digest", result.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
