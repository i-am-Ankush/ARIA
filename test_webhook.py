import requests
import hmac
import hashlib
import json

SECRET = "rzp_test_secret_12345"
URL = "http://localhost:8000/webhook/razorpay"

# Sample realistic Razorpay payment.failed payload
payload = {
    "entity": "event",
    "account_id": "acc_BF0Fg2ZIG213",
    "event": "payment.failed",
    "contains": ["payment"],
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_K3l4m5n6o7p8",
                "amount": 250000,
                "currency": "INR",
                "status": "failed",
                "order_id": "order_K3l4m5n6o7p8",
                "method": "upi",
                "bank": "HDFC",
                "contact": "+919876543210",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Bank system timeout occurred during transaction authorization"
            }
        }
    }
}

body_bytes = json.dumps(payload).encode("utf-8")

# Generate valid HMAC-SHA256 signature
valid_signature = hmac.new(
    SECRET.encode("utf-8"),
    body_bytes,
    hashlib.sha256
).hexdigest()

print("--- TEST 1: Valid Razorpay HMAC Signature ---")
headers = {
    "Content-Type": "application/json",
    "X-Razorpay-Signature": valid_signature
}

try:
    res = requests.post(URL, data=body_bytes, headers=headers, timeout=5)
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.json()}")
except Exception as e:
    print(f"Server not running or connection error: {e}")

print("\n--- TEST 2: Invalid Razorpay HMAC Signature ---")
bad_headers = {
    "Content-Type": "application/json",
    "X-Razorpay-Signature": "invalid_signature_12345"
}

try:
    res = requests.post(URL, data=body_bytes, headers=bad_headers, timeout=5)
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.json()}")
except Exception as e:
    print(f"Server not running or connection error: {e}")
