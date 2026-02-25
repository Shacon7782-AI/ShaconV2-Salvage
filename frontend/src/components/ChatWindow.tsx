"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";

interface Message {
    role: "user" | "assistant";
    content: string;
    thinking?: string;
}

export default function ChatWindow() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: input, history: messages.map(m => ({ role: m.role, content: m.content })) }),
            });

            if (!response.ok) throw new Error("Backend offline");

            const data = await response.json();
            const assistantMsg: Message = {
                role: "assistant",
                content: typeof data.result === 'string' ? data.result : JSON.stringify(data.result),
                thinking: data.thinking
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch {
            setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not connect to the Swarm." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-2xl glass rounded-3xl overflow-hidden glowing-border">
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5 backdrop-blur-md">
                <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-accent" />
                    <span className="font-mono text-sm tracking-widest uppercase">Orchestrator v2.5</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-accent node-pulse" />
                    <span className="text-[10px] font-mono text-white/50 uppercase tracking-tighter">Sovereign Link Active</span>
                </div>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-white/20 space-y-4">
                        <Sparkles className="w-12 h-12" />
                        <p className="font-mono text-xs uppercase tracking-[0.2em]">Awaiting User Intent</p>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                        <div className="flex items-center gap-2 mb-1 px-2">
                            {msg.role === "assistant" ? <Bot className="w-3 h-3 text-accent" /> : <User className="w-3 h-3 text-white/40" />}
                            <span className="text-[10px] uppercase tracking-widest text-white/40 font-mono">
                                {msg.role === "assistant" ? "Orchestrator" : "Authorized User"}
                            </span>
                        </div>

                        {msg.thinking && (
                            <div className="max-w-[85%] mb-2 p-3 rounded-xl bg-accent/5 border border-accent/10 text-[11px] font-mono text-accent/60 italic">
                                {msg.thinking}
                            </div>
                        )}

                        <div className={`max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed ${msg.role === "user"
                            ? "bg-accent/10 border border-accent/20 text-white rounded-tr-sm"
                            : "bg-white/5 border border-white/10 text-white/90 rounded-tl-sm backdrop-blur-sm"
                            }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex items-center gap-2 text-accent/50 animate-pulse">
                        <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                        <span className="text-[10px] font-mono uppercase tracking-widest">Processing...</span>
                    </div>
                )}
            </div>

            <div className="p-4 bg-white/5 border-t border-white/10 backdrop-blur-md">
                <div className="relative group">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        placeholder="Enter Sovereign Command..."
                        className="w-full bg-black/40 border border-white/10 rounded-xl py-3 px-4 pr-12 text-sm font-mono placeholder:text-white/20 focus:outline-none focus:border-accent/50 transition-all"
                    />
                    <button
                        onClick={handleSend}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-accent transition-colors"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
