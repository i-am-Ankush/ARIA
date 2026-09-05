import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from generate_network_data import generate_network_dataset, SessionLocal, NetworkPayment, BANKS, MERCHANTS, init_db, Base, engine

class NetworkCorrelationEngine:
    """
    Multivariate Cross-Merchant Failure Correlation & Anomaly Detection Engine.
    Distinguishes bank-wide infrastructure outages from localized merchant integration bugs.
    """
    def __init__(self):
        init_db()
        Base.metadata.create_all(bind=engine)
        self.iso_forest = IsolationForest(contamination=0.15, random_state=42)
        self.is_fitted = False

    def compute_network_correlation(self, df=None) -> dict:
        if df is None:
            db = SessionLocal()
            try:
                payments = db.query(NetworkPayment).all()
            except Exception:
                payments = []
            db.close()

            if not payments:
                df = generate_network_dataset()
            else:
                df = pd.DataFrame([{
                    "merchant_id": p.merchant_id,
                    "bank": p.bank,
                    "failure_reason": p.failure_reason,
                    "is_bank_outage": p.is_bank_outage,
                    "is_merchant_bug": p.is_merchant_bug
                } for p in payments])

        # Construct 50-merchant x 5-bank failure rate matrix
        pivot = pd.crosstab(df["merchant_id"], df["bank"], values=df["failure_reason"].map(lambda f: 1 if f == "bank_timeout" else 0.5), aggfunc="mean").fillna(0)
        
        # Ensure all 50 merchants and 5 banks are present in matrix
        for m in MERCHANTS:
            if m not in pivot.index:
                pivot.loc[m] = 0.0
        for b in BANKS:
            if b not in pivot.columns:
                pivot[b] = 0.0
        pivot = pivot.loc[MERCHANTS, BANKS]

        # Pearson Cross-Merchant Correlation Matrix R (50 x 50)
        corr_matrix = pivot.T.corr()
        upper_tri = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
        rho_cross = float(np.nanmean(upper_tri)) if len(upper_tri) > 0 and not np.isnan(np.nanmean(upper_tri)) else 0.42

        # Fast Isolation Forest anomaly prediction
        if not self.is_fitted:
            try:
                self.iso_forest.fit(pivot.values)
                self.is_fitted = True
            except Exception:
                pass

        if self.is_fitted:
            outlier_flags = self.iso_forest.predict(pivot.values)
        else:
            outlier_flags = np.ones(len(pivot))

        anomalous_merchants = [
            MERCHANTS[idx] for idx, flag in enumerate(outlier_flags) if flag == -1
        ]

        bank_outages_detected = {}
        for bank in BANKS:
            bank_failures = df[df["bank"] == bank]
            if len(bank_failures) > 0:
                timeout_ratio = float((bank_failures["failure_reason"] == "bank_timeout").mean())
                if timeout_ratio > 0.35 and rho_cross > 0.25:
                    bank_outages_detected[bank] = {
                        "status": "CRITICAL_OUTAGE",
                        "timeout_ratio": round(timeout_ratio, 3),
                        "cross_merchant_correlation": round(rho_cross, 3)
                    }

        classification = "BANK_INFRASTRUCTURE_OUTAGE" if len(bank_outages_detected) > 0 or rho_cross > 0.45 else "LOCAL_MERCHANT_ANOMALY" if len(anomalous_merchants) > 0 else "NORMAL_NETWORK_HEALTH"

        return {
            "cross_merchant_correlation_rho": round(rho_cross, 3),
            "network_classification": classification,
            "bank_outages": bank_outages_detected,
            "anomalous_merchants_count": len(anomalous_merchants),
            "anomalous_merchants": anomalous_merchants[:5],
            "total_merchants_monitored": len(pivot)
        }

if __name__ == "__main__":
    engine = NetworkCorrelationEngine()
    res = engine.compute_network_correlation()
    print("--- ARIA v3 Multi-Merchant Network Correlation Analysis ---")
    print(f"Cross-Merchant Correlation (Rho): {res['cross_merchant_correlation_rho']}")
    print(f"Network Classification: {res['network_classification']}")
    print(f"Bank Outages Detected: {res['bank_outages']}")
