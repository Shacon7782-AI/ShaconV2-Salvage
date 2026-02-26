import { useState, useEffect } from "react";
import api from "@/lib/api";

export interface Document {
    id: number;
    title: string;
    file_type: string;
    created_at: string;
}

export function useKnowledge() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);

    const fetchDocuments = async () => {
        setLoading(true);
        try {
            const { data } = await api.get<Document[]>("/documents");
            setDocuments(data);
        } catch (error) {
            console.error("Failed to fetch docs", error);
        } finally {
            setLoading(false);
        }
    };

    const uploadDocument = async (file: File) => {
        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            await api.post("/documents/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            await fetchDocuments(); // Refresh list
        } catch (error) {
            console.error("Upload failed", error);
            throw error;
        } finally {
            setUploading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    return { documents, loading, uploading, uploadDocument, refresh: fetchDocuments };
}
