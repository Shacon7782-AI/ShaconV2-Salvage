"use client";

import React, { useMemo, useState, useEffect } from "react";

interface HUDNode {
    id: number;
    x: number;
    y: number;
    size: number;
    pulseDelay: number;
}

export default function NodeHUD() {
    const [nodes] = useState<HUDNode[]>(() =>
        Array.from({ length: 12 }).map((_, i) => ({
            id: i,
            x: 10 + Math.random() * 80, // %
            y: 10 + Math.random() * 80, // %
            size: 2 + Math.random() * 4,
            pulseDelay: Math.random() * 5,
        }))
    );
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setMounted(true), 0);
        return () => clearTimeout(timer);
    }, []);

    // Simple lines between close-ish nodes
    const connections = useMemo(() => {
        if (!mounted) return [];
        const lines = [];
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[i].x - nodes[j].x;
                const dy = nodes[i].y - nodes[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 30) {
                    lines.push({ i, j, opacity: 1 - dist / 30 });
                }
            }
        }
        return lines;
    }, [nodes, mounted]);

    if (!mounted) return null;

    return (
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-40">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Connections */}
                {connections.map((line, idx) => (
                    <line
                        key={`line-${idx}`}
                        x1={nodes[line.i].x}
                        y1={nodes[line.i].y}
                        x2={nodes[line.j].x}
                        y2={nodes[line.j].y}
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
                    <span>Swarm Cluster: 12/12</span>
                    <span className="text-white/20">|</span>
                    <span>Latency: 42ms</span>
                </div>
                <div>Core Engine: NOMINAL</div>
                <div className="text-white/10 italic leading-tight">Searching for user-defined concepts...</div>
            </div>

            <div className="absolute bottom-8 left-8 text-left font-mono text-[10px] text-accent/40 uppercase tracking-widest hidden md:block">
                <div className="flex gap-4">
                    <span>ASI Score: 0.98</span>
                    <span className="text-white/20">|</span>
                    <span>Risk: LOW</span>
                </div>
            </div>
        </div>
    );
}
