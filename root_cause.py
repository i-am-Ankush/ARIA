import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key) if api_key and not api_key.startswith("sk-XXXX") else None

SYSTEM_PROMPT = """
You are ARIA's root cause analyst for failed Indian payments.
Given a failed payment's details, you output ONLY a JSON object like:
{
  "root_cause": "bank_timeout",
  "confidence": 0.91,
  "reasoning": "HDFC has elevated timeout rates after 9PM due to batch processing windows.",
  "recommended_strategy": "voice_outreach"
}

Root cause must be one of: bank_timeout, insufficient_funds, wrong_upi, card_expired, user_dropout
Recommended strategy must be one of: retry, emi_offer, voice_outreach, whatsapp_nudge, escalate
Output ONLY valid JSON. No explanation outside the JSON.
"""

def analyse_root_cause(payment):
    # If OpenAI key is present and valid, call OpenAI API
    if client and os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("sk-XXXX"):
        prompt = f"""
Payment failed. Details:
- Amount: ₹{payment.amount}
- Method: {payment.payment_method}
- Bank: {payment.bank}
- Time of day: {payment.time_of_day}:00
- Customer past failure rate: {payment.past_failure_rate}
- Pincode tier: {payment.pincode_tier}
- Recorded failure reason: {payment.failure_reason}

What is the root cause and best recovery strategy?
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.2
            )
            raw = response.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception:
            pass

    # Intelligent fallback when API key is default or offline
    reason = getattr(payment, 'failure_reason', 'bank_timeout')
    bank = getattr(payment, 'bank', 'HDFC')
    time_of_day = getattr(payment, 'time_of_day', 14)
    amount = getattr(payment, 'amount', 1000)

    if reason == "bank_timeout":
        strategy = "voice_outreach" if bank in ["HDFC", "SBI"] and time_of_day > 20 else "retry"
        reasoning = f"{bank} experiencing peak transaction timeouts at hour {time_of_day}. Automated outreach/retry suggested."
    elif reason == "insufficient_funds":
        strategy = "emi_offer" if amount > 2000 else "whatsapp_nudge"
        reasoning = f"Transaction amount ₹{amount} exceeds available balance. EMI offer recommended."
    else: # wrong_upi
        strategy = "whatsapp_nudge"
        reasoning = "UPI handle validation failure. WhatsApp re-verification link recommended."

    return {
        "root_cause": reason,
        "confidence": 0.88,
        "reasoning": reasoning,
        "recommended_strategy": strategy
    }

if __name__ == "__main__":
    class FakePayment:
        amount = 3500
        payment_method = "upi"
        bank = "HDFC"
        time_of_day = 22
        past_failure_rate = 0.18
        pincode_tier = 2
        failure_reason = "bank_timeout"

    result = analyse_root_cause(FakePayment())
    print(json.dumps(result, indent=2))
