import unittest
from fastapi.testclient import TestClient
from main import app

class TestFrontendContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_metrics_schema_contract(self):
        """Verify /metrics response JSON contract required by React dashboard."""
        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        expected_keys = [
            "total_payments", "recovered", "escalated", "recovery_rate",
            "total_amount_recovered", "total_intervention_cost", "net_capital_saved",
            "roi_ratio", "c_index", "cross_merchant_correlation", "network_classification"
        ]
        for key in expected_keys:
            self.assertIn(key, data)

    def test_audit_schema_contract(self):
        """Verify /audit response list item schema."""
        res = self.client.get("/audit")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            item = data[0]
            self.assertIn("action_id", item)
            self.assertIn("payment_id", item)
            self.assertIn("strategy", item)
            self.assertIn("outcome", item)

    def test_system_status_contract(self):
        """Verify /api/v1/system-status contract."""
        res = self.client.get("/api/v1/system-status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("database_engine", data)
        self.assertIn("gateway_webhooks", data)

if __name__ == "__main__":
    unittest.main()
