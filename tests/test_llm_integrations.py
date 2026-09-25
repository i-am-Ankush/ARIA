import unittest
from gemini_reasoner import GeminiPostmortemEngine
from root_cause import analyse_root_cause
from tts_resilience import ProductionTTSManager
from razorpay_client import RazorpayGatewayClient

class DummyPayment:
    amount = 5000.0
    payment_method = "upi"
    bank = "HDFC"
    time_of_day = 21
    past_failure_rate = 0.25
    pincode_tier = 1
    failure_reason = "bank_timeout"

class TestLLMIntegrations(unittest.TestCase):
    def test_gemini_postmortem_fallback(self):
        postmortem = GeminiPostmortemEngine.generate_ai_postmortem("pay_123", "HDFC", "bank_timeout", 5000.0)
        self.assertIsInstance(postmortem, str)
        self.assertGreater(len(postmortem), 0)

    def test_root_cause_analysis_fallback(self):
        res = analyse_root_cause(DummyPayment())
        self.assertIn("root_cause", res)
        self.assertIn("confidence", res)
        self.assertIn("reasoning", res)
        self.assertIn("recommended_strategy", res)

    def test_tts_resilience_manager(self):
        path = ProductionTTSManager.get_audio_path("Namaste test", "bank_timeout")
        self.assertTrue(path.endswith(".wav"))

    def test_razorpay_client_retry_fallback(self):
        res = RazorpayGatewayClient.trigger_gateway_retry("pay_rzp_test_999", 1000.0)
        self.assertIn("status", res)
        self.assertIn("message", res)

if __name__ == "__main__":
    unittest.main()
