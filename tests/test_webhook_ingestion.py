import unittest
from webhook_ingestion import GatewayWebhookParser
from shadow_router import ShadowTrafficEvaluator

class TestWebhookIngestion(unittest.TestCase):
    def test_parse_razorpay_webhook(self):
        payload = {
            "account_id": "acc_123",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_rzp_test",
                        "amount": 150000,
                        "method": "upi",
                        "bank": "HDFC",
                        "error_description": "Bank system timeout"
                    }
                }
            }
        }
        parsed = GatewayWebhookParser.parse_razorpay(payload)
        self.assertEqual(parsed["payment_id"], "pay_rzp_test")
        self.assertEqual(parsed["amount"], 1500.0)
        self.assertEqual(parsed["failure_reason"], "bank_timeout")

    def test_parse_payu_webhook(self):
        payload = {
            "txnid": "payu_tx_101",
            "amount": "2500.00",
            "mode": "UPI",
            "bank_ref_num": "HDFC",
            "error_Message": "Insufficient balance"
        }
        parsed = GatewayWebhookParser.parse_payu(payload)
        self.assertEqual(parsed["payment_id"], "payu_tx_101")
        self.assertEqual(parsed["amount"], 2500.0)
        self.assertEqual(parsed["failure_reason"], "insufficient_funds")

    def test_parse_cashfree_webhook(self):
        payload = {
            "data": {
                "order": {"order_id": "order_cf_1"},
                "payment": {
                    "cf_payment_id": "cf_pay_99",
                    "payment_amount": 3500.0,
                    "payment_group": "upi",
                    "payment_failure_details": {"failure_reason": "vpa_invalid"}
                }
            }
        }
        parsed = GatewayWebhookParser.parse_cashfree(payload)
        self.assertEqual(parsed["payment_id"], "cf_pay_99")
        self.assertEqual(parsed["amount"], 3500.0)
        self.assertEqual(parsed["failure_reason"], "wrong_upi")

    def test_shadow_evaluator(self):
        class DummyPayment:
            payment_id = "pay_shd_1"
            amount = 1000.0
            failure_reason = "bank_timeout"
            bank = "HDFC"

        evaluator = ShadowTrafficEvaluator()
        res = evaluator.evaluate_shadow_transaction(DummyPayment())
        self.assertIn("control", res)
        self.assertIn("aria", res)
        self.assertIn("shadow_metrics", res)

if __name__ == "__main__":
    unittest.main()
