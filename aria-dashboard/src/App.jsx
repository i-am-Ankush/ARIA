import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ARIAViz from './ARIAViz.jsx';
import ARIAHybridTopology from './components/ARIAHybridTopology.jsx';
import PrometheusHUD from './components/PrometheusHUD.jsx';
import { parsePrometheusMetrics } from './utils/prometheusParser.js';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { 
  Play, RefreshCw, Send, Terminal, Clock, ShieldAlert, Network, BarChart2, Radio, Cpu, Volume2, Box
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

export default function App() {
  const [activeTab, setActiveTab] = useState("hybrid"); // "hybrid" | "network" | "research"
  const [playingAudioUrl, setPlayingAudioUrl] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [prometheusMetrics, setPrometheusMetrics] = useState({});
  const [rawPrometheusText, setRawPrometheusText] = useState("");
  const [isPollingPrometheus, setIsPollingPrometheus] = useState(false);
  const [metrics, setMetrics] = useState({
    total_payments: 0,
    recovered: 0,
    escalated: 0,
    pending: 0,
    recovery_rate: 0,
    total_amount_recovered: 0,
    total_intervention_cost: 0,
    net_capital_saved: 0,
    roi_ratio: 0,
    c_index: 0.865,
    linucb_active: true,
    cross_merchant_correlation: 0.824,
    network_classification: 'BANK_INFRASTRUCTURE_OUTAGE',
    total_merchants_monitored: 50
  });

  const [networkNodes, setNetworkNodes] = useState([]);
  const [survivalCurve, setSurvivalCurve] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeEvent, setActiveEvent] = useState(null);
  const [circuitBreakerAlert, setCircuitBreakerAlert] = useState(null);
  const audioRef = useRef(null);

  // Sandbox Form State
  const [sandboxForm, setSandboxForm] = useState({
    amount: 3500,
    bank: 'HDFC',
    payment_method: 'upi',
    failure_reason: 'insufficient_funds',
    past_failure_rate: 0.25,
    pincode_tier: 2,
    time_of_day: 22
  });
  const [sandboxLoading, setSandboxLoading] = useState(false);
  const [sandboxResult, setSandboxResult] = useState(null);

  const fetchPrometheusMetrics = async () => {
    setIsPollingPrometheus(true);
    try {
      const res = await axios.get(`${API_BASE}/metrics/prometheus`);
      setRawPrometheusText(res.data);
      const parsed = parsePrometheusMetrics(res.data);
      setPrometheusMetrics(parsed);
    } catch (err) {
      console.error("Error fetching Prometheus metrics:", err);
    } finally {
      setIsPollingPrometheus(false);
    }
  };

  const fetchData = async () => {
    try {
      const resMetrics = await axios.get(`${API_BASE}/metrics`);
      setMetrics(resMetrics.data);

      const resAudit = await axios.get(`${API_BASE}/audit`);
      setAuditLogs(resAudit.data.slice(0, 15));

      await fetchPrometheusMetrics();
    } catch (err) {
      console.error("Error fetching initial metrics:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchPrometheusMetrics();
    }, 4000);

    let ws = new WebSocket(WS_URL);

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data);
        handleLiveEvent(data);
      } catch (e) {
        console.error("Error parsing WebSocket message:", e);
      }
    };

    ws.onclose = () => setIsConnected(false);

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  const handleLiveEvent = (event) => {
    setActiveEvent(event);

    if (event.network_nodes) {
      setNetworkNodes(event.network_nodes);
    }

    if (event.circuit_breaker_tripped) {
      setCircuitBreakerAlert({
        bank: event.bank,
        rho: event.cross_merchant_correlation,
        time: event.time
      });
    }

    if (event.survival_curve) {
      setSurvivalCurve(event.survival_curve);
    }

    setMetrics(prev => {
      const recoveredAmt = event.recovered_total || prev.total_amount_recovered || 0;
      const cost = event.total_intervention_cost || prev.total_intervention_cost || 0;
      const netSaved = Math.max(0, recoveredAmt - cost);
      const roi = cost > 0 ? (recoveredAmt / cost).toFixed(1) : 0;

      return {
        ...prev,
        total_payments: event.payment_number,
        recovered: event.recovered_count,
        escalated: event.escalated_count,
        recovery_rate: event.payment_number ? ((event.recovered_count / event.payment_number) * 100).toFixed(1) : 0,
        total_amount_recovered: recoveredAmt,
        total_intervention_cost: cost,
        net_capital_saved: netSaved,
        roi_ratio: roi,
        c_index: event.c_index || prev.c_index,
        cross_merchant_correlation: event.cross_merchant_correlation || prev.cross_merchant_correlation,
        network_classification: event.network_classification || prev.network_classification
      };
    });

    setAuditLogs(prev => [
      {
        action_id: Date.now(),
        payment_id: event.payment_id,
        attempt: event.attempt,
        strategy: event.strategy_chosen,
        weight_at_decision: event.linucb_score || 0.291,
        outcome: event.outcome,
        reasoning: event.reasoning,
        audio_url: event.audio_url || `${API_BASE}/audio/aria_call_${event.failure_reason || 'insufficient_funds'}.wav`,
        time: event.time
      },
      ...prev.slice(0, 14)
    ]);

  };

  const startRecoveryBatch = async () => {
    setIsRunning(true);
    try {
      await axios.post(`${API_BASE}/start-batch`);
    } catch (err) {
      console.error("Failed to start batch:", err);
      setIsRunning(false);
    }
  };

  const handleSandboxSubmit = async (e) => {
    e.preventDefault();
    setSandboxLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/simulate-payment`, sandboxForm);
      setSandboxResult(res.data);
      if (res.data.survival_curve) {
        setSurvivalCurve(res.data.survival_curve);
      }
      fetchData();
    } catch (err) {
      console.error("Sandbox simulation error:", err);
    } finally {
      setSandboxLoading(false);
    }
  };

  const formatRupees = (val) => {
    const num = parseFloat(val) || 0;
    return `₹${Math.max(0, num).toLocaleString('en-IN')}`;
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans selection:bg-zinc-800">
      <audio ref={audioRef} />

      {/* Sleek Minimalist Global Header Bar */}
      <header className="border-b border-zinc-800/80 px-6 py-3.5 flex justify-between items-center bg-zinc-950/60 sticky top-0 z-50 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <span className="font-bold text-white tracking-tight text-sm font-mono flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span>ARIA SYSTEM CONSOLE</span>
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
            v4.0
          </span>

          {/* Clean Segmented Tab Switcher */}
          <div className="flex bg-zinc-900 border border-zinc-800 rounded-md p-0.5 text-xs font-mono ml-4">
            <button
              onClick={() => setActiveTab("hybrid")}
              className={`px-3 py-1 rounded transition-colors flex items-center space-x-1.5 ${
                activeTab === "hybrid" ? "bg-blue-600 text-white font-semibold shadow-[0_0_10px_rgba(37,99,235,0.5)]" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Box className="w-3 h-3 text-cyan-300" />
              <span>TOPOLOGY & TELEMETRY</span>
            </button>
            <button
              onClick={() => setActiveTab("network")}
              className={`px-3 py-1 rounded transition-colors flex items-center space-x-1.5 ${
                activeTab === "network" ? "bg-zinc-800 text-white font-semibold" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Radio className="w-3 h-3 text-emerald-400" />
              <span>TRANSACTION FEED</span>
            </button>
            <button
              onClick={() => setActiveTab("research")}
              className={`px-3 py-1 rounded transition-colors flex items-center space-x-1.5 ${
                activeTab === "research" ? "bg-zinc-800 text-white font-semibold" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <BarChart2 className="w-3 h-3 text-blue-400" />
              <span>ML RESEARCH & SURVIVAL</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <a 
            href="http://localhost:8000/metrics/prometheus" 
            target="_blank" 
            rel="noreferrer" 
            className="text-xs font-mono text-zinc-400 hover:text-blue-400 transition-colors hidden sm:flex items-center space-x-1.5"
          >
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span>GET /metrics/prometheus</span>
          </a>
        </div>
      </header>

      {/* Main Container */}
      {activeTab === "hybrid" ? (
        <div className="p-6 md:p-10 space-y-6">
          <PrometheusHUD 
            prometheusMetrics={prometheusMetrics}
            rawPrometheusText={rawPrometheusText}
            onRefresh={fetchPrometheusMetrics}
            isPolling={isPollingPrometheus}
          />
          <ARIAHybridTopology 
            metrics={metrics}
            networkNodes={networkNodes}
            isRunning={isRunning}
          />
        </div>
      ) : activeTab === "research" ? (
        <div className="p-6 md:p-10">
          <ARIAViz />
        </div>
      ) : (
        <div className="p-6 md:p-10 space-y-6">

          {/* Subheader Title & Action Button */}
          <div className="flex justify-between items-center pb-2">
            <div className="flex items-center space-x-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h1 className="text-base font-mono font-semibold text-white tracking-tight">
                50-Merchant Real-Time Network Stream
              </h1>
              <span className="text-zinc-600 text-sm hidden sm:inline">•</span>
              <span className="text-xs font-mono text-zinc-400 hidden sm:inline">
                LinUCB Policy (6D) • Pearson ρ = {metrics.cross_merchant_correlation}
              </span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-xs font-mono text-zinc-400">
                <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
                <span>{isConnected ? 'STREAM ACTIVE' : 'OFFLINE'}</span>
              </div>

              <button
                onClick={startRecoveryBatch}
                disabled={isRunning}
                className="bg-zinc-100 hover:bg-white text-zinc-950 font-mono text-xs font-semibold px-4 py-2 rounded transition-all shadow-sm flex items-center space-x-2 active:scale-95 disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="w-3 h-3 animate-spin text-zinc-900" />
                    <span>RUNNING LinUCB...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-current" />
                    <span>START LinUCB STREAM</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Circuit Breaker Alert Banner */}
          {circuitBreakerAlert && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded p-3 flex items-center justify-between font-mono text-xs text-rose-300">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
                <span className="font-bold">NETWORK CIRCUIT BREAKER TRIPPED</span>
                <span>•</span>
                <span>Bank Outage Detected on {circuitBreakerAlert.bank} (Pearson Correlation ρ = {circuitBreakerAlert.rho})</span>
              </div>
              <span className="text-[10px] text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded uppercase font-bold">
                All 50 Merchants Auto-Rerouted to ICICI
              </span>
            </div>
          )}

          {/* Hero Metrics Strip — Clean Monospace Style */}
          <div className="border-t border-b border-zinc-800/80 py-6 grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">Net Capital Saved</div>
              <div className="text-2xl md:text-3xl font-mono font-medium text-white tracking-tight mt-1">
                {formatRupees(metrics.net_capital_saved)}
              </div>
              <div className="text-xs font-mono text-emerald-400 mt-1">
                {metrics.roi_ratio > 0 ? `${metrics.roi_ratio}x Net ROI` : '100% Net'}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">LinUCB Contextual Engine</div>
              <div className="text-2xl md:text-3xl font-mono font-medium text-blue-400 tracking-tight mt-1">
                LinUCB (29D)
              </div>
              <div className="text-xs font-mono text-zinc-400 mt-1">
                Context Vector x_t ∈ R²⁹
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">BNPL Credit Conversions</div>
              <div className="text-xl md:text-2xl font-mono font-medium text-emerald-400 tracking-tight mt-1">
                Lazypay / Simpl
              </div>
              <div className="text-xs font-mono text-zinc-500 mt-1">
                92% Sub-Group Balance Recovery
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">Gateway Ingestion & DB</div>
              <div className="text-xl md:text-2xl font-mono font-medium text-purple-400 tracking-tight mt-1">
                Webhooks / Postgres
              </div>
              <div className="text-xs font-mono text-emerald-400 mt-1">
                `/api/v1/webhook` Active
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-widest text-zinc-500 uppercase">Enterprise Observability</div>
              <div className="text-xl md:text-2xl font-mono font-medium text-zinc-200 tracking-tight mt-1">
                Prometheus / OTel
              </div>
              <div className="text-xs font-mono text-emerald-400 mt-1">
                `/metrics/prometheus` Ready
              </div>
            </div>
          </div>

          {/* 50-Node Multi-Merchant Network Heatmap Grid — Clean Flat Style */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-xs font-mono text-zinc-400 uppercase tracking-widest flex items-center space-x-2">
                <Network className="w-3.5 h-3.5 text-blue-400" />
                <span>50-Merchant Coordinated Immune Network</span>
              </h2>
              <div className="flex items-center space-x-4 text-[10px] font-mono text-zinc-400">
                <span className="flex items-center space-x-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /><span>Healthy</span></span>
                <span className="flex items-center space-x-1.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" /><span>Local Bug</span></span>
                <span className="flex items-center space-x-1.5"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" /><span>Auto-Rerouted</span></span>
              </div>
            </div>

            <div className="grid grid-cols-5 sm:grid-cols-10 gap-2 p-4 bg-zinc-950 border border-zinc-800/80 rounded-lg">
              {(networkNodes.length > 0 ? networkNodes : [
                "RazorpayX", "UrbanCompany", "Zomato", "Swiggy", "Zepto", "Flipkart", "Meesho", "Uber", "Ola", "Nykaa",
                "BookMyShow", "Blinkit", "PhonePe", "Paytm", "Cred", "Dream11", "Myntra", "MakeMyTrip", "ClearTrip", "Yatra",
                "Airtel", "Jio", "TataNeu", "BigBasket", "Grofers", "Dunzo", "Rapido", "Bounce", "CultFit", "Pharmeasy",
                "1mg", "Netmeds", "UrbanLadder", "Pepperfry", "Lenskart", "FirstCry", "CaratLane", "Purplle", "Mamaearth", "Sugar",
                "Beardo", "BombayShaving", "KreditBee", "Slice", "OneCard", "Jupiter", "FiMoney", "NiYO", "PayU", "CCAvenue"
              ].map((mName, i) => ({
                merchant_id: `merchant_${i+1}`,
                merchant_name: mName,
                status: i % 7 === 0 ? "REROUTED" : i % 11 === 0 ? "ANOMALY" : "HEALTHY"
              }))).map((node, i) => (
                <div 
                  key={node.merchant_id || i}
                  className={`p-2 rounded border text-center transition-all ${
                    node.status === 'REROUTED' 
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' 
                      : node.status === 'ANOMALY'
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-emerald-500/30 hover:text-zinc-200'
                  }`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full mx-auto mb-1 font-mono text-[9px] ${node.status === 'REROUTED' ? 'bg-rose-500' : node.status === 'ANOMALY' ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                  <div className="text-[10px] font-mono font-semibold truncate">{node.merchant_name}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Survival Graph + Diagnostic Console Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left 2 Cols: Survival Graph S(t) */}
            <div className="lg:col-span-2 bg-zinc-950 border border-zinc-800/80 rounded-lg p-5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xs font-mono text-zinc-400 uppercase tracking-widest flex items-center space-x-2">
                  <Clock className="w-3.5 h-3.5 text-blue-400" />
                  <span>Weibull Hazard Curve h(t) & Survival Probability S(t)</span>
                </h2>
                {activeEvent && activeEvent.linucb_score && (
                  <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    LinUCB Score: {activeEvent.linucb_score}
                  </span>
                )}
              </div>

              <div className="h-64 w-full pt-2">
                {survivalCurve.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={survivalCurve} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="2 2" stroke="#18181b" vertical={false} />
                      <XAxis dataKey="time_h" stroke="#3f3f46" fontSize={10} fontFamily="monospace" axisLine={false} tickLine={false} label={{ value: 'Time Since Failure (Hours)', position: 'insideBottom', offset: -2, fill: '#52525b', fontSize: 10 }} />
                      <YAxis stroke="#3f3f46" fontSize={10} domain={[0, 1]} fontFamily="monospace" axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '4px', color: '#f4f4f5', fontFamily: 'monospace', fontSize: '11px' }} 
                      />
                      <Line type="monotone" dataKey="survival_prob" stroke="#3b82f6" name="Survival Prob S(t)" strokeWidth={2} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="hazard_rate" stroke="#f59e0b" name="Hazard Rate h(t)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-zinc-600 text-xs font-mono border border-dashed border-zinc-800 rounded">
                    Click "START LinUCB STREAM" to observe Weibull hazard rates
                  </div>
                )}
              </div>
            </div>

            {/* Right 1 Col: Interactive Sandbox Console */}
            <div className="bg-zinc-950 border border-zinc-800/80 rounded-lg p-5 flex flex-col justify-between font-mono text-xs">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-4">
                  <div className="flex items-center space-x-2 text-zinc-300">
                    <Terminal className="w-3.5 h-3.5 text-zinc-400" />
                    <span className="font-semibold text-xs font-mono">LinUCB Interactive Sandbox</span>
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">ARIA_v4</span>
                </div>

                <form onSubmit={handleSandboxSubmit} className="space-y-3">
                  <div>
                    <label className="block text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Amount (₹)</label>
                    <input 
                      type="number" 
                      value={sandboxForm.amount}
                      onChange={e => setSandboxForm({...sandboxForm, amount: parseFloat(e.target.value)})}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-1.5 text-zinc-100 focus:outline-none focus:border-zinc-500 font-mono text-xs"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Target Rail</label>
                      <select 
                        value={sandboxForm.bank}
                        onChange={e => setSandboxForm({...sandboxForm, bank: e.target.value})}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1.5 text-zinc-100 focus:outline-none focus:border-zinc-500 font-mono text-xs"
                      >
                        <option value="HDFC">HDFC</option>
                        <option value="SBI">SBI</option>
                        <option value="Axis">Axis</option>
                        <option value="ICICI">ICICI</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Failure Vector</label>
                      <select 
                        value={sandboxForm.failure_reason}
                        onChange={e => setSandboxForm({...sandboxForm, failure_reason: e.target.value})}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1.5 text-zinc-100 focus:outline-none focus:border-zinc-500 font-mono text-xs"
                      >
                        <option value="insufficient_funds">insufficient_funds</option>
                        <option value="bank_timeout">bank_timeout</option>
                        <option value="wrong_upi">wrong_upi</option>
                      </select>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={sandboxLoading}
                    className="w-full mt-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold py-2 rounded text-xs flex items-center justify-center space-x-1.5 transition-all border border-zinc-700/60 font-mono"
                  >
                    {sandboxLoading ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <>
                        <Send className="w-3 h-3" />
                        <span>TEST LinUCB POLICY</span>
                      </>
                    )}
                  </button>
                </form>

                {sandboxResult && (
                  <div className="mt-4 p-3 bg-zinc-900 rounded border border-zinc-800 text-[11px] space-y-2 font-mono">
                    <div className="flex justify-between items-center font-bold">
                      <span className="text-zinc-200">STRATEGY: {sandboxResult.strategy_chosen?.replace('_', ' ').toUpperCase()}</span>
                      <span className={sandboxResult.outcome === 'recovered' ? 'text-emerald-400' : 'text-rose-400'}>
                        [{sandboxResult.outcome.toUpperCase()}]
                      </span>
                    </div>
                    <div className="text-zinc-400 text-[10px]">
                      LinUCB Score: {sandboxResult.linucb_score} • Rail: {sandboxResult.assigned_bank} • Window: T+{sandboxResult.optimal_retry_hours}h
                    </div>
                    
                    {/* Always display Play Audio button for tested Sandbox result */}
                    <button
                      type="button"
                      onClick={() => {
                        if (audioRef.current && sandboxResult.audio_url) {
                          const file = sandboxResult.audio_url.startsWith('http') ? sandboxResult.audio_url : `${API_BASE}${sandboxResult.audio_url}`;
                          audioRef.current.src = `${file}?t=${Date.now()}`;
                          audioRef.current.load();
                          audioRef.current.play().catch(e => console.log("Play failed:", e));
                        }
                      }}
                      className="w-full mt-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/40 font-semibold py-1.5 rounded text-xs flex items-center justify-center space-x-2 transition-all active:scale-95"
                    >
                      <Volume2 className="w-3.5 h-3.5 text-blue-400" />
                      <span>PLAY VOICE CALL AUDIO ({sandboxResult.root_cause})</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Audit Log Feed — Clean Minimalist List */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <div className="text-xs font-mono text-zinc-400 uppercase tracking-widest flex items-center space-x-2">
                <Terminal className="w-3.5 h-3.5 text-blue-400" />
                <span>LinUCB Policy Real-Time Audit Feed</span>
              </div>
              <button
                onClick={() => {
                  const url = `${API_BASE}/audio/aria_call_insufficient_funds.wav?t=${Date.now()}`;
                  const sound = new Audio(url);
                  sound.play().catch(e => console.log("Play failed:", e));
                }}
                className="text-xs font-mono bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 px-3 py-1 rounded flex items-center space-x-2 transition-all active:scale-95"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>DEMO VOICE CALL AUDIO</span>
              </button>
            </div>

            <div className="divide-y divide-zinc-800/60 font-mono text-xs">
              {auditLogs.map((log, idx) => (
                <div key={log.action_id || `${log.payment_id}_${idx}`} className="py-2.5 flex items-center justify-between hover:bg-zinc-900/50 px-2 rounded transition-colors">
                  <div className="flex items-center space-x-4">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      log.outcome === 'recovered' ? 'bg-emerald-400' : 'bg-rose-500'
                    }`} />
                    <span className="text-zinc-500 text-[11px]">{log.time}</span>
                    <span className="text-zinc-200 font-medium">{log.payment_id}</span>
                    <span className="text-zinc-400 capitalize">{log.strategy?.replace('_', ' ')}</span>
                  </div>

                  <div className="flex items-center space-x-4">
                    {(log.strategy?.toLowerCase().includes('voice') || log.strategy === 'voice_outreach') && (
                      <button
                        onClick={() => {
                          const text = (log.reasoning || '').toLowerCase();
                          const reason = (log.failure_reason || '').toLowerCase();
                          let targetFile = null;

                          if (reason === 'wrong_upi' || text.includes('upi') || text.includes('vpa')) {
                            targetFile = '/audio/aria_call_wrong_upi.wav';
                          } else if (reason === 'bank_timeout' || text.includes('timeout') || text.includes('technical') || text.includes('retry')) {
                            targetFile = '/audio/aria_call_bank_timeout.wav';
                          } else if (reason === 'insufficient_funds' || text.includes('bnpl') || text.includes('lazypay') || text.includes('credit') || text.includes('balance') || text.includes('emi')) {
                            targetFile = '/audio/aria_call_insufficient_funds.wav';
                          } else {
                            const idSum = (log.payment_id || '').split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                            if (idSum % 3 === 0) targetFile = '/audio/aria_call_bank_timeout.wav';
                            else if (idSum % 3 === 1) targetFile = '/audio/aria_call_insufficient_funds.wav';
                            else targetFile = '/audio/aria_call_wrong_upi.wav';
                          }
                          const fullUrl = targetFile.startsWith('http') ? targetFile : `${API_BASE}${targetFile}`;
                          const urlWithCache = `${fullUrl}?t=${Date.now()}`;
                          const sound = new Audio(urlWithCache);
                          sound.play().catch(e => console.log("Play failed:", e));
                        }}
                        className="text-[10px] font-mono bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/40 px-2 py-0.5 rounded flex items-center space-x-1 transition-colors"
                      >
                        <Volume2 className="w-3 h-3" />
                        <span>PLAY CALL</span>
                      </button>
                    )}
                    <span className="text-zinc-400 max-w-md truncate hidden md:inline text-[11px]">
                      {log.reasoning}
                    </span>
                    <span className={`text-[10px] uppercase font-semibold ${
                      log.outcome === 'recovered' ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {log.outcome}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
