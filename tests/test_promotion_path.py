# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Self-test for the promotion path to validate readiness gates.
"""

import unittest
from core.enforcement_mode import get_mode
from core.reality_classifier import classify_action
from core.value_scoreboard import load_scoreboard

class TestPromotionPath(unittest.TestCase):

    def test_enforcement_mode(self):
        """Test that the enforcement mode is correctly set to OBSERVE."""
        self.assertEqual(get_mode(), "OBSERVE")

    def test_reality_classifier(self):
        """Test that actions are classified correctly."""
        self.assertEqual(classify_action("test.critical_action"), "BLOCK")
        self.assertEqual(classify_action("test.high_risk_action"), "WARN")
        self.assertEqual(classify_action("test.default_action"), "ALLOW")

    def test_value_scoreboard(self):
        """Test that the scoreboard loads correctly."""
        scoreboard = load_scoreboard()
        self.assertIsInstance(scoreboard, dict)

if __name__ == "__main__":
    unittest.main()
