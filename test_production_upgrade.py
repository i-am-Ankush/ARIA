import unittest
import requests
import json
from webhook_ingestion import GatewayWebhookParser
from shadow_router import ShadowTrafficEvaluator
from tts_resilience import ProductionTTSManager

class TestProductionUpgrade(unittest.TestCase):
    
    def test_webhook_parsing(self):
        sample_rzp = {
            "account_id": "acc_enterprise_01",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_live_test_01",
                        "amount": 250000,
                        "method": "upi",
                        "bank": "HDFC",
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_description": "UPI VPA verification failed"
                    }
                }
            }
        }
        parsed = GatewayWebhookParser.parse_razorpay(sample_rzp)
        self.assertEqual(parsed["failure_reason"], "wrong_upi")
        self.assertEqual(parsed["amount"], 2500.0)

    def test_shadow_evaluator(self):
        class FakePayment:
            payment_id = "pay_shd_test"
            amount = 3500.0
            payment_method = "upi"
            bank = "HDFC"
            failure_reason = "wrong_upi"
            past_failure_rate = 0.2
            time_of_day = 14
            pincode_tier = 2

        evaluator = ShadowTrafficEvaluator()
        res = evaluator.evaluate_shadow_transaction(FakePayment())
        self.assertIn("control", res)
        self.assertIn("aria", res)
        self.assertIn("shadow_metrics", res)
        self.assertGreaterEqual(res["shadow_metrics"]["total_shadow_evaluated"], 1)

    def test_tts_resilience_manager(self):
        path = ProductionTTSManager.get_audio_path("Namaste test", "bank_timeout")
        self.assertTrue(path.endswith(".wav"))

if __name__ == "__main__":
    unittest.main()
