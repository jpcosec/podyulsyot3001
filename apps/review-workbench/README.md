# Review Workbench App

Current-state documentation for the ADR-001 UI scaffold.

## Purpose

React + TypeScript workbench for review flows:

1. View 1: Graph Explorer
2. View 2: Document to Graph
3. View 3: Graph to Document

## Routes

- `/` -> `PortfolioPage`
- `/jobs/:source/:jobId` -> `JobStagePage`
- `/sandbox` -> `SandboxPage` (fake-data component playground)
- `/sandbox/text_tagger` -> `TextTaggerPage` (dedicated highlight-to-node editor)
- `/sandbox/cv_graph` -> `CvGraphEditorPage` (React Flow deterministic CV graph editor)
- `/text-tagger` -> `TextTaggerPage` (alias)
- `/cv-graph` -> `CvGraphEditorPage` (alias)
- `/cv-graph/entry/:entryId` -> `CvGraphEditorPage` (entry-focused deep link)
- `/cv-graph/skill/:skillId` -> `CvGraphEditorPage` (skill-focused deep link)

## Core Modules

- `src/api/client.ts`: backend API fetch layer
- `src/types/models.ts`: shared frontend contract types
- `src/views/ViewOneGraphExplorer.tsx`: match graph inspection view
- `src/views/ViewTwoDocToGraph.tsx`: source + extracted requirement view
- `src/views/ViewThreeGraphToDoc.tsx`: generated document review shell
- `src/components/GraphCanvas.tsx`: Diagrammatic-UI graph rendering component
- `src/sandbox/pages/CvGraphEditorPage.tsx`: React Flow CV graph editor for base profile
- `src/sandbox/components/cv-graph/*`: custom React Flow node components (`EntryNode`, `SkillBallNode`, `GroupNode`)
- `src/sandbox/lib/mastery-scale.ts`: mastery scale database and category hue/intensity color mapping

## Local Commands

- Install: `npm --prefix apps/review-workbench install`
- Dev server: `npm --prefix apps/review-workbench run dev`
- Build: `npm --prefix apps/review-workbench run build`

## Current State

Implemented:

- Routing and stage-oriented navigation
- Diagrammatic-UI graph rendering in all three views
- API integration with backend timeline and view payload endpoints
- Responsive layout and status badges
- Component sandbox with fake data for isolated UI inspection (`/sandbox`)
- Dedicated text tagger route without sandbox noise (`/sandbox/text_tagger`)
- Drag-to-category text tagger (`@dnd-kit/core`) with two-level tab-like categorization (main + subcategory), requirement red-scale visual system, colorful info subcategories, exact captured text storage, click/keyboard quick-add, whole-card draggable recategorization, card-click collapse/expand behavior, and searchable scrollable note list
- Dedicated CV graph editor route (`/sandbox/cv_graph`) with preserved box-in-box document structure (group nodes containing entry nodes), entry click-to-expand editing panel (expands to the right), and connection-based skill matching
- Repurposed side panel as skill palette: unrelated skills pool, selected skill editor, and mastery scale legend
- Skill balls with always-visible labels, category color, and mastery intensity/value mapping via shared scale database (`src/sandbox/lib/mastery-scale.ts`)
- Tailwind CSS v4 integration using Vite plugin (`@tailwindcss/vite`) while keeping existing CSS custom properties and module-specific classes
- Entry/group expand actions trigger deterministic top-level dagre re-layout with React Flow node-internals refresh for stable handle positioning
- Loading states and accessibility polish for CV graph editor (skeleton placeholders + consistent focus-visible rings across interactive controls)
- Frontend API integration for CV profile graph endpoint (`GET /api/v1/portfolio/cv-profile-graph`) while keeping legacy base graph endpoint available

Not implemented yet:

1. Persisting editable graph mutations to backend storage (current editing is client-side)
2. Review decision submission from UI
3. Comment and feedback routing UI
4. Full inline editing + node-linked highlight flow integrated into View 3 (currently available as component/sandbox capability)
