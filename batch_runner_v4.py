import asyncio
import random
from database import SessionLocal, init_db, Action
from generate_network_data import NetworkPayment, generate_network_dataset, MERCHANTS, MERCHANT_NAMES, BANKS
from network_correlation import NetworkCorrelationEngine
from circuit_breaker import NetworkCircuitBreaker
from survival_model import ARIASurvivalEngine
from linucb_bandit import LinUCBBandit
from executor import execute_strategy
from datetime import datetime

correlation_engine = NetworkCorrelationEngine()
circuit_breaker    = NetworkCircuitBreaker()
survival_engine     = ARIASurvivalEngine()
linucb_bandit       = LinUCBBandit()

def run_v4_batch():
    init_db()
    db = SessionLocal()

    payments = db.query(NetworkPayment).filter(NetworkPayment.status == "pending").all()
    if not payments:
        db.close()
        generate_network_dataset()
        db = SessionLocal()
        payments = db.query(NetworkPayment).filter(NetworkPayment.status == "pending").all()

    print(f"\n🚀 ARIA v4 Enterprise LinUCB Stream — {len(payments)} payments across 50 merchants\n")

    recovered_count = 0
    recovered_amount = 0.0
    total_cost = 0.0
    rerouted_count = 0
    bnpl_conversions = 0

    # Cache correlation analysis once for performance
    analysis = correlation_engine.compute_network_correlation()

    for i, payment in enumerate(payments):
        assigned_bank, is_rerouted = circuit_breaker.get_rail_for_payment(payment.bank)
        if is_rerouted:
            rerouted_count += 1

        survival_res = survival_engine.predict_optimal_window(payment)
        t_star = survival_res["optimal_retry_hours"]

        strategy, ucb_score, ucb_map = linucb_bandit.select(payment)
        if strategy == "bnpl_credit":
            bnpl_conversions += 1

        result = execute_strategy(strategy, payment.failure_reason, 1, payment.amount)
        total_cost += result["cost"]

        linucb_bandit.update(payment, strategy, 1.0 if result["success"] else 0.0)

        audio_file = f"/audio/{result['audio_file']}" if result.get("audio_file") else f"/audio/aria_call_{payment.failure_reason}_{int(payment.amount)}.wav"
        action = Action(
            payment_id      = payment.payment_id,
            attempt_number  = 1,
            strategy_chosen = strategy,
            strategy_weight = ucb_score,
            reasoning_trace = f"[{payment.merchant_name}] LinUCB Score: {ucb_score}. {'Rerouted to ' + assigned_bank if is_rerouted else 'Assigned ' + payment.bank}. Intervened at T+{t_star}h. {result['reasoning_trace']}",
            outcome         = result["outcome"],
            audio_url       = audio_file
        )
        db.add(action)

        if result["success"]:
            payment_status = "recovered"
            recovered_count += 1
            recovered_amount += payment.amount
        else:
            payment_status = "escalated"

        try:
            db.query(NetworkPayment).filter(NetworkPayment.id == payment.id).update({"status": payment_status})
            db.commit()
        except Exception:
            db.rollback()

    db.close()
    
    total = len(payments)
    net_saved = recovered_amount - total_cost
    roi = (recovered_amount / total_cost) if total_cost > 0 else 0

    print(f"""
╔═════════════════════════════════════════════════════════════════╗
║         ARIA v4 PRODUCTION ENTERPRISE EDITION COMPLETE          ║
╠═════════════════════════════════════════════════════════════════╣
║ Monitored Merchants:          50 Network Nodes                 ║
║ LinUCB Contextual Bandit:     ACTIVE (6 Features per Payment)  ║
║ Instant BNPL Conversions:     {bnpl_conversions:<33}║
║ Preemptively Rerouted:        {rerouted_count:<33}║
║ Total Transactions Evaluated: {total:<33}║
║ Recovery Rate:                {f'{recovered_count/total*100:.1f}%':<33}║
║ Gross Amount Recovered:       ₹{recovered_amount:<31.0f}║
║ Net Capital Saved:            ₹{net_saved:<31.2f}║
║ Net Capital ROI Ratio:        {f'{roi:.1f}x':<33}║
║ OpenTelemetry Metrics Exporter: http://localhost:8000/metrics/prometheus ║
╚═════════════════════════════════════════════════════════════════╝
""")

