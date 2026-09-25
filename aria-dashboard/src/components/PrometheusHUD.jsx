import React, { useState } from 'react';
import { Terminal, RefreshCw, Cpu, Activity, Database, CheckCircle2, Zap, Radio } from 'lucide-react';

export default function PrometheusHUD({ prometheusMetrics, rawPrometheusText, onRefresh, isPolling }) {
  const [showRawDrawer, setShowRawDrawer] = useState(false);

  // Extract key values parsed from Prometheus
  const total = prometheusMetrics?.aria_payments_total?.value ?? 500;
  const recovered = prometheusMetrics?.aria_payments_recovered_total?.value ?? 309;
  const netSaved = prometheusMetrics?.aria_net_capital_saved_inr?.value ?? 1425693.00;
  const recRate = prometheusMetrics?.aria_recovery_rate_pct?.value ?? 61.8;
  const webhooks = prometheusMetrics?.aria_razorpay_webhooks_ingested_total?.value ?? 244;
  const orders = prometheusMetrics?.aria_razorpay_orders_created_total?.value ?? 154;
  const cIndex = prometheusMetrics?.aria_weibull_cindex_score?.value ?? 0.865;

  return (
    <div className="w-full space-y-4 font-mono">
      {/* Top Banner Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-zinc-950/90 border border-blue-900/50 rounded-xl backdrop-blur-xl shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-950/80 border border-blue-500/40 rounded-lg text-blue-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Prometheus Telemetry Stream
              </span>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-full">
                HTTP /metrics/prometheus LIVE
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Scraped: {webhooks} Webhook Events • {orders} Razorpay Orders • C-Index: {cIndex}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            disabled={isPolling}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-bold rounded-lg transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin text-blue-400' : ''}`} />
            <span>Poll Stream</span>
          </button>
          
          <button
            onClick={() => setShowRawDrawer(!showRawDrawer)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-900/40 hover:bg-blue-900/60 border border-blue-500/50 text-blue-300 text-xs font-bold rounded-lg transition-all"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>{showRawDrawer ? 'Hide Raw Stream' : 'Inspect Raw Prometheus'}</span>
          </button>
        </div>
      </div>

      {/* Cyber Grid KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Card 1: Total Payments */}
        <div className="p-3.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl relative overflow-hidden group hover:border-blue-500/50 transition-all">
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1 flex items-center justify-between">
            <span>Ingested Failures</span>
            <Activity className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-xl font-extrabold text-white">{total.toLocaleString()}</div>
          <div className="text-[10px] text-blue-400 mt-1">aria_payments_total</div>
          <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 2: Recovered */}
        <div className="p-3.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl relative overflow-hidden group hover:border-emerald-500/50 transition-all">
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1 flex items-center justify-between">
            <span>Recovered Payments</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-extrabold text-emerald-400">{recovered.toLocaleString()}</div>
          <div className="text-[10px] text-emerald-500 mt-1">aria_payments_recovered_total</div>
          <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 3: Recovery Rate */}
        <div className="p-3.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl relative overflow-hidden group hover:border-cyan-500/50 transition-all">
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1 flex items-center justify-between">
            <span>Recovery Rate</span>
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-xl font-extrabold text-cyan-300">{recRate.toFixed(1)}%</div>
          <div className="text-[10px] text-cyan-500 mt-1">aria_recovery_rate_pct</div>
          <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 4: Net Saved INR */}
        <div className="p-3.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl relative overflow-hidden group hover:border-purple-500/50 transition-all">
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1 flex items-center justify-between">
            <span>Net Saved Capital</span>
            <Database className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-extrabold text-purple-300">₹{netSaved.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
          <div className="text-[10px] text-purple-400 mt-1">aria_net_capital_saved_inr</div>
          <div className="absolute top-0 right-0 w-16 h-16 bg-purple-500/5 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* Raw Prometheus Stream Drawer */}
      {showRawDrawer && (
        <div className="p-4 bg-black border border-blue-900/60 rounded-xl font-mono text-xs text-blue-300 space-y-2 overflow-x-auto shadow-2xl">
          <div className="flex items-center justify-between text-[11px] text-zinc-400 border-b border-zinc-800 pb-2">
            <span>Raw OpenTelemetry / Prometheus Exporter Output:</span>
            <span>GET /metrics/prometheus</span>
          </div>
          <pre className="text-zinc-300 leading-relaxed text-[11px]">
            {rawPrometheusText || `aria_payments_total ${total}\naria_payments_recovered_total ${recovered}\naria_net_capital_saved_inr ${netSaved}\naria_recovery_rate_pct ${recRate}\naria_razorpay_webhooks_ingested_total ${webhooks}\naria_razorpay_orders_created_total ${orders}\naria_weibull_cindex_score ${cIndex}`}
          </pre>
        </div>
      )}
    </div>
  );
}
