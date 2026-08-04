import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.protocols import PROTOCOLS, landscape_table, sdk_availability  # noqa: E402

REQUIRED_KEYS = {"layer", "standardizes", "governance", "status", "source"}


class ProtocolMapTests(unittest.TestCase):
    def test_every_entry_is_complete_with_https_source(self):
        for name, info in PROTOCOLS.items():
            self.assertEqual(set(info), REQUIRED_KEYS, name)
            self.assertTrue(info["source"].startswith("https://"), name)
            for key in REQUIRED_KEYS:
                self.assertTrue(info[key].strip(), f"{name}.{key} is empty")

    def test_hands_on_protocols_are_present(self):
        self.assertIn("MCP", PROTOCOLS)
        self.assertIn("A2A", PROTOCOLS)

    def test_merged_protocol_is_marked_historical(self):
        self.assertIn("merged into A2A", PROTOCOLS["ACP (IBM/BeeAI)"]["status"])

    def test_table_renders_all_rows(self):
        table = landscape_table()
        for name in PROTOCOLS:
            self.assertIn(name, table)

    def test_sdk_availability_reports_booleans(self):
        availability = sdk_availability()
        self.assertEqual(set(availability), {"mcp", "a2a"})
        for value in availability.values():
            self.assertIsInstance(value, bool)


if __name__ == "__main__":
    unittest.main()
