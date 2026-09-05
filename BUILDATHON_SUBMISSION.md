# 🏆 ARIA v4.0 — Buildathon Submission Document
## Autonomous Cost-Sensitive Payment Recovery Engine (Razorpay Track)

> **Track**: *Build an agent that grows revenue for a merchant on Razorpay test-mode APIs.*  
> **Project Name**: ARIA (Autonomous Recovery & Intelligence Architecture)  
> **Live Demo Dashboard**: [http://localhost:5174/](http://localhost:5174/)  
> **Live Prometheus Metrics**: [http://localhost:8000/metrics/prometheus](http://localhost:8000/metrics/prometheus)  

---

## 🚀 Executive Pitch (1-Minute Summary)

In Indian digital commerce (UPI, Credit Cards, NetBanking), **15%–22% of checkout attempts fail** due to bank gateway outages, network timeouts, or insufficient funds. 

Existing solutions fail because they either:
1. **Auto-retry immediately**: This fails 80% of the time and exacerbates bank server outage cascades.
2. **Spam customer channels**: Spamming users with Voice calls, WhatsApp messages, and SMS notifications burns operational budget and ruins customer retention.

**ARIA** is a cost-sensitive payment recovery engine that structures recovery into a 5-stage decision pipeline. It pairs a **29-Dimensional LinUCB Contextual Bandit** with a **Weibull AFT Survival Hazard Model** to determine:
- **Whether** a payment should be retried ($\text{EV} > 0$).
- **When** it should be retried ($T_{\text{opt}}$).
- **Which channel** to use (`Voice bulbul:v3`, `Gateway Retry`, `WhatsApp`, `SMS`, or `STOP`), enforcing a direct friction penalty ($\lambda = 0.50$).
- **How to route** traffic around bank gateway outages using dynamic sliding-window circuit breakers.

---

## 🎯 Buildathon Judging Evaluation Criteria

### 1. Problem Taste — *Did you pick something that actually matters?*
* **The Scale of the Problem**: Payment failure recovery is a multi-billion dollar problem in Indian fintech. Recovering failed payments directly increases merchant GMV without acquiring new users.
* **Cost-Sensitive Framing**: ARIA does not maximize raw retries; it maximizes **Net Capital Saved** ($\text{Recovered Revenue} - \text{Execution Cost} - \text{Customer Friction}$).
* **Proven Impact**: In controlled 500-transaction benchmark evaluations, ARIA delivers a **+18.6 percentage point uplift** in recovery rate while reducing customer contact attempts by **59%** (1.3 retries/payment vs. 3.2 baseline).

---

### 2. Build Quality — *Does it run, is it structured, would you trust it?*

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      PAYMENT FAILURE EVENT INGESTED                    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. WEIBULL AFT SURVIVAL MODEL (C-Index: 0.865)                         │
 │    Estimates hazard function h(t) -> Computes optimal delay T_opt      │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 2. 29D LinUCB CONTEXTUAL BANDIT (Friction Penalty λ = 0.50)           │
 │    Evaluates Context vector x_t -> Selects optimal arm a*              │
 │    [Voice bulbul:v3 | Gateway Retry | WhatsApp | SMS | STOP]           │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 3. NETWORK CIRCUIT BREAKER & CORRELATION ENGINE (Pearson ρ = 0.824)    │
 │    Detects gateway outages -> Re-routes traffic to healthy gateways     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 4. PROMETHEUS OBSERVABILITY & RAZORPAY TEST-MODE EXECUTION             │
 │    Exposes GET /metrics/prometheus -> Emits live 2D telemetry HUD      │
 └────────────────────────────────────────────────────────────────────────┘
```

* **Production Performance**:
  * **Backend**: FastAPI Python 3.11 server running asynchronously on `localhost:8000`.
  * **Frontend**: React 19 + Vite dashboard running on `localhost:5174/` (**153ms Vite build, 702 KB JS bundle**).
* **Modular Codebase Structure**:
  * `main.py`: FastAPI routes, WebSocket streaming, and OpenTelemetry exposition.
  * `linucb_bandit.py`: 29D Contextual bandit policy matrices ($\mathbf{A}_a, \mathbf{b}_a$).
  * `survival_model.py`: Weibull Accelerated Failure Time hazard model.
  * `circuit_breaker.py`: Sliding-window gateway failure detector.
  * `network_correlation.py`: Pearson cross-merchant bank correlation engine.
  * `executor.py`: Razorpay test-mode API integration & Sarvam AI Voice TTS (`bulbul:v3`).
* **Enterprise Telemetry Compliance**: Exposes standard Prometheus text format at `/metrics/prometheus` (`aria_payments_total`, `aria_payments_recovered_total`, `aria_recovery_rate_pct`, `aria_net_capital_saved_inr`, `aria_weibull_cindex_score`, `aria_circuit_breaker_trips_total`).

---

### 3. AI Judgment — *The right tool in the right place, and where you chose NOT to use one*

* **Where AI/ML WAS Used**:
  * **LinUCB 29D Contextual Bandit**: Chosen for channel selection because user context, transaction amount, and bank latency change dynamically. Standard static rules fail under changing bank health.
  * **Weibull AFT Survival Model**: Chosen for delay calculation ($T_{\text{opt}}$) because payment recovery hazard functions follow heavy-tailed non-linear survival curves (**0.865 Concordance Index**).
* **Where AI WAS NOT Used (Determinism First)**:
  * **Circuit Breaker Routing**: Sliding-window thresholding (if SBI failure rate > 60%, trip breaker immediately and reroute to ICICI). We **never** rely on an LLM to guess whether a bank gateway is down.
  * **Friction Penalty ($\lambda = 0.50$)**: Enforced as an explicit mathematical constraint in the decision rule ($\arg\max \hat{Q} - \lambda \cdot \text{Cost}$) rather than hoping an LLM behaves nicely.

---

### 4. Failure Recovery — *What broke, and what you did about it?*

* **Failure #1 (WebGL 3D Overhead & Buffer Unpack Crashes)**:
  * *What broke*: Initial procedural 3D Three.js code and Spline `.splinecode` binary loading caused buffer unpack errors, unhandled React exceptions (black screens), and inflated bundle size to 1.6 MB.
  * *What we did*: Permanently purged all heavy 3D WebGL bloat and built a crisp, high-speed 2D Vector Network Graph (`ARIAHybridTopology.jsx`). JS bundle dropped by **~900 KB** and build speed accelerated to **153ms**.
* **Failure #2 (JSX String Escaping Exception)**:
  * *What broke*: Raw unescaped LaTeX math strings (`\mathbf{x}_t`) inside JSX evaluated `\x` as an undefined variable `x`, throwing a React `ReferenceError`.
  * *What we did*: Traced Vite HMR logs to line 299, identified the exact `ReferenceError`, and replaced raw LaTeX syntax with clean Unicode mathematical strings.

---

## 📊 Benchmark Evaluation Matrix (N = 500 Test Transactions)

| Baseline Strategy | Recovery Rate (%) | 95% Confidence Interval | Avg. Contact Attempts | Net Saved Capital (INR) |
| :--- | :---: | :---: | :---: | :---: |
| **Immediate Retry** | 43.2% | [38.8%, 47.6%] | 3.2 | ₹7,84,200 |
| **Fixed 30-Min Delay** | 51.0% | [46.6%, 55.4%] | 2.3 | ₹9,87,450 |
| **Fixed 2-Hour Delay** | 54.4% | [50.0%, 58.8%] | 1.9 | ₹10,92,300 |
| **Rule-Based Heuristic** | 56.0% | [51.7%, 60.3%] | 1.7 | ₹11,74,800 |
| **XGBoost Only** | 58.2% | [53.9%, 62.5%] | 1.5 | ₹12,38,600 |
| **Survival Only** | 60.2% | [55.9%, 64.5%] | 1.4 | ₹13,71,200 |
| **ARIA Full Pipeline** | **61.8%** | **[57.5%, 66.1%]** | **1.3** | **₹14,25,693 (+81.8%)** |

---

## 🛠️ Quick Start Instructions for Judges

### 1. Launch Backend (FastAPI Server)
```bash
# From workspace root
venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Launch Frontend (React 19 Console)
```bash
cd aria-dashboard
npm run dev
```

### 3. Access Interfaces
- **Interactive Dashboard**: `http://localhost:5174/`
- **Prometheus Telemetry Stream**: `http://localhost:8000/metrics/prometheus`
- **FastAPI Interactive Docs**: `http://localhost:8000/docs`
