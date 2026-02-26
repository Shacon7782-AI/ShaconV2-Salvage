import { useState, useEffect } from "react";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

interface User {
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    full_name?: string;
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        checkUser();
    }, []);

    const checkUser = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) {
                setLoading(false);
                return;
            }
            const { data } = await api.get<User>("/users/me");
            setUser(data);
        } catch (error) {
            console.error("Auth check failed:", error);
            localStorage.removeItem("token");
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string) => {
        // 1. Get Token (Requires form-data format for OAuth2 standard)
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const { data } = await api.post("/auth/token", formData, {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });

        // 2. Save Token
        localStorage.setItem("token", data.access_token);

        // 3. Fetch User
        await checkUser();

        return true;
    };

    const logout = () => {
        localStorage.removeItem("token");
        setUser(null);
        router.push("/login");
    };

    return { user, loading, login, logout, checkUser };
}
