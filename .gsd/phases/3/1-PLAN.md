---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Frontend Foundation & Design System

## Objective
Set up the frontend architecture served by FastAPI static files. Create the design system (CSS variables, layout, typography) and the shell app structure with navigation. All pages will be vanilla HTML/CSS/JS — no build step required.

## Context
- c:\PharMgmt\src\pharmgmt\main.py — FastAPI app with static file mount
- .gsd/SPEC.md — Offline-first, no paid APIs, runs on low-end devices
- Phase 3 requires 6+ pages, responsive design

## Tasks

<task type="auto">
  <name>Create design system and app shell</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\index.html
    c:\PharMgmt\src\pharmgmt\static\css\index.css
    c:\PharMgmt\src\pharmgmt\static\css\components.css
    c:\PharMgmt\src\pharmgmt\static\js\app.js
    c:\PharMgmt\src\pharmgmt\static\js\api.js
    c:\PharMgmt\src\pharmgmt\static\js\router.js
  </files>
  <action>
    Design system (`index.css`):
    - CSS custom properties (dark theme primary): --bg-primary: #0f0f23, --bg-secondary: #1a1a36, --bg-card: #1e1e3a, --accent: #6366f1, --accent-hover: #818cf8, --text-primary: #e2e8f0, --text-secondary: #94a3b8, --success: #22c55e, --warning: #f59e0b, --danger: #ef4444, --border: #2d2d52
    - Typography: Google Font 'Inter' (400, 500, 600, 700)
    - Spacing scale: 4px increments
    - Border radius: --radius-sm: 6px, --radius-md: 10px, --radius-lg: 16px
    - Transitions: --transition: 0.2s ease
    - Glassmorphism cards: background: rgba(30,30,58,0.8), backdrop-filter: blur(10px)
    - Responsive breakpoints: 768px, 1024px, 1280px

    Components (`components.css`):
    - .btn (primary, secondary, ghost, danger variants with hover/active states)
    - .card (glassmorphism with border glow effect)
    - .stat-card (icon, value, label, trend indicator)
    - .table (dark styled with hover rows, alternating stripes)
    - .badge (status badges: success, warning, danger, info)
    - .input, .select (dark-styled form controls)
    - .modal (overlay + centered dialog)
    - .toast (notification popups, slide-in animation)
    - .sidebar (collapsible nav, active state)
    - .header (top bar with logo, search, actions)
    - .empty-state (illustration placeholder + CTA)
    - .skeleton (loading shimmer animation)
    - .progress-bar (animated fill)
    - .dropdown (click-to-open menu)
    - .search-input (with icon, clear button)
    - .file-drop (drag & drop zone with dashed border, hover glow)
    - .confidence-bar (horizontal bar colored by confidence level)

    App shell (`index.html`):
    - Single-page app with hash-based routing
    - Sidebar navigation: Dashboard, Bills, Upload, Products, Staging Review
    - Main content area with page container
    - Top header with app name and search
    - SEO meta tags

    Router (`router.js`):
    - Hash-based SPA router (#/dashboard, #/bills, #/bills/:id, #/upload, #/products, #/staging)
    - Route registration with lazy page loading
    - Active nav highlighting
    - 404 fallback

    API client (`api.js`):
    - fetch wrapper with base URL, error handling
    - Methods: getHealth(), getDocuments(skip, limit), getDocument(id), uploadPdf(file), getStats()
    - Response normalization

    App init (`app.js`):
    - Initialize router, register pages
    - Sidebar toggle for mobile
    - Global error handling
    - Toast notification system

    IMPORTANT:
    - All pages load instantly (no build step)
    - Dark theme is the default (premium feel)
    - Mobile-first responsive design
    - All interactive elements have unique IDs for testing
  </action>
  <verify>
    Start server: .venv\Scripts\python -m pharmgmt.cli.commands serve
    Open browser: http://localhost:8000/static/index.html
    Verify: shell renders with sidebar, navigation works between empty pages
  </verify>
  <done>App shell loads, sidebar navigates between routes, dark theme renders correctly on desktop and mobile</done>
</task>

## Success Criteria
- [ ] Design system with CSS variables and component styles
- [ ] SPA shell with hash-based routing
- [ ] Sidebar navigation between 5 pages
- [ ] API client wrapper connecting to FastAPI backend
- [ ] Responsive layout (mobile sidebar collapses)
