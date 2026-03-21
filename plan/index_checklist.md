# Planning Checklist

This is the single planning checklist for active work.

## 01 UI — ui-redesign branch (Terran Command design system)

### Fase 0 — Foundation (Router + Layouts + Portfolio)
- [ ] `utils/cn.ts` — clsx + tailwind-merge helper
- [ ] `main.tsx` — QueryClientProvider wrapper
- [ ] `AppShell.tsx` — LeftNav + `<Outlet />`
- [ ] `JobWorkspaceShell.tsx` — Pipeline TopBar + nested `<Outlet />`
- [ ] `Badge.tsx` atom — forwardRef, cn(), variant prop
- [ ] `usePortfolioSummary.ts` + `PortfolioDashboard.tsx` stub
- [ ] Mock toggle: `VITE_MOCK=true` via vite alias
- [ ] Mock fixtures: `portfolio.json`, `timeline_201397.json`, `timeline_999001.json`

### Fase 1 — Job Flow Inspector (B0)
- [ ] `useJobTimeline.ts`
- [ ] `JobFlowInspector.tsx` — timeline visual con pipeline stages

### Fase 2 — Data Explorer (A2)
- [ ] `useBrowseExplorer.ts`
- [ ] `DataExplorer.tsx` — file tree + raw content viewer

### Fase 3 — Scrape Diagnostics (B1)
- [ ] `useStageOutputs.ts`
- [ ] `ScrapeDiagnostics.tsx` — metadata + texto extraído

### Fase 4 — Extract & Understand (B2)
- [ ] `useViewTwo.ts` + `useExtractState.ts`
- [ ] `SourceTextPane.tsx` + `RequirementList.tsx` + `RequirementItem.tsx`
- [ ] `ExtractControlPanel.tsx`
- [ ] `ExtractUnderstand.tsx`

### Fase 5 — Match (B3)
- [ ] `useViewOne.ts` + `useMatchState.ts`
- [ ] `MatchGraphCanvas.tsx` (ReactFlow + dagre)
- [ ] `RequirementNode.tsx` + `ProfileNode.tsx` + `EdgeScoreBadge.tsx`
- [ ] `EvidenceBankPanel.tsx` + `MatchControlPanel.tsx` + `MatchDecisionModal.tsx`
- [ ] `Match.tsx`

### Fase 6 — Generate Documents PREP_MATCH (B4)
- [ ] `useViewThree.ts` + `useDocumentSave.ts`
- [ ] `DocumentTabs.tsx` + `DocumentEditor.tsx` + `ContextPanel.tsx`
- [ ] `DocApproveBar.tsx` + `RegenModal.tsx`
- [ ] `GenerateDocuments.tsx`

### Fase 7 — Package & Deployment (B5)
- [ ] `usePackageFiles.ts`
- [ ] `MissionSummaryCard.tsx` + `PipelineChecklist.tsx`
- [ ] `PackageFileList.tsx` + `DeploymentCta.tsx`
- [ ] `PackageDeployment.tsx`

### Fase 8 — Default Document Gates (B4b) ⚠️ BLOCKED — requiere backend
- [ ] `useDocumentGate.ts` + `useGateDecision.ts`
- [ ] Prop `mode="default_gate"` en `GenerateDocuments.tsx`

### Fase 9 — Base CV Editor (A3)
- [ ] `useCvProfileGraph.ts` + `useSaveCvGraph.ts`
- [ ] `CvGraphEditor.tsx` (ReactFlow)
- [ ] `BaseCvEditor.tsx`

### Fase 10 — Application Context Gate (B3b) ⚠️ BLOCKED — requiere backend
- [ ] `useApplicationContext.ts` + `useContextDecision.ts`
- [ ] `ContextBrief.tsx` + `MatchReferencePanel.tsx` + `ContextDecisionBar.tsx`
- [ ] `ApplicationContext.tsx`

### Reglas globales
- Sin datos hardcodeados — todo dato sale del mock/API
- Todos los E2E via TestSprite
- Componentes dumb en `pages/`, lógica en `features/`
- `cn()` para toda composición de clases Tailwind

---

## 02 AI — Phase 1: LLM Wrappers and Structured Output ✅

- [x] ChatGoogleGenerativeAI.with_structured_output() for extract_understand
- [x] contact_info stable extraction
- [x] salary_grade strictly optional
- [x] Deterministic TextSpan via resolve_span (no LLM offsets)
- [x] LangSmith structured config (LLMConfig + trace_section)
- [x] LangSmith traces for extract_understand and match stages

## 03 Scrapper — Phase 1: Robust Scraping ✅

- [x] PlaywrightFetcher with try/except
- [x] error_screenshot.png on failures
- [x] bot_profile persistent directory
- [x] HTTP -> Playwright -> LLM fallback cascade
- [x] Artifacts under nodes/scrape/ and raw/source_text.md

---

## Rules

- Mark a phase complete only when code, verification, and changelog agree.
- Archive obsolete planning docs instead of letting them drift in active folders.
- Put subsystem specs in `docs/`, not in `plan/`.
- All E2E tests via TestSprite — never raw Playwright test files.
- No hardcoded data in components — data always from API/mock fixtures.
