/// <reference lib="webworker" />
// HUD Physics Web Worker
// Calculates node positions off-main-thread to maintain 60fps

interface WorkerNode {
    id: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
}

let nodes: WorkerNode[] = [];

onmessage = function (e: MessageEvent) {
    const { type, data } = e.data;

    if (type === "INIT") {
        nodes = data.nodes.map((n: { id: number, x: number, y: number }) => ({
            ...n,
            vx: 0,
            vy: 0
        }));
    }

    if (type === "TICK") {
        // Simplified Force Directed Graph logic in Vanilla JS
        const friction = 0.95;
        const center = { x: 50, y: 50 };

        nodes.forEach(node => {
            // Pull to center
            node.vx += (center.x - node.x) * 0.01;
            node.vy += (center.y - node.y) * 0.01;

            // Repulsion between nodes
            nodes.forEach(other => {
                if (node.id === other.id) return;
                const dx = node.x - other.x;
                const dy = node.y - other.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                if (dist < 20) {
                    const force = (20 - dist) * 0.05;
                    node.vx += (dx / dist) * force;
                    node.vy += (dy / dist) * force;
                }
            });

            // Update positions
            node.vx *= friction;
            node.vy *= friction;
            node.x += node.vx;
            node.y += node.vy;

            // Clamp to bounds
            node.x = Math.max(0, Math.min(100, node.x));
            node.y = Math.max(0, Math.min(100, node.y));
        });

        postMessage({ type: "TICK", nodes });
    }
};
