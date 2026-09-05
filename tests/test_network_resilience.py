import unittest
from network_correlation import NetworkCorrelationEngine
from circuit_breaker import NetworkCircuitBreaker

class TestNetworkResilience(unittest.TestCase):
    def setUp(self):
        self.corr_engine = NetworkCorrelationEngine()
        self.breaker = NetworkCircuitBreaker()

    def test_network_correlation_computation(self):
        res = self.corr_engine.compute_network_correlation()
        self.assertIn("cross_merchant_correlation_rho", res)
        self.assertIn("network_classification", res)
        self.assertIn("bank_outages", res)
        self.assertIn("total_merchants_monitored", res)
        self.assertEqual(res["total_merchants_monitored"], 50)

    def test_circuit_breaker_trip_and_reroute(self):
        mock_analysis = {
            "bank_outages": {
                "HDFC": {"status": "CRITICAL_OUTAGE", "timeout_ratio": 0.75, "cross_merchant_correlation": 0.82}
            }
        }
        tripped = self.breaker.evaluate_and_trip(mock_analysis)
        self.assertEqual(len(tripped), 1)
        self.assertEqual(tripped[0]["degraded_bank"], "HDFC")

        rail, rerouted = self.breaker.get_rail_for_payment("HDFC")
        self.assertTrue(rerouted)
        self.assertEqual(rail, "ICICI")

        rail_normal, rerouted_normal = self.breaker.get_rail_for_payment("SBI")
        self.assertFalse(rerouted_normal)
        self.assertEqual(rail_normal, "SBI")

if __name__ == "__main__":
    unittest.main()
