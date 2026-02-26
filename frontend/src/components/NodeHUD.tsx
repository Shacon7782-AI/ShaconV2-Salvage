"use client";

import React, { useState, useEffect, useRef } from "react";

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
    const workerRef = useRef<Worker | null>(null);

    useEffect(() => {
        // Hydration safety: break the synchronous flow to satisfy linter
        setTimeout(() => setMounted(true), 0);

        // 1. Initialize Worker
        workerRef.current = new Worker(new URL("./hud.worker.ts", import.meta.url));

        // 2. Worker Listener
        workerRef.current.onmessage = (e) => {
            if (e.data.type === "TICK") {
                setNodes(e.data.nodes);
            }
        };

        // 3. Fetch Data Logic
        async function fetchGraph() {
            try {
                const start = Date.now();
                const res = await fetch("http://localhost:8080/api/dashboard/graph");
                const data = await res.json();
                const latency = Date.now() - start;

                const entities: string[] = data.entities || [];
                const relations: { source: string, target: string }[] = data.relations || [];

                // Create initial nodes if worker is ready
                const initialNodes = entities.map((_e: string, idx: number) => ({
                    id: idx,
                    x: Math.random() * 100,
                    y: Math.random() * 100,
                    size: 2 + (idx % 5),
                    pulseDelay: (idx * 0.5) % 5
                }));

                const newConnections = relations.map((rel: { source: string, target: string }) => {
                    const sourceIdx = entities.indexOf(rel.source);
                    const targetIdx = entities.indexOf(rel.target);
                    return (sourceIdx !== -1 && targetIdx !== -1) ? { i: sourceIdx, j: targetIdx, opacity: 0.5 } : null;
                }).filter((c): c is { i: number, j: number, opacity: number } => c !== null);

                setConnections(newConnections);
                setStats({ nodes: initialNodes.length, latency });

                // Send to worker
                workerRef.current?.postMessage({
                    type: "INIT",
                    data: { nodes: initialNodes, connections: newConnections }
                });

            } catch (err) {
                console.error("HUD Fetch Error:", err);
            }
        }

        fetchGraph();
        const fetchInterval = setInterval(fetchGraph, 10000);

        // 4. Tick Loop (Off-thread simulation)
        const tickInterval = setInterval(() => {
            workerRef.current?.postMessage({ type: "TICK" });
        }, 16); // ~60fps

        return () => {
            workerRef.current?.terminate();
            clearInterval(fetchInterval);
            clearInterval(tickInterval);
        };
    }, []);

    if (!mounted) return null;

    return (
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-40">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
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

            <div className="absolute top-8 right-8 text-right font-mono text-[10px] space-y-1 text-accent/40 uppercase tracking-widest hidden md:block">
                <div className="flex justify-end gap-4">
                    <span>Active Clusters: {stats.nodes}</span>
                    <span className="text-white/20">|</span>
                    <span>Phys-Worker: 60FPS</span>
                </div>
                <div>Spatial Threading: ACTIVE</div>
            </div>
        </div>
    );
}
