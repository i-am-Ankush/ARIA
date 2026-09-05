import unittest
from generate_200_razorpay_test_payments import generate_200_payments
from generate_network_data import generate_network_dataset

class TestDataGenerators(unittest.TestCase):
    def test_generate_dataset(self):
        res = generate_200_payments()
        self.assertIsInstance(res, dict)

    def test_generate_network_dataset(self):
        df = generate_network_dataset()
        self.assertGreater(len(df), 0)
        self.assertIn("merchant_id", df.columns)
        self.assertIn("bank", df.columns)

if __name__ == "__main__":
    unittest.main()
