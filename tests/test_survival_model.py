import unittest
from survival_model import ARIASurvivalEngine

class DummyPayment:
    bank = "HDFC"
    past_failure_rate = 0.2
    time_of_day = 14
    pincode_tier = 2

class TestSurvivalModel(unittest.TestCase):
    def setUp(self):
        self.engine = ARIASurvivalEngine()

    def test_train_survival_model(self):
        c_index = self.engine.train()
        self.assertIsInstance(c_index, float)
        self.assertGreaterEqual(c_index, 0.5)

    def test_predict_optimal_window(self):
        payment = DummyPayment()
        res = self.engine.predict_optimal_window(payment)
        self.assertIn("optimal_retry_hours", res)
        self.assertIn("peak_hazard_rate", res)
        self.assertIn("predicted_median_t", res)
        self.assertIn("survival_curve", res)
        self.assertIsInstance(res["survival_curve"], list)
        self.assertGreater(len(res["survival_curve"]), 0)
        self.assertGreaterEqual(res["optimal_retry_hours"], 0.0)

if __name__ == "__main__":
    unittest.main()
