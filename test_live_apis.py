import os
import sys
import time
import requests
import json
import base64
from dotenv import load_dotenv

load_dotenv()

def test_gemini_api():
    print("=" * 60)
    print("🧠 TESTING GOOGLE GEMINI 3.6 FLASH API...")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env!")
        return False
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    prompt = (
        "You are ARIA, an enterprise payment recovery AI engine. "
        "Generate a concise, 1-sentence technical postmortem for this transaction failure: "
        "Payment ID: pay_live_demo_99, Bank: HDFC, Amount: ₹5000, Failure: bank_timeout. "
        "Explain the failure cause and why LinUCB selected the automatic retry strategy."
    )
    
    start_time = time.time()
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20
        )
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            data = response.json()
            parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            result_text = text_parts[-1].strip() if text_parts else "No text generated."
            
            print(f"✅ GEMINI 3.6 FLASH RESPONSE (Latency: {latency}s):")
            print(f"   \"{result_text}\"\n")
            return True
        else:
            print(f"❌ Gemini API Error ({response.status_code}): {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Exception calling Gemini API: {e}\n")
        return False

def test_sarvam_api():
    print("=" * 60)
    print("🎙️ TESTING SARVAM AI CLOUD TTS API (bulbul:v3)...")
    print("=" * 60)
    
    sarvam_key = os.getenv("SARVAM_API_KEY", "")
    if not sarvam_key:
        print("❌ SARVAM_API_KEY not found in .env!")
        return False
        
    text = "Namaste! Aapka payment process nahi hua — bank ki taraf se thodi technical dikkat aayi. Kya aap ek baar aur try karna chahenge?"
    
    start_time = time.time()
    try:
        response = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": sarvam_key, "Content-Type": "application/json"},
            json={
                "inputs": [text],
                "target_language_code": "hi-IN",
                "speaker": "priya",
                "pace": 1.0,
                "model": "bulbul:v3"
            },
            timeout=15
        )
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            data = response.json()
            audio_b64 = data["audios"][0]
            audio_bytes = base64.b64decode(audio_b64)
            
            output_file = "audio_cache/live_test_sarvam_priya.wav"
            os.makedirs("audio_cache", exist_ok=True)
            with open(output_file, "wb") as f:
                f.write(audio_bytes)
                
            print(f"✅ SARVAM AI RESPONSE (Latency: {latency}s):")
            print(f"   Model: bulbul:v3 | Speaker: priya")
            print(f"   Saved Audio File: {output_file} ({len(audio_bytes):,} bytes, 22.05kHz RIFF WAVE)\n")
            return True
        else:
            print(f"❌ Sarvam AI Error ({response.status_code}): {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Exception calling Sarvam AI API: {e}\n")
        return False

if __name__ == "__main__":
    g_ok = test_gemini_api()
    s_ok = test_sarvam_api()
    
    print("=" * 60)
    if g_ok and s_ok:
        print("🎉 ALL LIVE API TESTS PASSED SUCCESSFULLY! Both AI engines are fully operational.")
    else:
        print("⚠️ Some API tests had issues. Review log output above.")
    print("=" * 60)
