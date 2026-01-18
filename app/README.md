# PrepAIr Frontend

React + TypeScript + Vite frontend providing the user interface for CV analysis, interview practice, and progress tracking.

## 🏗️ Architecture

- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State:** LocalStorage + React hooks
- **Voice:** Web Speech API (browser-native TTS/STT)

## 📁 Structure

```
app/
├── index.html          # HTML entry point
├── vite.config.ts      # Vite configuration (proxy to backend)
├── package.json        # Node dependencies
├── src/
│   ├── main.tsx        # React entry point
│   ├── App.tsx         # Main app component (routes)
│   ├── App.css         # Global styles
│   ├── index.css       # Base styles
│   ├── api/
│   │   └── client.ts   # API client (typed functions)
│   ├── pages/          # Page components
│   │   ├── Landing.tsx              # Landing page
│   │   ├── DocumentSetup.tsx        # CV + JD input
│   │   ├── CvImprove.tsx            # CV analysis & editing
│   │   ├── PreInterview.tsx         # Plan review & settings
│   │   ├── InterviewRoom.tsx        # Voice/text interview
│   │   ├── Done.tsx                 # Interview complete
│   │   ├── FeedbackPlaceholder.tsx  # Placeholder
│   │   └── Dashboard.tsx            # Readiness progress
│   └── voice/          # Voice modules
│       ├── tts.ts      # Text-to-speech (Web Speech API)
│       └── stt.ts      # Speech-to-text (Web Speech Recognition)
```

## 🚀 Setup

### Prerequisites

- Node.js 18+
- Backend running on port 8000

### Installation

```bash
cd app
npm install
```

### Configuration

Optional: Set `VITE_BACKEND_URL` in `.env` (defaults to `http://localhost:8000`)

```bash
VITE_BACKEND_URL=http://localhost:8000
```

### Running

```bash
npm run dev
```

Frontend available at `http://localhost:5173`

Vite automatically proxies `/api/*` requests to backend.

### Building for Production

```bash
npm run build
```

Output: `dist/` folder (static files to serve)

## 🎨 Pages & Features

### Landing (`/`)
- Choose: Start Interview, Improve CV, or Dashboard
- Ensures user exists (creates if needed)

### Document Setup (`/setup`)
- Input CV text and Job Description
- Two actions:
  - **Analyze & Improve CV** → CV Improve page
  - **Skip to Interview** → Pre-Interview page

### CV Improve (`/cv-improve`)
- Shows match score, strengths, gaps, suggestions
- Editable CV textarea
- **Save CV** → Create new CV version
- **Proceed to Interview** → Start interview with improved CV

### Pre-Interview (`/pre-interview`)
- Shows session plan summary
- Settings toggles:
  - Voice On/Off
  - Captions On/Off (tooltip: may reduce realism)
  - Realism Mode
- **Start** → Interview Room

### Interview Room (`/interview/:sessionId`)
- **Timer** and progress bar
- **Question display** with "Repeat Question" button
- **Code Whiteboard** button (for code questions) - modal popup
- **Voice recording** button (mic) with live transcript
- **Text input** fallback if voice unsupported
- **Submit Answer** button
- **End Interview** button

**Code Questions:**
- "Open Code Whiteboard" button appears
- Modal popup with code editor (monospace textarea)
- Code submitted separately with transcript

### Done (`/done/:sessionId`)
- Completion message
- **Continue to Feedback** → Feedback Placeholder
- **View Dashboard** → Dashboard

### Dashboard (`/dashboard`)
- Readiness score with progress bar
- Breakdown: CV Score, Interview Score, Practice Score
- Trend chart (last 10 snapshots)
- Action buttons: History, Self-Progress, OCEAN Test

### Feedback Placeholder (`/feedback/:sessionId`)
- Placeholder (feedback not implemented)

## 🎤 Voice Features

### Text-to-Speech (TTS)
- Uses `window.speechSynthesis`
- Speaks interview questions
- "Repeat Question" button replays

### Speech-to-Text (STT)
- Uses `webkitSpeechRecognition` (Chrome/Edge)
- Continuous recognition with interim results
- Falls back to textarea if unsupported
- Live transcript updates during recording

**Browser Support:**
- ✅ Chrome/Edge: Full support
- ⚠️ Firefox: Limited support
- ❌ Safari: May require workarounds

## 🔌 API Integration

All API calls through `src/api/client.ts`:

```typescript
import { api } from './api/client';

// Ensure user
const { user_id } = await api.ensureUser();

// Ingest CV
const { cv_version_id } = await api.ingestCV(userId, cvText);

// Start interview
const { session_id } = await api.startInterview(...);

// Submit answer
const result = await api.nextInterview(sessionId, transcript, code);
```

See `src/api/client.ts` for all available functions.

## 💾 State Management

### LocalStorage
Stores session data:
- `userId` - Current user ID
- `cvVersionId` - Active CV version
- `jobSpecId` - Current job spec
- `cvText` - CV text (temporary)

### React State
- Component-level state for UI (forms, modals, etc.)
- No global state manager (Redux/Context) needed for MVP

## 🎯 User Flow

```
Landing
  ├─→ Document Setup
  │     ├─→ CV Improve → Pre-Interview → Interview Room → Done → Feedback
  │     └─→ Pre-Interview → Interview Room → Done → Feedback
  └─→ Dashboard
```

## 🛠️ Development

### Adding a New Page

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation link where needed

### Styling

- Page-specific CSS in `src/pages/*.css`
- Global styles in `src/App.css`
- Uses CSS (no CSS-in-JS or preprocessors)

### Environment Variables

Use `import.meta.env.VITE_*` for env vars:

```typescript
const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
```

## 🔍 Troubleshooting

**Cannot connect to backend:**
- Ensure backend running on port 8000
- Check `vite.config.ts` proxy settings
- Verify `VITE_BACKEND_URL` if set

**Voice not working:**
- Use Chrome or Edge browser
- Check browser permissions (microphone)
- Falls back to text input automatically

**Build errors:**
- Clear `node_modules` and reinstall
- Check Node.js version (18+)
- Verify TypeScript errors

## 📝 Notes

- TypeScript strict mode enabled
- React Router handles all navigation
- No external UI library (pure CSS)
- Code whiteboard uses modal popup (not inline)
- OCEAN test button opens `/ocean-test` (route TBD)
