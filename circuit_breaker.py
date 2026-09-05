import threading
from generate_network_data import BANKS

class NetworkCircuitBreaker:
    """
    Coordinated Multi-Merchant Circuit Breaker & Payment Rail Rerouting Engine.
    Prevents cross-merchant cascading failures by switching payment rails when bank outages are detected.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.breakers = {
            bank: {
                "state": "CLOSED",
                "trip_count": 0,
                "alternate_rail": "ICICI" if bank != "ICICI" else "SBI"
            }
            for bank in BANKS
        }

    def evaluate_and_trip(self, network_analysis: dict) -> list:
        tripped_events = []
        bank_outages = network_analysis.get("bank_outages", {})

        with self.lock:
            for bank, info in bank_outages.items():
                if bank in self.breakers and self.breakers[bank]["state"] != "TRIPPED":
                    self.breakers[bank]["state"] = "TRIPPED"
                    self.breakers[bank]["trip_count"] += 1
                    alt_rail = self.breakers[bank]["alternate_rail"]
                    
                    event = {
                        "event": "CIRCUIT_BREAKER_TRIPPED",
                        "degraded_bank": bank,
                        "cross_merchant_correlation": info.get("cross_merchant_correlation", 0.8),
                        "action": f"Auto-rerouted all 50 merchants from {bank} to {alt_rail} alternate rail",
                        "alternate_rail": alt_rail,
                        "affected_merchants_count": 50
                    }
                    tripped_events.append(event)
                    print(f"🚨 CIRCUIT BREAKER TRIPPED for {bank}! Rerouting all 50 merchants to {alt_rail}.")

        return tripped_events

    def reset_breaker(self, bank: str):
        with self.lock:
            if bank in self.breakers:
                self.breakers[bank]["state"] = "CLOSED"

    def get_rail_for_payment(self, requested_bank: str) -> tuple[str, bool]:
        with self.lock:
            if requested_bank in self.breakers and self.breakers[requested_bank]["state"] == "TRIPPED":
                alt_rail = self.breakers[requested_bank]["alternate_rail"]
                # Check if alternate rail is also tripped
                if self.breakers.get(alt_rail, {}).get("state") == "TRIPPED":
                    alt_rail = "Axis" if requested_bank != "Axis" else "SBI"
                return alt_rail, True
            return requested_bank, False

    def get_status(self) -> dict:
        with self.lock:
            return dict(self.breakers)

if __name__ == "__main__":
    cb = NetworkCircuitBreaker()
    mock_analysis = {
        "bank_outages": {
            "HDFC": {"status": "CRITICAL_OUTAGE", "timeout_ratio": 0.75, "cross_merchant_correlation": 0.82}
        }
    }
    events = cb.evaluate_and_trip(mock_analysis)
    print("Circuit Breaker Status:", cb.get_status())
