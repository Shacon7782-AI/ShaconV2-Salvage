"use client"

import { useState, useCallback } from "react"
import api from "@/lib/api"

interface PageSpec {
    slug: string
    title: string
    purpose: string
    key_sections: string[]
}

interface AnalyzeResponse {
    project_summary: string
    target_audience: string
    brand_tone: string
    core_features: string[]
    suggested_pages: PageSpec[]
}

interface Project {
    id: number
    name: string
    description: string | null
    spec_json: AnalyzeResponse | null
}

export function useProject() {
    const [analyzing, setAnalyzing] = useState(false)
    const [creating, setCreating] = useState(false)
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(false)
    const [spec, setSpec] = useState<AnalyzeResponse | null>(null)

    const analyzeBrief = useCallback(async (brief: string): Promise<AnalyzeResponse | null> => {
        setAnalyzing(true)
        try {
            const res = await api.post<AnalyzeResponse>("/projects/analyze", { brief })
            setSpec(res.data)
            return res.data
        } catch (e) {
            console.error("Failed to analyze brief:", e)
            return null
        } finally {
            setAnalyzing(false)
        }
    }, [])

    const createProject = useCallback(async (brief: string): Promise<Project | null> => {
        setCreating(true)
        try {
            const res = await api.post<Project>("/projects/", { brief })
            return res.data
        } catch (e) {
            console.error("Failed to create project:", e)
            return null
        } finally {
            setCreating(false)
        }
    }, [])

    const fetchProjects = useCallback(async () => {
        setLoading(true)
        try {
            const res = await api.get<Project[]>("/projects/")
            setProjects(res.data)
        } catch (e) {
            console.error("Failed to fetch projects:", e)
        } finally {
            setLoading(false)
        }
    }, [])

    const deleteProject = useCallback(async (id: number): Promise<boolean> => {
        try {
            await api.delete(`/projects/${id}`)
            setProjects(prev => prev.filter(p => p.id !== id))
            return true
        } catch (e) {
            console.error("Failed to delete project:", e)
            return false
        }
    }, [])

    return {
        spec,
        setSpec,
        analyzing,
        analyzeBrief,
        creating,
        createProject,
        projects,
        loading,
        fetchProjects,
        deleteProject,
    }
}
