// Style Archetypes Configuration
// Each archetype has a unique font pairing and aesthetic

export interface StyleArchetype {
    id: string
    name: string
    description: string
    primaryFont: string
    secondaryFont: string | null
    googleFontsImport: string
    cssVariables: {
        fontHeading: string
        fontBody: string
    }
    preview: {
        bgColor: string
        textColor: string
        accentColor: string
    }
}

export const styleArchetypes: StyleArchetype[] = [
    {
        id: "modern",
        name: "Modern / Clean",
        description: "Unified geometric modernism with sharp brand character",
        primaryFont: "Plus Jakarta Sans",
        secondaryFont: null,
        googleFontsImport: "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap",
        cssVariables: {
            fontHeading: "'Plus Jakarta Sans', sans-serif",
            fontBody: "'Plus Jakarta Sans', sans-serif",
        },
        preview: {
            bgColor: "#ffffff",
            textColor: "#1a1a1a",
            accentColor: "#0066ff",
        },
    },
    {
        id: "professional",
        name: "Professional",
        description: "Balances data competence with utility; ideal for trust-based industries",
        primaryFont: "Manrope",
        secondaryFont: "Inter",
        googleFontsImport: "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap",
        cssVariables: {
            fontHeading: "'Manrope', sans-serif",
            fontBody: "'Inter', sans-serif",
        },
        preview: {
            bgColor: "#f8f9fa",
            textColor: "#212529",
            accentColor: "#2563eb",
        },
    },
    {
        id: "elegant",
        name: "Elegant",
        description: "Soft Modern editorial trend; refined, high-contrast, sophisticated",
        primaryFont: "Instrument Serif",
        secondaryFont: "DM Sans",
        googleFontsImport: "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;600&display=swap",
        cssVariables: {
            fontHeading: "'Instrument Serif', serif",
            fontBody: "'DM Sans', sans-serif",
        },
        preview: {
            bgColor: "#faf8f5",
            textColor: "#2d2a26",
            accentColor: "#9b7b5b",
        },
    },
    {
        id: "tech",
        name: "Tech / Startup",
        description: "Deep Tech aesthetic; pixel-precise ink traps signal innovation",
        primaryFont: "Sora",
        secondaryFont: "Space Grotesk",
        googleFontsImport: "https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600&display=swap",
        cssVariables: {
            fontHeading: "'Sora', sans-serif",
            fontBody: "'Space Grotesk', sans-serif",
        },
        preview: {
            bgColor: "#0a0a0a",
            textColor: "#fafafa",
            accentColor: "#00d4ff",
        },
    },
    {
        id: "friendly",
        name: "Friendly",
        description: "Humanist warmth without childish roundness; maintains professional trust",
        primaryFont: "Figtree",
        secondaryFont: "Nunito Sans",
        googleFontsImport: "https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Nunito+Sans:wght@400;500;600&display=swap",
        cssVariables: {
            fontHeading: "'Figtree', sans-serif",
            fontBody: "'Nunito Sans', sans-serif",
        },
        preview: {
            bgColor: "#fffbf5",
            textColor: "#3d3d3d",
            accentColor: "#ff6b35",
        },
    },
]

export function getArchetypeById(id: string): StyleArchetype | undefined {
    return styleArchetypes.find((a) => a.id === id)
}
