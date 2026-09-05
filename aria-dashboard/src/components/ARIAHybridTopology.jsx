import React, { useState, useEffect } from 'react';
import { Radio, Zap, ShieldAlert, CheckCircle2, Activity, ArrowUpRight, Cpu, RefreshCw, Volume2, MessageSquare, Send, RotateCcw, AlertTriangle } from 'lucide-react';

export default function ARIAHybridTopology({ metrics, networkNodes = [], isRunning = false, onSelectBank }) {
  const [selectedBank, setSelectedBank] = useState(null);
  const [simulatedOutage, setSimulatedOutage] = useState(false);
  const [activePackets, setActivePackets] = useState([]);
  const [recentTxLogs, setRecentTxLogs] = useState([]);

  // Default Bank Topology Nodes
  const defaultBanks = [
    { code: 'HDFC', name: 'HDFC Bank', successRate: 98.4, latency: 84, tps: 1420, health: 'HEALTHY', color: '#10b981', x: 200, y: 140 },
    { code: 'SBI', name: 'State Bank of India', successRate: 74.2, latency: 420, tps: 890, health: 'DEGRADED', color: '#f59e0b', x: 600, y: 140 },
    { code: 'ICICI', name: 'ICICI Bank', successRate: 96.1, latency: 110, tps: 1250, health: 'HEALTHY', color: '#10b981', x: 180, y: 380 },
    { code: 'AXIS', name: 'Axis Bank', successRate: 91.5, latency: 165, tps: 980, health: 'HEALTHY', color: '#10b981', x: 620, y: 380 },
    { code: 'KOTAK', name: 'Kotak Mahindra', successRate: 42.0, latency: 1180, tps: 310, health: 'CRITICAL', color: '#ef4444', x: 400, y: 440 },
  ];

  const banks = defaultBanks.map(b => {
    const isOutage = simulatedOutage && (b.code === 'SBI' || b.code === 'KOTAK');
    return {
      ...b,
      healthStatus: isOutage ? 'CIRCUIT_BREAKER_TRIPPED' : b.health,
      activeColor: isOutage ? '#ef4444' : b.color
    };
  });

  const centerCore = { x: 400, y: 260 };

  const armPayoffs = [
    { id: 'voice', label: 'Voice Call (bulbul:v3)', value: 85, cost: '₹0.45', icon: Volume2, color: '#ec4899' },
    { id: 'retry', label: 'Gateway Retry', value: 79, cost: '₹0.05', icon: RotateCcw, color: '#3b82f6' },
    { id: 'whatsapp', label: 'WhatsApp Intercept', value: 68, cost: '₹0.20', icon: MessageSquare, color: '#22c55e' },
    { id: 'sms', label: 'SMS Notification', value: 48, cost: '₹0.10', icon: Send, color: '#eab308' },
    { id: 'stop', label: 'Escalate without Cost (STOP)', value: 15, cost: '₹0.00', icon: AlertTriangle, color: '#64748b' },
  ];

  // Fire live payment packet animation
  const handleFirePayment = () => {
    const target = banks[Math.floor(Math.random() * banks.length)];
    const packetId = `packet-${Date.now()}-${Math.random()}`;
    
    setActivePackets(prev => [...prev, { id: packetId, target, startTime: Date.now() }]);

    const txId = `pay_${Math.random().toString(36).substring(2, 9)}`;
    const amounts = [1499, 2999, 4999, 8500, 12000];
    const amt = amounts[Math.floor(Math.random() * amounts.length)];

    setRecentTxLogs(prev => [
      { id: txId, amount: amt, bank: target.code, status: target.healthStatus === 'CIRCUIT_BREAKER_TRIPPED' ? 'REROUTED → ICICI' : 'RECOVERED', time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 4)
    ]);
  };

  // Remove expired packets
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setActivePackets(prev => prev.filter(p => now - p.startTime < 1200));
    }, 200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full space-y-6 font-mono text-zinc-100">
      
      {/* Sleek Top Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-zinc-950/90 border border-blue-900/40 rounded-xl backdrop-blur-xl shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-950/80 border border-blue-500/40 rounded-lg text-blue-400">
            <Radio className="w-5 h-5 animate-pulse text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                REAL-TIME PAYMENT GATEWAY TOPOLOGY
              </span>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-full">
                LinUCB 29D Core • Pearson ρ = 0.824
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Live fiber-optic routing • 50 Merchants Monitored • Weibull C-Index: 0.865
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleFirePayment}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all shadow-[0_0_15px_rgba(37,99,235,0.5)] active:scale-95"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Fire Payment Packet</span>
          </button>

          <button
            onClick={() => setSimulatedOutage(!simulatedOutage)}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold rounded-lg transition-all active:scale-95 border ${
              simulatedOutage
                ? 'bg-rose-950 border-rose-500 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.6)] animate-pulse'
                : 'bg-zinc-900 hover:bg-zinc-800 text-rose-300 border-rose-900/50'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>{simulatedOutage ? 'Outage Active (Rerouted)' : 'Simulate Outage'}</span>
          </button>
        </div>
      </div>

      {/* Main Hybrid Network Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* SVG Network Topology View (2 Cols) */}
        <div className="lg:col-span-2 relative min-h-[480px] bg-zinc-950/90 border border-blue-900/30 rounded-xl p-4 overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)]">
          
          {/* Subtle Background Grid Pattern */}
          <div 
            className="absolute inset-0 opacity-15 pointer-events-none"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, #3b82f6 1px, transparent 0)`,
              backgroundSize: '24px 24px'
            }}
          />

          {/* Outage Warning Banner */}
          {simulatedOutage && (
            <div className="absolute top-4 left-4 right-4 z-20 p-2.5 bg-rose-950/90 border border-rose-500/60 rounded-lg backdrop-blur-md text-xs text-rose-200 flex items-center justify-between animate-in fade-in">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
                <span className="font-bold">BANK OUTAGE DETECTED (SBI & KOTAK)</span>
                <span>— Traffic Auto-Rerouted to ICICI Gateway</span>
              </div>
              <span className="text-[10px] bg-rose-900/60 px-2 py-0.5 rounded border border-rose-400/50 uppercase font-bold">
                Circuit Breaker Tripped
              </span>
            </div>
          )}

          <svg className="w-full h-[450px]" viewBox="0 0 800 520">
            <defs>
              {/* Glowing Line Gradients */}
              <linearGradient id="blueLine" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.3" />
              </linearGradient>
              <linearGradient id="redLine" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.4" />
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Bezier Cable Connection Lines */}
            {banks.map(b => {
              const isTripped = b.healthStatus === 'CIRCUIT_BREAKER_TRIPPED';
              const pathD = `M ${centerCore.x} ${centerCore.y} Q ${(centerCore.x + b.x)/2} ${(centerCore.y + b.y)/2 - 30} ${b.x} ${b.y}`;
              return (
                <g key={`cable-${b.code}`}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isTripped ? '#ef4444' : '#1e3a8a'}
                    strokeWidth="3"
                    strokeDasharray={isTripped ? '6,6' : 'none'}
                    className={isTripped ? 'animate-pulse' : ''}
                  />
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isTripped ? '#f43f5e' : '#38bdf8'}
                    strokeWidth="1.5"
                    strokeOpacity="0.7"
                    filter="url(#glow)"
                  />
                </g>
              );
            })}

            {/* Animated Fiber Data Stream Particles */}
            {activePackets.map(p => {
              const target = p.target;
              const pathD = `M ${centerCore.x} ${centerCore.y} Q ${(centerCore.x + target.x)/2} ${(centerCore.y + target.y)/2 - 30} ${target.x} ${target.y}`;
              return (
                <circle key={p.id} r="5" fill="#38bdf8" filter="url(#glow)">
                  <animateMotion path={pathD} dur="0.8s" repeatCount="1" fill="freeze" />
                </circle>
              );
            })}

            {/* Central ARIA Intelligence Core */}
            <g transform={`translate(${centerCore.x}, ${centerCore.y})`}>
              <circle r="42" fill="#030712" stroke="#3b82f6" strokeWidth="2" filter="url(#glow)" />
              <circle r="34" fill="#0f172a" stroke="#60a5fa" strokeWidth="1.5" />
              <circle r="26" fill="#1e3a8a" opacity="0.6" className="animate-pulse" />
              <text textAnchor="middle" y="-4" fill="#ffffff" fontSize="12" fontWeight="bold" fontFamily="monospace">
                ARIA CORE
              </text>
              <text textAnchor="middle" y="12" fill="#60a5fa" fontSize="9" fontFamily="monospace">
                LinUCB 29D
              </text>
            </g>

            {/* Bank Gateway Topology Nodes */}
            {banks.map(b => {
              const isSelected = selectedBank?.code === b.code;
              const isTripped = b.healthStatus === 'CIRCUIT_BREAKER_TRIPPED';

              return (
                <g 
                  key={`node-${b.code}`} 
                  transform={`translate(${b.x}, ${b.y})`}
                  onClick={() => {
                    setSelectedBank(b);
                    if (onSelectBank) onSelectBank(b);
                  }}
                  className="cursor-pointer group"
                >
                  {/* Outer Pulsing Ring */}
                  <circle 
                    r="28" 
                    fill="none" 
                    stroke={b.activeColor} 
                    strokeWidth={isSelected ? "3" : "1.5"}
                    strokeOpacity={isSelected ? "1" : "0.5"}
                    filter="url(#glow)"
                    className={isTripped ? "animate-ping" : ""}
                  />
                  {/* Node Body */}
                  <circle r="22" fill="#090d16" stroke={b.activeColor} strokeWidth="2" />
                  
                  {/* Bank Symbol Text */}
                  <text textAnchor="middle" y="4" fill="#ffffff" fontSize="11" fontWeight="bold" fontFamily="monospace">
                    {b.code}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Floating HTML Screen Badges for Bank Nodes */}
          {banks.map(b => (
            <div
              key={`badge-${b.code}`}
              style={{ left: `${(b.x / 800) * 100}%`, top: `${(b.y / 520) * 100}%` }}
              onClick={() => {
                setSelectedBank(b);
                if (onSelectBank) onSelectBank(b);
              }}
              className="absolute -translate-x-1/2 translate-y-6 z-10 cursor-pointer select-none"
            >
              <div className={`px-2.5 py-1 rounded-md text-[11px] font-bold backdrop-blur-md border transition-all hover:scale-105 shadow-xl flex items-center space-x-1.5 ${
                b.healthStatus === 'CIRCUIT_BREAKER_TRIPPED'
                  ? 'bg-rose-950/90 border-rose-500 text-rose-200 animate-bounce'
                  : selectedBank?.code === b.code
                    ? 'bg-emerald-950/90 border-emerald-400 text-emerald-200 ring-2 ring-emerald-500/50'
                    : 'bg-zinc-950/85 border-zinc-800 text-zinc-300 hover:border-blue-400'
              }`}>
                <span className={`w-2 h-2 rounded-full ${b.healthStatus === 'CIRCUIT_BREAKER_TRIPPED' ? 'bg-rose-500 animate-ping' : 'bg-emerald-400'}`} />
                <span>{b.name}</span>
                <span className="text-zinc-400 font-normal">({b.successRate}%)</span>
              </div>
            </div>
          ))}

          {/* Bottom Left Live Telemetry Feed */}
          {recentTxLogs.length > 0 && (
            <div className="absolute bottom-4 left-4 z-20 w-72 p-3 bg-zinc-950/95 border border-blue-900/40 rounded-xl backdrop-blur-md text-xs space-y-1.5 shadow-2xl">
              <div className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider border-b border-zinc-800 pb-1 flex justify-between">
                <span>Live Transaction Stream</span>
                <span className="text-emerald-400 animate-pulse">● LIVE</span>
              </div>
              {recentTxLogs.map((tx) => (
                <div key={tx.id} className="flex justify-between items-center text-[11px]">
                  <span className="text-zinc-200 font-bold">{tx.id}</span>
                  <span className="text-zinc-400">₹{tx.amount}</span>
                  <span className="text-blue-400">{tx.bank}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${tx.status.includes('RECOVERED') ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                    {tx.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 29D LinUCB Policy Payoff Weights Panel (1 Col) */}
        <div className="space-y-4">
          <div className="p-5 bg-zinc-950/90 border border-blue-900/40 rounded-xl backdrop-blur-xl shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  LinUCB Contextual Payoffs (29D)
                </h3>
                <p className="text-[10px] text-zinc-400">Expected Value EV(a, t | x_t)</p>
              </div>
              <Cpu className="w-4 h-4 text-blue-400" />
            </div>

            <div className="space-y-3">
              {armPayoffs.map((arm) => {
                const Icon = arm.icon;
                return (
                  <div key={arm.id} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <Icon className="w-3.5 h-3.5" style={{ color: arm.color }} />
                        <span className="font-semibold text-zinc-200">{arm.label}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-zinc-500">{arm.cost}</span>
                        <span className="font-bold" style={{ color: arm.color }}>{arm.value}%</span>
                      </div>
                    </div>
                    {/* Sleek Progress Bar */}
                    <div className="w-full h-2 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                      <div 
                        className="h-full rounded-full transition-all duration-500" 
                        style={{ width: `${arm.value}%`, backgroundColor: arm.color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-3 bg-blue-950/30 border border-blue-800/40 rounded-lg text-[11px] text-blue-300 leading-relaxed">
              <span className="font-bold">LinUCB Decision Rule:</span> Arm chosen via argmax_a (x_t^T θ_a + α √(x_t^T A_a⁻¹ x_t)). Friction penalty λ = 0.50.
            </div>
          </div>

          {/* Selected Bank Gateway Detail Card */}
          {selectedBank && (
            <div className="p-4 bg-zinc-950/95 border border-emerald-500/50 rounded-xl backdrop-blur-xl shadow-2xl space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                <div className="flex items-center space-x-2">
                  <span className={`w-3 h-3 rounded-full ${selectedBank.healthStatus === 'CIRCUIT_BREAKER_TRIPPED' ? 'bg-red-500 animate-ping' : 'bg-emerald-400'}`} />
                  <span className="font-bold text-white text-sm">{selectedBank.name} ({selectedBank.code})</span>
                </div>
                <button 
                  onClick={() => setSelectedBank(null)}
                  className="text-zinc-500 hover:text-white text-xs px-1.5 py-0.5 rounded border border-zinc-800"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2 text-xs text-zinc-300">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Success Rate:</span>
                  <span className="font-bold text-emerald-400">{selectedBank.successRate}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Avg Latency:</span>
                  <span className="font-bold text-blue-400">{selectedBank.latency} ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Throughput (TPS):</span>
                  <span className="font-bold text-cyan-400">{selectedBank.tps} req/s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Health Status:</span>
                  <span className={`font-bold ${selectedBank.healthStatus === 'CIRCUIT_BREAKER_TRIPPED' ? 'text-red-400' : 'text-emerald-400'}`}>
                    {selectedBank.healthStatus}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
