import unittest
import os
from executor import execute_strategy, generate_hinglish_call, INTERVENTION_COSTS

class TestExecutionEngine(unittest.TestCase):
    def test_execute_strategy_retry(self):
        res = execute_strategy("retry", "bank_timeout", 1, 1000.0)
        self.assertIn("outcome", res)
        self.assertIn("reasoning_trace", res)
        self.assertIn("success", res)
        self.assertIn("cost", res)
        self.assertEqual(res["cost"], INTERVENTION_COSTS["retry"])

    def test_execute_strategy_bnpl(self):
        res = execute_strategy("bnpl_credit", "insufficient_funds", 1, 2000.0)
        self.assertIn("outcome", res)
        self.assertEqual(res["cost"], INTERVENTION_COSTS["bnpl_credit"])

    def test_execute_strategy_dnc_flag(self):
        # Repeat executions to test execution stability
        for _ in range(20):
            res = execute_strategy("voice_outreach", "wrong_upi", 2, 500.0)
            self.assertIn(res["outcome"], ["recovered", "failed", "dnc_flagged"])

    def test_generate_hinglish_call(self):
        audio_file = generate_hinglish_call(1500.0, "bank_timeout")
        self.assertTrue(audio_file.endswith(".wav"))

if __name__ == "__main__":
    unittest.main()
