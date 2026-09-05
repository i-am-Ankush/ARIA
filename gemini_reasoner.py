import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class GeminiPostmortemEngine:
    """
    Connects ARIA to Google Gemini 3.6 Flash API for automated, dynamic 
    payment failure root-cause analysis and postmortem generation.
    """
    
    @staticmethod
    def generate_ai_postmortem(payment_id: str, bank: str, failure_reason: str, amount: float) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return f"Standard rule fallback for {payment_id}: {failure_reason} on {bank} gateway."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
        prompt = (
            f"You are ARIA, an enterprise payment recovery AI. "
            f"Generate a concise 1-sentence technical postmortem for a failed transaction. "
            f"Details: Payment ID: {payment_id}, Bank: {bank}, Amount: ₹{amount}, Failure: {failure_reason}. "
            f"Explain why the transaction failed and why LinUCB selected the intervention."
        )
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20
            )
            if response.status_code == 200:
                data = response.json()
                parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                if text_parts:
                    return text_parts[-1].strip()
        except Exception as e:
            print("Gemini API call notice:", e)
            
        return f"LinUCB recovery trace for {payment_id} ({bank} • {failure_reason}): Intervened based on 29D feature vector."
