# Frontend Dashboard

## Tech Stack

- **Framework:** Next.js 14 (App Router compatible)
- **Language:** TypeScript
- **Styling:** TailwindCSS with custom dark theme
- **Charts:** Recharts
- **API Client:** Axios
- **Markdown:** react-markdown

## Setup

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

Requires backend running at `http://localhost:8000`.

## Features

### Dashboard Tabs

| Tab | Content |
|-----|---------|
| Overview | Pipeline bar chart + flow diagram |
| Tasks | Filterable task list with detail view |
| Approvals | Live HITL approval queue with approve/reject buttons |
| Logs | Real-time log viewer with level filtering |
| CEO Briefing | Weekly executive report rendered as markdown |

### Status Cards

Seven live counters (one per pipeline stage) with color coding:
- Blue → Inbox
- Yellow → In Progress
- Purple → Plans
- Orange → Pending Approval
- Green → Approved
- Red → Rejected
- Emerald → Done

### Auto-refresh

Dashboard polls the backend API every 15 seconds automatically.

### Approval Actions

Judges and users can approve/reject tasks directly from the dashboard UI — no need to edit files in Obsidian.

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Production Build

```bash
npm run build
npm start
```

## Component Structure

```
frontend/
├── pages/
│   ├── _app.tsx           Next.js app wrapper
│   └── index.tsx          Main dashboard page
├── components/
│   ├── Layout.tsx         Header + footer shell
│   ├── StatusCard.tsx     Colored metric card
│   ├── PipelineChart.tsx  Recharts bar chart
│   ├── PipelineBoard.tsx  Flow visualization
│   ├── TaskList.tsx       Filterable task table
│   ├── ApprovalQueue.tsx  HITL approval UI
│   ├── LogViewer.tsx      Live log terminal
│   └── CeoBriefing.tsx    Markdown briefing viewer
├── lib/
│   ├── api.ts             Axios API client
│   └── types.ts           TypeScript interfaces
└── styles/
    └── globals.css        Tailwind base + custom theme
```
