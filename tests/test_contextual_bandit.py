import unittest
import numpy as np
from linucb_bandit import LinUCBBandit

class DummyPayment:
    def __init__(self, amount=2000.0, past_failure_rate=0.2, time_of_day=14, pincode_tier=2, bank="HDFC", failure_reason="insufficient_funds"):
        self.amount = amount
        self.past_failure_rate = past_failure_rate
        self.time_of_day = time_of_day
        self.pincode_tier = pincode_tier
        self.bank = bank
        self.failure_reason = failure_reason

class TestContextualBandit(unittest.TestCase):
    def setUp(self):
        self.linucb = LinUCBBandit()

    def test_feature_vector_dimension(self):
        payment = DummyPayment()
        x_t = self.linucb._extract_feature_vector(payment)
        self.assertEqual(x_t.shape, (29, 1))

    def test_linucb_select_returns_valid_arm(self):
        payment = DummyPayment()
        chosen, score, ucb_map = self.linucb.select(payment)
        self.assertIn(chosen, self.linucb.strategies)
        self.assertIsInstance(score, float)
        self.assertEqual(len(ucb_map), len(self.linucb.strategies))

    def test_linucb_update_modifies_matrices(self):
        payment = DummyPayment()
        strategy = "bnpl_credit"
        A_before = self.linucb.A[strategy].copy()
        b_before = self.linucb.b[strategy].copy()

        self.linucb.update(payment, strategy, reward=1.0)
        
        self.assertFalse(np.array_equal(self.linucb.A[strategy], A_before))
        self.assertFalse(np.array_equal(self.linucb.b[strategy], b_before))

        snapshot = self.linucb.snapshot()
        self.assertIsInstance(snapshot, dict)
        for s in self.linucb.strategies:
            self.assertIn(f"{s}_weight", snapshot)

if __name__ == "__main__":
    unittest.main()
