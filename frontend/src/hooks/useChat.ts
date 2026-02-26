import { useState } from "react";
import api from "@/lib/api";

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

export interface ChatResponse {
    response: string;
    sources: string[];
}

export function useChat() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);

    const sendMessage = async (message: string) => {
        // Optimistic Update
        const userMsg: ChatMessage = { role: "user", content: message };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const { data } = await api.post<ChatResponse>("/chat", { message });
            const aiMsg: ChatMessage = { role: "assistant", content: data.response };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (error) {
            console.error("Chat failed", error);
            const errorMsg: ChatMessage = { role: "assistant", content: "Sorry, I encountered an error answering that." };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setLoading(false);
        }
    };

    return { messages, loading, sendMessage, setMessages };
}
