"use client";

import React, { useState, useEffect } from "react";
import { Terminal, Activity, Zap } from "lucide-react";

interface TelemetryItem {
    agent_id: string;
    content: string;
    timestamp: string;
    type: "finding" | "insight";
}

export default function TelemetryFeed() {
    const [items, setItems] = useState<TelemetryItem[]>([]);

    useEffect(() => {
        async function fetchTelemetry() {
            try {
                const res = await fetch("http://localhost:8080/api/dashboard/telemetry");
                const data = await res.json();

                // Combine findings and insights, sort by timestamp
                const combined = [
                    ...data.findings.map((f: { agent_id: string, content: string, timestamp: string }) => ({ ...f, type: "finding" })),
                    ...data.insights.map((i: { agent_id: string, content: string, timestamp: string }) => ({ ...i, type: "insight" }))
                ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

                setItems(combined.slice(0, 15)); // Keep last 15
            } catch (err) {
                console.error("Telemetry Fetch Error:", err);
            }
        }

        fetchTelemetry();
        const interval = setInterval(fetchTelemetry, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed left-6 top-1/2 -translate-y-1/2 w-64 h-[400px] hidden xl:flex flex-col gap-4 pointer-events-none z-20">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-t-xl bg-accent/10 border-x border-t border-accent/20 backdrop-blur-md">
                <Activity className="w-3 h-3 text-accent animate-pulse" />
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-accent/80">Live Telemetry</span>
            </div>

            <div className="flex-1 overflow-hidden bg-black/40 border border-white/5 rounded-b-xl backdrop-blur-sm relative">
                <div className="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-black/60 pointer-events-none" />

                <div className="p-4 space-y-4">
                    {items.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full gap-2 opacity-20">
                            <Terminal className="w-6 h-6" />
                            <span className="text-[8px] font-mono uppercase tracking-widest">Awaiting Uplink...</span>
                        </div>
                    ) : (
                        items.map((item, idx) => (
                            <div key={idx} className="space-y-1 animate-in fade-in slide-in-from-left-4 duration-500">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                        <Zap className={`w-2 h-2 ${item.type === 'insight' ? 'text-accent' : 'text-white/40'}`} />
                                        <span className="text-[8px] font-bold font-mono uppercase tracking-tighter text-white/60">
                                            {item.agent_id}
                                        </span>
                                    </div>
                                    <span className="text-[7px] font-mono text-white/20 whitespace-nowrap">
                                        {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                    </span>
                                </div>
                                <p className="text-[9px] font-mono text-white/40 leading-relaxed border-l border-white/10 pl-2">
                                    {item.content}
                                </p>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
