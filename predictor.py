import pandas as pd
import numpy as np
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sqlalchemy.orm import Session
from database import SessionLocal, Payment

_explainer = None

METHOD_MAP = {"upi": 0, "card": 1, "netbanking": 2, "wallet": 3}
BANK_MAP = {"hdfc": 0, "sbi": 1, "axis": 2, "icici": 3, "kotak": 4}

def get_method_enc(method_str):
    return METHOD_MAP.get(str(method_str or "upi").lower(), 0)

def get_bank_enc(bank_str):
    return BANK_MAP.get(str(bank_str or "hdfc").lower(), 0)

def load_training_data():
    db = SessionLocal()
    payments = db.query(Payment).all()
    db.close()

    rows = []
    for p in payments:
        amount_val = max(0.0, float(p.amount or 1000.0))
        rows.append({
            "payment_method_enc": get_method_enc(p.payment_method),
            "bank_enc":           get_bank_enc(p.bank),
            "past_failure_rate":  float(p.past_failure_rate or 0.2),
            "time_of_day":        int(p.time_of_day or 14),
            "pincode_tier":       int(p.pincode_tier or 2),
            "amount_log":         float(np.log1p(amount_val)),
        })
    return pd.DataFrame(rows)

def train_predictor():
    global _explainer
    df = load_training_data()

    if len(df) < 10:
        features = ["payment_method_enc","bank_enc","past_failure_rate","time_of_day","pincode_tier","amount_log"]
        return None, features

    np.random.seed(42)
    prob = (
        0.30 * df["past_failure_rate"] +
        0.25 * (df["time_of_day"] > 19).astype(float) +
        0.20 * (df["bank_enc"] == 0).astype(float) +
        0.15 * (df["pincode_tier"] == 3).astype(float) +
        np.random.normal(0, 0.12, len(df))
    )
    df["label"] = (prob > 0.30).astype(int)

    features = ["payment_method_enc","bank_enc","past_failure_rate",
                "time_of_day","pincode_tier","amount_log"]
    X = df[features]
    y = df["label"]

    if len(y.unique()) < 2:
        return None, features

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=60,
        max_depth=3,
        learning_rate=0.08,
        eval_metric="logloss",
        random_state=42
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"✅ Predictor trained — AUC-ROC: {auc:.3f}")

    return model, features

def get_risk_score(model, features, payment):
    amount_val = max(0.0, float(getattr(payment, "amount", 1000.0) or 1000.0))
    row = pd.DataFrame([{
        "payment_method_enc": get_method_enc(getattr(payment, "payment_method", "upi")),
        "bank_enc":           get_bank_enc(getattr(payment, "bank", "HDFC")),
        "past_failure_rate":  float(getattr(payment, "past_failure_rate", 0.2) or 0.2),
        "time_of_day":        int(getattr(payment, "time_of_day", 14) or 14),
        "pincode_tier":       int(getattr(payment, "pincode_tier", 2) or 2),
        "amount_log":         float(np.log1p(amount_val)),
    }])

    if model is not None:
        try:
            score = model.predict_proba(row)[0][1]
        except Exception:
            score = 0.65
    else:
        score = 0.65

    explanation = [
        {"feature": "past_failure_rate", "impact": round(float(payment.past_failure_rate * 0.5), 3)},
        {"feature": "time_of_day", "impact": round(float(payment.time_of_day / 24.0 * 0.3), 3)},
        {"feature": "amount_log", "impact": round(float(np.log1p(payment.amount) * 0.1), 3)}
    ]

    return round(float(score), 3), explanation

if __name__ == "__main__":
    model, features = train_predictor()
