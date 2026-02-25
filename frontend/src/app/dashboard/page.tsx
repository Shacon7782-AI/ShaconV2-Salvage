"use client";

import React, { useEffect, useState } from "react";
import { Activity, Database, GitBranch, Shield, Zap } from "lucide-react";

interface TelemetryFinding {
    agent_id: string;
    content: string;
    timestamp: string;
}

interface TelemetryInsight {
    agent_id: string;
    content: string;
    timestamp: string;
}

interface TelemetryData {
    findings: TelemetryFinding[];
    insights: TelemetryInsight[];
}

interface GraphRelation {
    source: string;
    target: string;
    relation: string;
}

interface GraphData {
    entities: Record<string, any>;
    relations: GraphRelation[];
}

interface HealthCheck {
    name: string;
    status: string;
}

interface HealthReport {
    status: string;
    checks: HealthCheck[];
    summary: string;
}

export default function Dashboard() {
    const [telemetry, setTelemetry] = useState<TelemetryData>({ findings: [], insights: [] });
    const [graph, setGraph] = useState<GraphData>({ entities: {}, relations: [] });
    const [health, setHealth] = useState<HealthReport | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [telRes, graphRes, healthRes] = await Promise.all([
                    fetch("http://localhost:8080/api/dashboard/telemetry"),
                    fetch("http://localhost:8080/api/dashboard/graph"),
                    fetch("http://localhost:8080/api/health")
                ]);

                setTelemetry(await telRes.json());
                setGraph(await graphRes.json());
                setHealth(await healthRes.json());
            } catch (err) {
                console.error("Failed to fetch dashboard data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-cyan-500 flex items-center justify-center font-mono">
                <div className="animate-pulse">INITIALIZING SENTINEL INTERFACE...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#050505] text-white p-8 font-mono bg-[radial-gradient(circle_at_50%_50%,#111_0%,#050505_100%)]">
            {/* Header */}
            <header className="flex justify-between items-center mb-12 border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter text-transparent bg-clip-text bg-linear-to-r from-cyan-400 to-blue-600">
                        SENTINEL DASHBOARD
                    </h1>
                    <p className="text-white/40 text-xs mt-1">SHACON V2 // SYSTEM INTROSPECTION MODULE</p>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10">
                        <Shield className="w-4 h-4 text-green-400" />
                        <span className="text-xs uppercase tracking-widest">{health?.status || "NOMINAL"}</span>
                    </div>
                </div>
            </header>

            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Health & Telemetry */}
                <div className="space-y-8 lg:col-span-1">
                    {/* Health Check Cards */}
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
                        <h2 className="text-sm font-bold mb-4 flex items-center gap-2 opacity-60">
                            <Zap className="w-4 h-4" /> SYSTEM VITALITY
                        </h2>
                        <div className="space-y-4">
                            {health?.checks?.map((check: HealthCheck, i: number) => (
                                <div key={i} className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/5">
                                    <span className="text-xs uppercase text-white/60">{check.name}</span>
                                    <span className={`text-[10px] px-2 py-0.5 rounded ${check.status === 'OK' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                        {check.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                        <p className="text-[10px] text-white/30 mt-4 leading-relaxed italic">{health?.summary}</p>
                    </div>

                    {/* Real-time Insights Feed */}
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl h-[400px] overflow-hidden flex flex-col">
                        <h2 className="text-sm font-bold mb-4 flex items-center gap-2 opacity-60">
                            <Activity className="w-4 h-4" /> BLACKBOARD INSIGHTS
                        </h2>
                        <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar">
                            {telemetry.insights.length === 0 && <p className="text-xs text-white/20 italic">No semantic insights captured...</p>}
                            {telemetry.insights.map((insight: TelemetryInsight, i: number) => (
                                <div key={i} className="p-3 border-l-2 border-cyan-500/50 bg-white/5 rounded-r-lg">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-[10px] text-cyan-400 font-bold">{insight.agent_id}</span>
                                        <span className="text-[8px] text-white/20">{new Date(insight.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="text-[11px] leading-snug">{insight.content}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Column: Knowledge Graph Visualization */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-xl h-full min-h-[600px] flex flex-col">
                        <h2 className="text-sm font-bold mb-6 flex items-center gap-2 opacity-60">
                            <GitBranch className="w-4 h-4" /> SEMANTIC KNOWLEDGE MAP
                        </h2>

                        <div className="flex-1 relative border border-white/5 bg-black/40 rounded-xl overflow-hidden flex items-center justify-center">
                            {/* This is a placeholder for a real D3/Cytoscape graph. For now, we'll list entities semantically */}
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 w-full p-8 overflow-y-auto">
                                {Object.keys(graph.entities).length === 0 && (
                                    <div className="col-span-full text-center text-white/10 text-xs py-20 italic">
                                        Knowledge Graph is building...
                                    </div>
                                )}
                                {Object.keys(graph.entities).map((id, i) => (
                                    <div key={i} className="group relative bg-white/5 border border-white/10 p-4 rounded-lg hover:border-cyan-500/50 transition-all cursor-default overflow-hidden">
                                        <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/5 rounded-full -mr-8 -mt-8 group-hover:bg-cyan-500/10 transition-colors"></div>
                                        <div className="text-[10px] text-cyan-500/40 mb-1 font-bold">ENTITY</div>
                                        <div className="text-sm font-bold tracking-tight truncate">{id}</div>
                                        <div className="mt-2 flex flex-wrap gap-1">
                                            {graph.relations.filter(r => r.source === id || r.target === id).slice(0, 3).map((r, ri) => (
                                                <div key={ri} className="text-[8px] color-white/20 bg-white/5 px-1 py-0.5 rounded">
                                                    {r.relation} {r.source === id ? '→' : '←'} {r.source === id ? r.target : r.source}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Status Info Box */}
                            <div className="absolute bottom-4 right-4 bg-black/80 border border-white/10 p-4 rounded shadow-2xl backdrop-blur-md">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-cyan-500/10 rounded">
                                        <Database className="w-4 h-4 text-cyan-400" />
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-white/40 uppercase">Nodes Synced</div>
                                        <div className="text-lg font-bold">{Object.keys(graph.entities).length}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-6 flex gap-8">
                            <div className="flex-1">
                                <div className="text-[10px] text-white/20 uppercase mb-2">Recent Findings Feed</div>
                                <div className="space-y-2 max-h-32 overflow-y-auto pr-2 custom-scrollbar">
                                    {telemetry.findings.map((f, i) => (
                                        <div key={i} className="text-[9px] text-white/40 border-b border-white/5 pb-1">
                                            <span className="text-cyan-500/40">[{f.agent_id}]</span> {f.content.substring(0, 80)}...
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
      `}</style>
        </div>
    );
}
