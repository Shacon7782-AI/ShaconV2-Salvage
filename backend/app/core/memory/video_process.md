# Video Implementation Process

## Overview
The "Antigravity" video system consists of two parts: a high-fidelity cinematic splash screen (frontend) and an AI-driven video analysis engine (backend).

## Frontend: Cinematic Splash Screen

### 1. Asset Placement
- The video file must be placed in the `frontend/public/` directory.
- The standard filename used across the project is `intro.mp4`.
- **Hurdle**: The `public/` directory was missing in previous builds because it was empty and ignored by Git. Always ensure a `.gitkeep` or a small asset (like `favicon.ico`) exists in `public/`.

### 2. Component Logic (`VideoIntro.tsx`)
- **Path**: `frontend/components/VideoIntro.tsx`
- **Autoplay Compliance**: Use `autoPlay`, `muted`, `loop`, and `playsInline`. Browsers block non-muted autoplay.
- **Session Memory**: Prevents the video from playing on every page refresh using `sessionStorage`.
```javascript
const SESSION_KEY = 'ag_splash_entered';
// ... mount logic ...
if (!sessionStorage.getItem(SESSION_KEY)) {
  setShow(true);
}
```
- **Auto-Transition**: A 10-second timer automatically enters the site if the user doesn't click the "ENTER" button.

### 3. Pathing & Imports
- In Next.js/Vite, use an absolute path starting with `/` to reference assets in the `public/` folder (e.g., `<source src="/intro.mp4" ... />`).
- **Dynamic Import**: If using Next.js, import the component with `ssr: false` to avoid hydration mismatches with `sessionStorage`.

## Backend: Gemini Video Analysis

### 1. Requirements
- `google-generativeai>=0.5.0`
- `GOOGLE_API_KEY` configured in `.env`.

### 2. Process Flow
1. **Upload**: Accept `UploadFile` via FastAPI.
2. **Buffer/Temp**: Save to a temporary file locally.
3. **GenAI Upload**: Use `genai.upload_file()` to push to Google's infrastructure.
4. **Processing State**: Poll the file state until it is `ACTIVE`.
5. **Analysis**: Prompt the model (e.g., `gemini-1.5-pro`) with the file object.
6. **Cleanup**: Call `genai.delete_file()` to manage cloud storage.

## Troubleshooting & "Ghost Corruption"
- **GDrive Sync**: On Windows, Google Drive sync latency can cause "Module not found" or "SyntaxError" if file handles are locked.
- **Docker Volume Shadowing**: Avoid bind-mounting source code on top of container directories if using GDrive. Prefer `docker cp` for one-way sync during debugging.
- **Bytecode Pollution**: Run `find . -name "*.pyc" -delete` if encountering phantom syntax errors that grep cannot find.
