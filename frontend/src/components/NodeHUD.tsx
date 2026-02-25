"use client";

import React, { useState, useEffect } from "react";

interface HUDNode {
    id: number;
    x: number;
    y: number;
    size: number;
    pulseDelay: number;
}

export default function NodeHUD() {
    const [nodes, setNodes] = useState<HUDNode[]>([]);
    const [connections, setConnections] = useState<{ i: number, j: number, opacity: number }[]>([]);
    const [mounted, setMounted] = useState(false);
    const [stats, setStats] = useState({ nodes: 0, latency: 42 });

    useEffect(() => {
        const timer = setTimeout(() => setMounted(true), 0);

        async function fetchGraph() {
            try {
                const start = Date.now();
                const res = await fetch("http://localhost:8080/api/dashboard/graph");
                const data = await res.json();
                const latency = Date.now() - start;

                const entities: string[] = data.entities || [];
                const relations: { source: string, target: string }[] = data.relations || [];

                // Transform entities into HUD nodes with stable-ish positions based on ID
                const newNodes: HUDNode[] = entities.map((_entity: string, idx: number) => {
                    return {
                        id: idx,
                        x: 10 + (Math.abs(Math.sin(idx * 1.5)) * 80),
                        y: 10 + (Math.abs(Math.cos(idx * 2.2)) * 80),
                        size: 2 + (idx % 5),
                        pulseDelay: (idx * 0.5) % 5
                    };
                });

                // Map relations to connections
                const newConnections = relations.map((rel: { source: string, target: string }) => {
                    // Find indices
                    const sourceIdx = entities.indexOf(rel.source);
                    const targetIdx = entities.indexOf(rel.target);
                    if (sourceIdx !== -1 && targetIdx !== -1) {
                        return { i: sourceIdx, j: targetIdx, opacity: 0.5 };
                    }
                    return null;
                }).filter((c): c is { i: number, j: number, opacity: number } => c !== null);

                setNodes(newNodes);
                setConnections(newConnections);
                setStats({ nodes: newNodes.length, latency });
            } catch (err) {
                console.error("HUD Fetch Error:", err);
            }
        }

        fetchGraph();
        const interval = setInterval(fetchGraph, 10000);

        return () => {
            clearTimeout(timer);
            clearInterval(interval);
        };
    }, []);

    if (!mounted) return null;

    return (
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-40">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Connections */}
                {connections.map((line, idx) => (
                    <line
                        key={`line-${idx}`}
                        x1={nodes[line.i]?.x || 0}
                        y1={nodes[line.i]?.y || 0}
                        x2={nodes[line.j]?.x || 0}
                        y2={nodes[line.j]?.y || 0}
                        stroke="var(--accent)"
                        strokeWidth="0.1"
                        strokeOpacity={line.opacity * 0.3}
                    />
                ))}

                {/* Nodes */}
                {nodes.map((node) => (
                    <g key={`node-${node.id}`} className="node-pulse" style={{ animationDelay: `${node.pulseDelay}s` }}>
                        <circle
                            cx={node.x}
                            cy={node.y}
                            r={node.size * 0.15}
                            fill="var(--accent)"
                            className="drop-shadow-[0_0_8px_var(--accent)]"
                        />
                        <circle
                            cx={node.x}
                            cy={node.y}
                            r={node.size * 0.4}
                            fill="transparent"
                            stroke="var(--accent)"
                            strokeWidth="0.05"
                            strokeOpacity="0.2"
                        />
                    </g>
                ))}
            </svg>

            {/* HUD Overlays */}
            <div className="absolute top-8 right-8 text-right font-mono text-[10px] space-y-1 text-accent/40 uppercase tracking-widest hidden md:block">
                <div className="flex justify-end gap-4">
                    <span>Knowledge Nodes: {stats.nodes}</span>
                    <span className="text-white/20">|</span>
                    <span>Latency: {stats.latency}ms</span>
                </div>
                <div>Core Engine: NOMINAL</div>
                <div className="text-white/10 italic leading-tight">Live Intelligence Mapping Active...</div>
            </div>

            <div className="absolute bottom-8 left-8 text-left font-mono text-[10px] text-accent/40 uppercase tracking-widest hidden md:block">
                <div className="flex gap-4">
                    <span>Sovereign Link: Stable</span>
                    <span className="text-white/20">|</span>
                    <span>Context Density: {(stats.nodes / 10).toFixed(2)}</span>
                </div>
            </div>
        </div>
    );
}
