export const siteConfig = {
    name: "Antigravity Workspace",
    description: "AI-Powered Service Creation Platform",
    api: {
        baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api",
        timeout: 60000,
    },
    // Links to external resources or docs
    links: {
        github: "https://github.com/shacon/antigravity",
    }
}
