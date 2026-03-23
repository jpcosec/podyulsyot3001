# Planning Checklist

This is the single planning checklist for active work.

## Workflow Rules

1. **Commit OBLIGATORIO** al cerrar cada fase — seguir formato:
   ```
   feat(ui): implement <view name> (<spec-id>)
   
   - <component 1>
   - <component 2>
   ...
   - Connected to <hook names>
   ```
2. **Changelog** — agregar entrada en `changelog.md`
3. **Checklist** — marcar `[x]` en este archivo

## 01 UI — ui-redesign branch (Terran Command design system)

### Fase 0 — Foundation (Router + Layouts + Portfolio) ✅
- [x] `utils/cn.ts` — clsx + tailwind-merge helper
- [x] `main.tsx` — QueryClientProvider wrapper
- [x] `AppShell.tsx` — LeftNav + `<Outlet />`
- [x] `JobWorkspaceShell.tsx` — Pipeline TopBar + nested `<Outlet />`
- [x] `Badge.tsx` atom — forwardRef, cn(), variant prop
- [x] `types/api.types.ts` — PortfolioSummary, ViewPayload, GraphNode, GraphEdge, etc.
- [x] `types/ui.types.ts` — MatchNodeData, ExtractEditorState, DocumentDraft, ExplorerTreeNode, GateDecisionState
- [x] Mock fixtures y client

### Fase 0 — A1 Portfolio Dashboard ✅
- [x] `usePortfolioSummary.ts`
- [x] `PortfolioTable.tsx`
- [x] `DeadlineSidebar.tsx`, `RecentArtifacts.tsx`, `SystemStatus.tsx`
- [x] `PortfolioDashboard.tsx`

### Fase 1 — B0 Job Flow Inspector ✅
- [x] `useJobTimeline.ts`
- [x] `JobFlowInspector.tsx` — timeline visual con pipeline stages
- [x] `HitlCtaBanner.tsx`, `JobMetaPanel.tsx`, `PipelineTimeline.tsx`, `StageRow.tsx`

### Atoms pre-Fase 2 ✅
- [x] `Button.tsx` — variant: primary|ghost|danger, size: sm|md, loading?: boolean
- [x] `Icon.tsx` — Lucide wrapper, name prop, size: xs|sm|md
- [x] `Spinner.tsx` — CSS spinner, size: xs|sm|md, color primario
- [x] `SplitPane.tsx` (molecule) — wrapper de react-resizable-panels

### Fase 2 — A2 Data Explorer ✅
- [x] `useExplorerBrowse.ts`
- [x] `ExplorerTree.tsx`, `BreadcrumbNav.tsx`, `FilePreview.tsx`, `JsonPreview.tsx`, `MarkdownPreview.tsx`, `ImagePreview.tsx`
- [x] `DataExplorer.tsx`

### Fase 3 — B1 Scrape Diagnostics ✅
- [x] `useArtifacts.ts`
- [x] `ScrapeMetaCard.tsx`, `SourceTextPreview.tsx`, `ErrorScreenshot.tsx`, `ScrapeControlPanel.tsx`
- [x] `ScrapeDiagnostics.tsx`

### Atoms pre-Fase 4 ✅
- [x] `Tag.tsx` — inline span, category: skill|req|risk, border-l-2 color-coded

### Fase 4 — B2 Extract & Understand ✅
- [x] `useViewExtract.ts`
- [x] `SourceTextPane.tsx`, `RequirementList.tsx`, `RequirementItem.tsx`, `ExtractControlPanel.tsx`
- [x] `ExtractUnderstand.tsx`

### Fase 5 — B3 Match ✅
- [x] `useViewMatch.ts`, `useEvidenceBank.ts`, `useGateDecide.ts`, `useEditorState.ts`
- [x] `MatchGraphCanvas.tsx`, `RequirementNode.tsx`, `ProfileNode.tsx`, `EdgeScoreBadge.tsx`
- [x] `EvidenceBankPanel.tsx`, `MatchControlPanel.tsx`, `MatchDecisionModal.tsx`
- [x] `Match.tsx`

### Atoms pre-Fase 6 ✅
- [x] `Kbd.tsx` — keyboard shortcut display, keys: string[], estilo mono

### Fase 6 — B4 Generate Documents ✅
- [x] `useViewDocuments.ts`, `useDocumentSave.ts`, `useGateDecide.ts`
- [x] `DocumentTabs.tsx`, `DocumentEditor.tsx`, `ContextPanel.tsx`
- [x] `DocApproveBar.tsx`, `RegenModal.tsx`
- [x] `GenerateDocuments.tsx`

### Fase 7 — B5 Package & Deployment ✅
- [x] `usePackageFiles.ts`
- [x] `MissionSummaryCard.tsx`, `PipelineChecklist.tsx`, `PackageFileList.tsx`, `DeploymentCta.tsx`
- [x] `PackageDeployment.tsx`

### Fase 8 — B4b Default Document Gates ⚠️ BLOCKED — requiere backend
- [ ] `useDocumentGate.ts`, `useGateDecision.ts`
- [ ] Prop `mode="default_gate"` en `GenerateDocuments.tsx`

### Fase 9 — A3 Base CV Editor ✅
- [x] `useCvProfileGraph.ts`, `useSaveCvGraph.ts`
- [x] `CvGraphCanvas.tsx`, `EntryNode.tsx`, `SkillNode.tsx`, `NodeInspector.tsx`, `ProfileStats.tsx`
- [x] `BaseCvEditor.tsx`
- [x] **E2E tests** — all TestSprite tests passing (TC001–TC049 suite, 100%)

### Fase 11 — Component Map Compliance ✅
- [x] `IntelligentEditor` — fixed decorations (StateField), added `onSpanSelect` prop
- [x] `SourceTextPane` → uses IntelligentEditor (tag-hover mode)
- [x] `DocumentEditor` → uses IntelligentEditor (fold mode)
- [x] `ScrapeControlPanel` → uses ControlPanel molecule
- [x] `ExtractControlPanel` → uses ControlPanel molecule
- [x] `MatchControlPanel` → uses ControlPanel molecule (with children for detail pane)
- [x] `GraphCanvas` → added `onConnect` prop
- [x] `MatchGraphCanvas` → uses GraphCanvas organism
- [x] `ExplorerTree` → delegates to FileTree organism
- [x] `JsonPreview` → uses IntelligentEditor (fold/json)
- [x] `MarkdownPreview` → uses IntelligentEditor (fold/markdown)
- [x] `CvGraphCanvas` — kept as-is (uses parentId/extent, incompatible with generic GraphCanvas)
- [x] **E2E tests** — TestSprite suite run; refactored-component tests passing (TC011, TC012, TC019, TC025, TC007)

### Fase 10 — B3b Application Context Gate ⚠️ BLOCKED — requiere backend
- [ ] `useApplicationContext.ts`, `useContextDecision.ts`
- [ ] `ContextBrief.tsx`, `MatchReferencePanel.tsx`, `ContextDecisionBar.tsx`
- [ ] `ApplicationContext.tsx`

---

## Rules

- Mark a phase complete only when code, verification, and changelog agree.
- **Commit message is OBLIGATORY** — follow format in `README.md`
- **Changelog entry is OBLIGATORY** — add to `changelog.md`
- All E2E tests via TestSprite — never raw Playwright test files.
- No hardcoded data in components — data always from API/mock fixtures.
- Components dumb in `pages/`, logic in `features/`
- `cn()` for all Tailwind class composition
