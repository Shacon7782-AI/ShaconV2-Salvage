// Type declarations for GrapesJS plugins without TypeScript definitions

declare module 'grapesjs-preset-webpage' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-plugin-forms' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-tabs' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-navbar' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-component-countdown' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-typed' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}

declare module 'grapesjs-touch' {
    const plugin: (editor: import('grapesjs').Editor, options?: Record<string, unknown>) => void;
    export default plugin;
}
