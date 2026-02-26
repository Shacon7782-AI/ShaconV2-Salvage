
"use client";

import React, { useState, useEffect } from "react";
import { Activity, ShieldCheck, Zap, Cpu } from "lucide-react";
import "@/styles/CyberGlass.css";

export default function TactileHUD() {
    const [telemetry, setTelemetry] = useState({ cpu: 15, mem: 23, agent_count: 50 });
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const fetchStats = async () => {
            try {
                // In a real scenario, this would be a WebSocket or SSE stream from the backend
                // For now, we simulate the hardware-reactive data
                const cpu = 10 + Math.random() * 20;
                const mem = 20 + Math.random() * 5;
                setTelemetry({ cpu, mem, agent_count: 50 });

                // Update CSS Variables for CyberGlass
                const pulseRate = Math.max(0.2, 2 - (cpu / 50)) + "s";
                document.documentElement.style.setProperty('--p-core-pulse', pulseRate);
                document.documentElement.style.setProperty('--intel-load-color', cpu > 40 ? 'var(--sovereign-crimson)' : 'var(--sovereign-teal)');
            } catch (err) {
                console.error("Telemetry Error:", err);
            }
        };

        const interval = setInterval(fetchStats, 1000);
        return () => clearInterval(interval);
    }, []);

    if (!mounted) return null;

    return (
        <div className="fixed top-6 right-6 flex flex-col gap-6 z-50 pointer-events-none w-80">
            {/* 1. Main Hardware Diagnostic HUD */}
            <div className="cyber-glass reactive-pulse hologram-tilt p-6 space-y-4">
                <div className="scanline" />

                <div className="flex items-center justify-between border-b border-white/5 pb-2">
                    <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-accent" />
                        <span className="text-[10px] font-mono font-black tracking-widest uppercase">Kernel Diagnostics</span>
                    </div>
                    <div className="text-[9px] font-mono text-accent animate-pulse">LIVE UPLINK</div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <div className="text-[8px] text-white/30 uppercase font-mono">P-Core Saturation</div>
                        <div className="text-xl font-bold font-mono tracking-tighter text-white">
                            {telemetry.cpu.toFixed(1)}%
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-accent transition-all duration-500"
                                style={{ width: `${telemetry.cpu}%` }}
                            />
                        </div>
                    </div>
                    <div className="space-y-1">
                        <div className="text-[8px] text-white/30 uppercase font-mono">VRAM Isolation</div>
                        <div className="text-xl font-bold font-mono tracking-tighter text-white">
                            {telemetry.mem.toFixed(1)}%
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-accent transition-all duration-500"
                                style={{ width: `${telemetry.mem}%` }}
                            />
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4 text-[9px] font-mono text-white/40 pt-2 border-t border-white/5">
                    <div className="flex items-center gap-1">
                        <Zap className="w-3 h-3 text-gold" />
                        <span>Swarms: {telemetry.agent_count}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-teal" />
                        <span>Audit: LOCKED</span>
                    </div>
                </div>
            </div>

            {/* 2. Forensic Ingress Meter */}
            <div className="cyber-glass p-4 space-y-3 hologram-tilt" style={{ opacity: 0.9 }}>
                <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-3 h-3 text-accent" />
                    <span className="text-[9px] font-mono tracking-widest opacity-60">Intelligence Waveform</span>
                </div>
                <div className="h-12 flex items-center justify-around gap-1">
                    {[...Array(24)].map((_, i) => (
                        <div
                            key={i}
                            className="w-1 bg-accent/20 rounded-full transition-all duration-300"
                            style={{
                                height: `${10 + Math.random() * 80}%`,
                                backgroundColor: i % 4 === 0 ? 'var(--sovereign-teal)' : 'rgba(0, 242, 255, 0.1)'
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
