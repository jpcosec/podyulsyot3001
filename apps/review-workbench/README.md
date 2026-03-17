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

## Core Modules

- `src/api/client.ts`: backend API fetch layer
- `src/types/models.ts`: shared frontend contract types
- `src/views/ViewOneGraphExplorer.tsx`: match graph inspection view
- `src/views/ViewTwoDocToGraph.tsx`: source + extracted requirement view
- `src/views/ViewThreeGraphToDoc.tsx`: generated document review shell
- `src/components/GraphCanvas.tsx`: Cytoscape rendering component

## Local Commands

- Install: `npm --prefix apps/review-workbench install`
- Dev server: `npm --prefix apps/review-workbench run dev`
- Build: `npm --prefix apps/review-workbench run build`

## Current State

Implemented:

- Routing and stage-oriented navigation
- Cytoscape graph rendering in all three views
- API integration with backend timeline and view payload endpoints
- Responsive layout and status badges

Not implemented yet:

1. Editable graph mutations (node/edge update/delete)
2. Review decision submission from UI
3. Comment and feedback routing UI
4. Full Slate-based inline editing flow in View 3
