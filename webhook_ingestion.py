import time
import uuid
import hashlib
from typing import Dict, Any, Optional

class GatewayWebhookParser:
    """
    Parses and normalizes live incoming Payment Gateway Webhook payloads
    (Razorpay, PayU, Cashfree) into ARIA's internal Context Vector schema x_t in R^29.
    """
    
    FAILURE_MAPPING = {
        "payment_failed": "bank_timeout",
        "bad_request_error": "wrong_upi",
        "gateway_error": "bank_timeout",
        "insufficient_funds": "insufficient_funds",
        "bank_technical_error": "bank_timeout",
        "invalid_vpa": "wrong_upi",
        "user_cancelled": "insufficient_funds",
        "wrong_pin": "wrong_upi",
        "expired_vpa": "wrong_upi",
    }

    @staticmethod
    def parse_razorpay(payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        error_code = str(entity.get("error_code", "") or "").lower()
        error_desc = str(entity.get("error_description", "") or "").lower()
        
        failure_reason = "bank_timeout"
        if "upi" in error_desc or "vpa" in error_desc or "pin" in error_desc:
            failure_reason = "wrong_upi"
        elif "balance" in error_desc or "fund" in error_desc or "insufficient" in error_desc:
            failure_reason = "insufficient_funds"
        elif error_code in GatewayWebhookParser.FAILURE_MAPPING:
            failure_reason = GatewayWebhookParser.FAILURE_MAPPING[error_code]

        raw_amount = entity.get("amount")
        amount = (float(raw_amount) / 100.0) if raw_amount is not None else 1000.0
        
        return {
            "payment_id": str(entity.get("id") or f"pay_rzp_{uuid.uuid4().hex[:8]}"),
            "merchant_id": str(payload.get("account_id") or "merchant_rzp_prod"),
            "merchant_name": "Razorpay Enterprise Merchant",
            "amount": amount,
            "payment_method": str(entity.get("method") or "upi"),
            "bank": str(entity.get("bank") or "HDFC"),
            "failure_reason": failure_reason,
            "raw_error": error_desc or error_code,
            "gateway_type": "Razorpay Live Webhook",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def parse_payu(payload: Dict[str, Any]) -> Dict[str, Any]:
        error_msg = str(payload.get("error_Message", "") or "").lower()
        failure_reason = "bank_timeout"
        if "upi" in error_msg or "vpa" in error_msg:
            failure_reason = "wrong_upi"
        elif "fund" in error_msg or "balance" in error_msg:
            failure_reason = "insufficient_funds"

        raw_amount = payload.get("amount")
        amount = float(raw_amount) if raw_amount is not None else 1500.0

        raw_bank = payload.get("bank_ref_num") or payload.get("bankcode") or "SBI"
        bank_str = str(raw_bank).upper()
        bank = bank_str if bank_str in ["HDFC", "SBI", "AXIS", "ICICI", "KOTAK"] else "SBI"

        return {
            "payment_id": str(payload.get("txnid") or f"pay_payu_{uuid.uuid4().hex[:8]}"),
            "merchant_id": str(payload.get("key") or "merchant_payu_prod"),
            "merchant_name": "PayU Enterprise Merchant",
            "amount": amount,
            "payment_method": str(payload.get("mode") or "upi").lower(),
            "bank": bank,
            "failure_reason": failure_reason,
            "raw_error": error_msg,
            "gateway_type": "PayU Live Webhook",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def parse_cashfree(payload: Dict[str, Any]) -> Dict[str, Any]:
        data = payload.get("data", {})
        payment = data.get("payment", {})
        error_details = str(payment.get("payment_failure_details", {}).get("failure_reason", "") or "").lower()
        
        failure_reason = "bank_timeout"
        if "upi" in error_details or "vpa" in error_details:
            failure_reason = "wrong_upi"
        elif "fund" in error_details or "balance" in error_details:
            failure_reason = "insufficient_funds"

        raw_amount = payment.get("payment_amount")
        amount = float(raw_amount) if raw_amount is not None else 2500.0

        raw_bank = payment.get("bank_name") or "Axis"
        bank_str = str(raw_bank).upper()
        bank = bank_str if bank_str in ["HDFC", "SBI", "AXIS", "ICICI", "KOTAK"] else "Axis"

        return {
            "payment_id": str(payment.get("cf_payment_id") or f"pay_cf_{uuid.uuid4().hex[:8]}"),
            "merchant_id": str(data.get("order", {}).get("order_id") or "merchant_cf_prod"),
            "merchant_name": "Cashfree Enterprise Merchant",
            "amount": amount,
            "payment_method": str(payment.get("payment_group") or "upi").lower(),
            "bank": bank,
            "failure_reason": failure_reason,
            "raw_error": error_details,
            "gateway_type": "Cashfree Live Webhook",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
