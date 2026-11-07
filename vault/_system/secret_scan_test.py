"""secret_scan.py tests. Sample secrets are built from parts at run time; no real pattern sits in this file."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secret_scan  # noqa: E402

FAKE = {
    "sk": "sk-" + "ant-" + "A1b2C3d4E5f6G7h8I9j0K1l2",
    "github": "gh" + "p_" + "a" * 36,
    "aws": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "key_block": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "product": "-".join(["ABCDE"] * 5),
    "mac": ":".join(["a4"] * 6),
}


class SecretScanTest(unittest.TestCase):
    def kinds(self, line: str) -> list[str]:
        return [k for k, _ in secret_scan.scan_line(line)]

    def test_known_patterns_are_caught(self):
        for label, value in FAKE.items():
            with self.subTest(label):
                self.assertTrue(self.kinds(f"x = {value}"), label)

    def test_assignment_and_placeholder(self):
        self.assertTrue(self.kinds("api_key = " + "Zx9" + "kq2LmN7pQ"))
        for placeholder in ("password: $PASSWORD", "token = <here>", "api_key = os.environ['X']", "secret: ***", "token: example123"):
            with self.subTest(placeholder):
                self.assertEqual(self.kinds(placeholder), [])

    def test_env_json_and_hugging_face(self):
        # Regression: .env keys with a `_` prefix and a quoted JSON key were missed
        for line in ("OPENAI_API_KEY=" + "sk9" + "xQ2mLp8vT4wZ", "DB_PASSWORD=" + "Qw3" + "rTy99zz",
                     '"api_key": "' + "Ab3" + 'dEf9gHij"', "HF_TOKEN=" + "hf_" + "b" * 34):
            with self.subTest(line[:12]):
                self.assertTrue(self.kinds(line))

    def test_code_expression_is_not_a_secret(self):
        # Regression: calls in our own code stopped the commit
        for line in ('token = data.get("token")', 'secret = os.getenv("X")', "password = self.password_field"):
            with self.subTest(line):
                self.assertEqual(self.kinds(line), [])

    def test_ip_only_public_address(self):
        self.assertEqual(self.kinds("server 127.0.0.1:8000 and example 93.184.216.34"), [])
        self.assertEqual(self.kinds("version 0.8.2.1 released; v1.0.0.12"), [])
        self.assertEqual(self.kinds("999.1.2.3 is not an IP"), [])
        self.assertEqual(self.kinds("modem " + "192.168." + "1.1 and docker " + "172.17." + "0.1"), [])   # private network
        self.assertTrue(self.kinds("server " + "8.8." + "4.4"))

    def test_allow_marker(self):
        self.assertEqual(self.kinds(FAKE["aws"] + "  # secret-scan: allow (test)"), [])

    def test_value_is_masked(self):
        values = [v for _, v in secret_scan.scan_line("x " + FAKE["github"])]
        self.assertTrue(all(FAKE["github"] not in v for v in values))


if __name__ == "__main__":
    unittest.main(verbosity=1)
