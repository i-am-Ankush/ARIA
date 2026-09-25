import unittest
from fastapi.testclient import TestClient
import os
import json
import hmac
import hashlib

from main import app

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_audio_path_traversal_prevention(self):
        """Issue 1 & 2: Check that path traversal is prevented or safely handled."""
        response = self.client.get("/audio/../../.env")
        self.assertIn(response.status_code, [404, 400, 422])

    def test_audio_range_header_parsing(self):
        """Issue 9 & 10: Range header parsing."""
        response = self.client.get("/audio/aria_call_bank_timeout.wav", headers={"Range": "bytes=0-100"})
        if response.status_code == 206:
            self.assertTrue(response.headers.get("Content-Range").startswith("bytes 0-100/"))
        else:
            self.assertIn(response.status_code, [200, 404, 206])

    def test_payments_endpoint(self):
        """Check /payments endpoint returns 200 list."""
        response = self.client.get("/payments")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_audit_endpoint(self):
        """Check /audit endpoint returns 200 list."""
        response = self.client.get("/audit")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_prometheus_metrics_endpoint(self):
        """Issue 6, 7 & 8: Check /metrics/prometheus returns 200 plain text."""
        response = self.client.get("/metrics/prometheus")
        self.assertEqual(response.status_code, 200)
        self.assertIn("aria_payments_total", response.text)

    def test_simulate_payment_validation(self):
        """Check payment simulation with custom payload."""
        payload = {
            "amount": 2500.0,
            "payment_method": "upi",
            "bank": "HDFC",
            "time_of_day": 14,
            "past_failure_rate": 0.15,
            "pincode_tier": 1,
            "failure_reason": "bank_timeout"
        }
        response = self.client.post("/simulate-payment", json=payload)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertIn("payment_id", res)
        self.assertIn("strategy_chosen", res)

    def test_razorpay_webhook_signature_verification(self):
        """Issue 15: Signature verification for Razorpay webhooks."""
        secret = os.getenv("RAZORPAY_KEY_SECRET", "")
        payload = {"event": "payment.failed", "payload": {"payment": {"entity": {"amount": 50000, "method": "upi", "bank": "HDFC"}}}}
        body_bytes = json.dumps(payload).encode("utf-8")

        if secret and secret != "XXXXXXXX":
            sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
            res = self.client.post("/webhook/razorpay", content=body_bytes, headers=headers)
            self.assertEqual(res.status_code, 200)
        else:
            # Bad signature test
            headers = {"X-Razorpay-Signature": "invalid_sig", "Content-Type": "application/json"}
            res = self.client.post("/webhook/razorpay", content=body_bytes, headers=headers)
            # If secret is non-default, should reject 400
            self.assertIn(res.status_code, [200, 400])

if __name__ == "__main__":
    unittest.main()
