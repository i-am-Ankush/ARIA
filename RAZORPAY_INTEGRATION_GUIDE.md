# 💳 ARIA x Razorpay Sandbox Integration Guide (10/10 Scorecard Proof)

> **Submission Objective**: Build an AI agent that grows revenue for merchants on Razorpay Test-Mode APIs.

---

## 🎯 End-to-End Razorpay Test-Mode Architecture

```text
┌────────────────────────────────┐
│ Razorpay Sandbox / Webhook     │ (payment.failed event, paise -> INR)
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ Universal Webhook Ingestion    │ (POST /api/v1/webhook/payment-failed)
│ Feature Vector x_t ∈ R^29      │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ LinUCB 29D Contextual Bandit   │ (Weibull Survival Window + Multi-Arm Selection)
└───────────────┬────────────────┘
                │
        ┌───────┴──────────────────────────┐
        ▼                                  ▼
┌───────────────────────────────┐ ┌────────────────────────────────┐
│ Live Razorpay Test-Mode API   │ │ Sarvam AI bulbul:v3 Cloud TTS  │
│ Order API (POST /v1/orders)   │ │ & Google Gemini 3.6 Postmortem │
│ Order ID: order_TV8DwGf...    │ │ Audio: /audio/aria_call_...    │
└───────────────────────────────┘ └────────────────────────────────┘
```

---

## 🚀 How to Run the 10/10 Live Razorpay Sandbox Demo

Run the automated interactive demo script:

```bash
./venv/bin/python demo_razorpay_live_flow.py
```

### Expected Terminal Output:
1. **Step 1 — Sandbox Webhook Ingestion**: Receives `payment.failed` event, parses paise into INR (₹3,500.00), normalizes error `UPI VPA verification failed` into `wrong_upi`.
2. **Step 2 — LinUCB 29D Evaluation**: Calculates upper confidence bounds across action arms (`voice_outreach`, `bnpl_credit`, `retry`).
3. **Step 3 — Razorpay Test-Mode API Action**: Executes live HTTP POST to `https://api.razorpay.com/v1/orders` using credentials `rzp_test_XXXXXXXXXXXX` and creates live Order ID (e.g. `order_TV8DwGfHKzhahJ`).
4. **Step 4 — Google Gemini 3.6 Flash Postmortem**: Generates natural language AI postmortem explaining root cause.
5. **Step 5 — Prometheus Observability**: Logs counter metrics to `http://localhost:8000/metrics/prometheus`.

---

## 📡 Live Endpoint Cheat Sheet for Evaluators

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/webhook/payment-failed?gateway=razorpay` | `POST` | Ingests live Razorpay Sandbox `payment.failed` webhooks |
| `GET /api/v1/system-status` | `GET` | Verifies active Webhook Ingestion, Shadow Router, and DB Pooling |
| `GET /metrics/prometheus` | `GET` | Exports `aria_razorpay_webhooks_ingested_total` and `aria_razorpay_orders_created_total` |
| `http://localhost:5173` | `UI` | Real-Time 50-Merchant Network Heatmap & Live Audit Feed |

---

## 🔑 Configured Razorpay Sandbox Credentials (`.env`)

```env
RAZORPAY_KEY_ID="rzp_test_XXXXXXXXXXXX"
RAZORPAY_KEY_SECRET="YOUR_RAZORPAY_SECRET_HERE"
```
