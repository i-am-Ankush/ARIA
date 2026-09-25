import random
import requests
import os
import time
import base64
import wave
import math
import struct
from dotenv import load_dotenv

load_dotenv()

# Intervention unit costs in INR (Fintech Unit Economics)
INTERVENTION_COSTS = {
    "retry":          0.05,
    "emi_offer":      0.15,
    "voice_outreach": 0.50,
    "whatsapp_nudge": 0.20,
    "bnpl_credit":     0.10,  # Lazypay / Simpl 14-day zero-interest credit line
    "escalate":       2.00,
}

RECOVERY_PROBS = {
    "bank_timeout": {
        "retry":          0.45,
        "emi_offer":      0.30,
        "voice_outreach": 0.65,
        "whatsapp_nudge": 0.40,
        "bnpl_credit":     0.50,
        "escalate":       0.00,
    },
    "insufficient_funds": {
        "retry":          0.10,
        "emi_offer":      0.60,
        "voice_outreach": 0.50,
        "whatsapp_nudge": 0.35,
        "bnpl_credit":     0.92,  # Instant BNPL credit line conversion
        "escalate":       0.00,
    },
    "wrong_upi": {
        "retry":          0.55,
        "emi_offer":      0.15,
        "voice_outreach": 0.70,
        "whatsapp_nudge": 0.60,
        "bnpl_credit":     0.40,
        "escalate":       0.00,
    },
}

MAX_ATTEMPTS  = 3
DNC_FLAG_PROB = 0.05

import subprocess
import uuid

def generate_sample_wav(filename: str, text: str = "Namaste! Your payment failure is being processed safely by ARIA."):
    """Generates a clean synthetic spoken voice RIFF WAVE audio file if Sarvam API key is unconfigured/offline."""
    try:
        temp_aiff = filename + ".aiff"
        subprocess.run(["say", "-v", "Aman", text, "-o", temp_aiff], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if os.path.exists(temp_aiff):
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", temp_aiff, filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if os.path.exists(temp_aiff):
                os.remove(temp_aiff)
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                return
    except Exception:
        pass

    sample_rate = 8000
    duration = 1.5
    n_samples = int(sample_rate * duration)
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            value = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', value))

def generate_hinglish_call(payment_amount: float, failure_reason: str) -> str:
    """
    Generates a Hinglish TTS audio clip for the recovery call.
    Returns filename of generated audio clip.
    """
    safe_reason = os.path.basename(failure_reason)
    filename = f"aria_call_{safe_reason}.wav"
    sarvam_key = os.getenv("SARVAM_API_KEY", "")

    scripts = {
        "bank_timeout": (
            "Namaste! Aapka payment abhi process nahi hua — bank ki taraf se thodi technical dikkat aayi. "
            "Kya aap ek baar aur try karna chahenge? Yeh bilkul surakshit hai."
        ),
        "insufficient_funds": (
            "Namaste! Aapka payment complete nahi hua. Kya aap E M I ya Pay-Later option consider karna chahenge? "
            "14 days mein aasaani se pay kar sakte hain."
        ),
        "wrong_upi": (
            "Namaste! Aapka payment fail hua kyunki U P I ID verify nahi ho payi... "
            "Kya aap apna U P I ID check karke dobara try kar sakte hain? Sirf ek minute lagega."
        ),
    }

    script = scripts.get(safe_reason, scripts["bank_timeout"])
    
    from tts_resilience import ProductionTTSManager
    cached_path = ProductionTTSManager.get_audio_path(script, safe_reason)
    if os.path.exists(cached_path):
        return cached_path

    generate_sample_wav(filename, script)
    return filename

def execute_strategy(strategy: str, failure_class: str, attempt: int, amount: float = 1000.0) -> dict:
    """
    Simulates executing a recovery strategy.
    Returns outcome, reasoning trace, and intervention cost.
    """
    cost = INTERVENTION_COSTS.get(strategy, 0.20)

    # DNC check
    if random.random() < DNC_FLAG_PROB and attempt > 1:
        return {
            "outcome":         "dnc_flagged",
            "reasoning_trace": f"Customer triggered DNC flag on attempt {attempt}. "
                               f"Contact permanently stopped. Escalating to human review.",
            "success":         False,
            "force_escalate":  True,
            "audio_file":      None,
            "cost":            cost,
        }

    prob    = RECOVERY_PROBS.get(failure_class, {}).get(strategy, 0.3)
    success = random.random() < prob

    from razorpay_client import RazorpayGatewayClient
    rzp_res = {}
    if strategy == "retry":
        rzp_res = RazorpayGatewayClient.trigger_gateway_retry(f"pay_{uuid.uuid4().hex[:8]}", amount)

    audio_file = generate_hinglish_call(amount, failure_class)

    traces = {
        "retry": (
            f"Triggered automatic payment retry via Razorpay API (Order {rzp_res.get('order_id', 'live_rzp')}). "
            f"{'Bank accepted retry — payment processed.' if success else 'Bank rejected retry again.'}"
        ),
        "emi_offer": (
            f"Sent EMI conversion offer via SMS + in-app notification. "
            f"{'Customer accepted 3-month EMI plan.' if success else 'Customer did not respond to EMI offer.'}"
        ),
        "bnpl_credit": (
            f"Converted to instant Lazypay / Simpl 0-interest 14-day credit line. "
            f"{'Customer approved 1-click BNPL line — payment recovered instantly.' if success else 'Customer declined BNPL credit line.'}"
        ),
        "voice_outreach": (
            f"Initiated Hinglish voice call via Sarvam AI TTS. "
            f"Script: 'Namaste! Aapka payment process nahi hua. Kya aap retry karna chahenge?' "
            f"{'Customer confirmed retry — payment recovered.' if success else 'No answer after 3 rings.'}"
        ),
        "whatsapp_nudge": (
            f"Sent WhatsApp message with payment retry link. "
            f"{'Customer clicked link and completed payment.' if success else 'Message delivered but no action taken.'}"
        ),
        "escalate": (
            f"Routed to human recovery agent. Reason: {failure_class} "
            f"exceeded automated recovery threshold after {attempt} attempts."
        ),
    }

    return {
        "outcome":         "recovered" if success else "failed",
        "reasoning_trace": traces.get(strategy, "Strategy executed."),
        "success":         success,
        "force_escalate":  False,
        "audio_file":      audio_file,
        "cost":            cost,
    }