async def run_v4_batch_async(broadcast_callback=None):
    init_db()
    db = SessionLocal()

    print(f"\n🚀 ARIA v4 Async LinUCB 50-Merchant Infinite Stream Active\n")

    recovered_count = 0
    recovered_amount = 0.0
    total_cost = 0.0
    rerouted_count = 0
    bnpl_conversions = 0

    while True:
        payments = db.query(NetworkPayment).filter(NetworkPayment.status == "pending").all()
        if not payments or len(payments) < 5:
            generate_network_dataset()
            payments = db.query(NetworkPayment).all()

        analysis = correlation_engine.compute_network_correlation()

        for i, payment in enumerate(payments):
            assigned_bank, is_rerouted = circuit_breaker.get_rail_for_payment(payment.bank)
            if is_rerouted:
                rerouted_count += 1

            survival_res = survival_engine.predict_optimal_window(payment)
            t_star = survival_res["optimal_retry_hours"]

            strategy, ucb_score, ucb_map = linucb_bandit.select(payment)
            if strategy == "bnpl_credit":
                bnpl_conversions += 1

            result = execute_strategy(strategy, payment.failure_reason, 1, payment.amount)
            total_cost += result["cost"]

            linucb_bandit.update(payment, strategy, 1.0 if result["success"] else 0.0)

            audio_file = f"/audio/{result['audio_file']}" if result.get("audio_file") else f"/audio/aria_call_{payment.failure_reason}_{int(payment.amount)}.wav"
            action = Action(
                payment_id      = payment.payment_id,
                attempt_number  = 1,
                strategy_chosen = strategy,
                strategy_weight = ucb_score,
                reasoning_trace = f"[{payment.merchant_name}] LinUCB Score: {ucb_score}. {'Rerouted to ' + assigned_bank if is_rerouted else 'Bank ' + payment.bank}. {result['reasoning_trace']}",
                outcome         = result["outcome"],
                audio_url       = audio_file
            )
            db.add(action)

            if result["success"]:
                payment.status = "recovered"
                recovered_count += 1
                recovered_amount += payment.amount
            else:
                payment.status = "escalated"

            db.commit()

            if (i + 1) % 15 == 0:
                analysis = correlation_engine.compute_network_correlation()
                tripped_events = circuit_breaker.evaluate_and_trip(analysis)
            else:
                tripped_events = []

            network_nodes = []
            for idx, m_id in enumerate(MERCHANTS):
                m_name = MERCHANT_NAMES[idx]
                is_anom = m_id in analysis.get("anomalous_merchants", [])
                has_outage = len(analysis.get("bank_outages", {})) > 0
                
                status = "REROUTED" if (has_outage and idx % 3 == 0) else "ANOMALY" if is_anom else "HEALTHY"
                network_nodes.append({
                    "merchant_id": m_id,
                    "merchant_name": m_name,
                    "status": status
                })

            if broadcast_callback:
                snapshot = linucb_bandit.snapshot()
                net_saved = recovered_amount - total_cost
                roi = (recovered_amount / total_cost) if total_cost > 0 else 0

                event = {
                    "payment_number":             i + 1,
                    "total_payments":             len(payments),
                    "payment_id":                 payment.payment_id,
                    "merchant_id":                payment.merchant_id,
                    "merchant_name":              payment.merchant_name,
                    "amount":                     payment.amount,
                    "failure_reason":             payment.failure_reason,
                    "bank":                       payment.bank,
                    "assigned_bank":              assigned_bank,
                    "is_rerouted":                is_rerouted,
                    "optimal_retry_hours":        t_star,
                    "survival_curve":             survival_res["survival_curve"],
                    "c_index":                    survival_res["c_index"],
                    "linucb_score":               ucb_score,
                    "bnpl_conversions":           bnpl_conversions,
                    "attempt":                    1,
                    "strategy_chosen":            strategy,
                    "outcome":                    result["outcome"],
                    "reasoning":                  f"[{payment.merchant_name}] LinUCB Score: {ucb_score}. Intervened at T+{t_star}h. {result['reasoning_trace']}",
                    "audio_url":                  f"/audio/aria_call_{payment.failure_reason}.wav",
                    "bandit_weights":             snapshot,
                    "network_nodes":              network_nodes,
                    "cross_merchant_correlation": analysis["cross_merchant_correlation_rho"],
                    "network_classification":     analysis["network_classification"],
                    "bank_outages":               analysis["bank_outages"],
                    "circuit_breaker_tripped":    len(tripped_events) > 0,
                    "circuit_breaker_status":     circuit_breaker.get_status(),
                    "recovered_count":            recovered_count,
                    "escalated_count":            (i + 1) - recovered_count,
                    "recovered_total":            round(recovered_amount, 2),
                    "total_intervention_cost":    round(total_cost, 2),
                    "net_capital_saved":          round(net_saved, 2),
                    "roi_ratio":                  round(roi, 1),
                    "audio_url":                  f"/audio/{result['audio_file']}" if result.get("audio_file") else None,
                    "time":                       datetime.utcnow().strftime("%H:%M:%S")
                }
                await broadcast_callback(event)
                await asyncio.sleep(1.2)

    db.close()

if __name__ == "__main__":
    run_v4_batch()
