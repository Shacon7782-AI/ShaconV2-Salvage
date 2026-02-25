"use client";

import ChatWindow from "@/components/ChatWindow";
import NodeHUD from "@/components/NodeHUD";
import { Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-black text-white font-sans selection:bg-accent/30 selection:text-accent">
      {/* Background VFX */}
      <NodeHUD />
      <div className="absolute inset-0 radial-glow pointer-events-none" />

      {/* Floating Orbs */}
      <div className="absolute top-[20%] left-[10%] w-64 h-64 bg-accent/5 rounded-full blur-[100px]" />
      <div className="absolute bottom-[20%] right-[10%] w-96 h-96 bg-accent/5 rounded-full blur-[120px]" />

      <main className="relative z-10 flex flex-col items-center gap-12 px-6 w-full max-w-6xl py-20">
        {/* Hero Text */}
        <div className="flex flex-col items-center text-center space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent/5 text-[10px] font-mono tracking-[0.3em] text-accent uppercase mb-4">
            <Sparkles className="w-3 h-3" />
            Sovereign Engine v2.0
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tighter bg-linear-to-b from-white to-white/40 bg-clip-text text-transparent">
            Build the Swarm. <br />
            <span className="text-accent">Master the Void.</span>
          </h1>
          <p className="max-w-xl text-sm md:text-base text-white/40 font-mono leading-relaxed uppercase tracking-tighter">
            An autonomous agentic workspace built for massive scale. <br className="hidden md:block" />
            Powered by the Shacon Intelligence Cluster.
          </p>
        </div>

        {/* Central Component: The Chat Interface */}
        <div className="w-full flex justify-center animate-in fade-in zoom-in-95 duration-1000 delay-300">
          <ChatWindow />
        </div>

        {/* Footer Meta */}
        <div className="flex flex-col md:flex-row gap-8 items-center text-[10px] font-mono text-white/20 uppercase tracking-[0.2em] mt-8">
          <div className="flex items-center gap-3">
            <div className="w-1 h-1 rounded-full bg-accent" />
            <span>Stateless API Architecture</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-1 h-1 rounded-full bg-accent" />
            <span>Stateless RAG Cluster</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-1 h-1 rounded-full bg-accent" />
            <span>Autonomous Logic Transplants</span>
          </div>
        </div>
      </main>

      {/* Aesthetic Overlays */}
      <div className="fixed top-0 inset-x-0 h-px bg-linear-to-r from-transparent via-white/10 to-transparent pointer-events-none" />
      <div className="fixed bottom-0 inset-x-0 h-px bg-linear-to-r from-transparent via-white/10 to-transparent pointer-events-none" />
    </div>
  );
}
