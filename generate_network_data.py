import random
import uuid
import pandas as pd
import numpy as np
from database import SessionLocal, init_db, Base, engine
from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime

class NetworkPayment(Base):
    __tablename__ = "network_payments"
    payment_id        = Column(String, primary_key=True)
    merchant_id       = Column(String)
    merchant_name     = Column(String)
    amount            = Column(Float)
    payment_method    = Column(String)
    bank              = Column(String)
    failure_reason    = Column(String)
    is_bank_outage    = Column(Integer, default=0) # 1 if caused by bank-wide infrastructure outage
    is_merchant_bug   = Column(Integer, default=0) # 1 if localized merchant-specific bug
    status            = Column(String, default="pending")
    created_at        = Column(DateTime, default=datetime.utcnow)

MERCHANTS = [f"merchant_{i:02d}" for i in range(1, 51)]
MERCHANT_NAMES = [
    "Zomato", "Swiggy", "Flipkart", "Nykaa", "BookMyShow", "MakeMyTrip", "Uber", "Ola",
    "Zepto", "Blinkit", "Dunzo", "BigBasket", "Myntra", "Ajio", "TataCliq", "UrbanCompany",
    "RazorpayX", "CRED", "PhonePe", "Paytm", "PolicyBazaar", "Groww", "Zerodha", "Upstox",
    "CultFit", "Lenskart", "FirstCry", "NykaaMan", "Mamaearth", "SugarCosmetics", "Boat",
    "Noise", "FireBoltt", "Minimalist", "PlumGoodness", "Beardo", "BombayShavingCo", "Wakefit",
    "Pepperfry", "UrbanLadder", "ClearTrip", "EaseMyTrip", "AbhiBus", "RedBus", "Rapido",
    "Drivezy", "Zoomcar", "ChaiPoint", "BlueTokai", "ThirdWaveCoffee"
]

BANKS           = ["HDFC", "SBI", "Axis", "ICICI", "Kotak"]
METHODS         = ["upi", "card", "netbanking", "wallet"]
FAILURE_REASONS = ["bank_timeout", "insufficient_funds", "wrong_upi"]

def generate_network_dataset(n_per_merchant=10):
    init_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    db.query(NetworkPayment).delete()
    db.commit()

    rows = []
    np.random.seed(42)
    
    total_records = len(MERCHANTS) * n_per_merchant
    print(f"Generating multi-merchant network telemetry across {len(MERCHANTS)} merchants ({total_records} payments)...")

    for m_idx, m_id in enumerate(MERCHANTS):
        m_name = MERCHANT_NAMES[m_idx]
        
        # Localized bug injected for merchant_12 and merchant-[#28]
        has_local_bug = (m_id in ["merchant_12", "merchant_28"])

        for i in range(n_per_merchant):
            bank = random.choice(BANKS)
            method = random.choice(METHODS)
            amount = round(random.uniform(300, 45000), 2)

            # Ingest bank-wide HDFC outage simulation flag
            is_hdfc_outage = (bank == "HDFC" and random.random() < 0.70)
            is_local_bug   = (has_local_bug and random.random() < 0.60)

            if is_hdfc_outage:
                failure = "bank_timeout"
            elif is_local_bug:
                failure = "wrong_upi"
            else:
                failure = random.choices(FAILURE_REASONS, [0.50, 0.30, 0.20])[0]

            p = NetworkPayment(
                payment_id        = f"pay_net_{uuid.uuid4().hex[:10]}",
                merchant_id       = m_id,
                merchant_name     = m_name,
                amount            = amount,
                payment_method    = method,
                bank              = bank,
                failure_reason    = failure,
                is_bank_outage    = 1 if is_hdfc_outage else 0,
                is_merchant_bug   = 1 if is_local_bug else 0,
                status            = "pending"
            )
            db.add(p)
            rows.append({
                "payment_id": p.payment_id,
                "merchant_id": m_id,
                "merchant_name": m_name,
                "amount": amount,
                "bank": bank,
                "payment_method": method,
                "failure_reason": failure,
                "is_bank_outage": p.is_bank_outage,
                "is_merchant_bug": p.is_merchant_bug
            })

    db.commit()
    db.close()
    print(f"✅ Generated multi-merchant dataset for 50 network nodes")
    return pd.DataFrame(rows)

if __name__ == "__main__":
    generate_network_dataset()
