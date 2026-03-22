# Pipeline Stages (PhD 2.0)

## Initial Data Sources (Candidate Context)

Before starting any pipeline, the system relies on:

- **CV Profile (Knowledge Graph)**: Hierarchical structure of Sections -> Entries -> Descriptions -> Skills.
- **Base Documents**: Repository of "Master Docs" (drafted CV, email templates, cover letters) that serve as starting points for deltas.

## Detailed Stages

### 1. Scrape (Source Capture)

- **Objective**: Get raw content and visual evidence of the job posting.
- **Input**: URL or job board identifier.
- **Output**: `raw/source_text.md` and `trace/error_screenshot.png`.
- **Workflow**: Identify the Application Method (Email, Fast Apply, Internal Site) as critical metadata.
- **Review**: Confirm capture integrity.

### 2. Translate if Needed (Normalization)

- **Objective**: Translate to standardize processing.
- **Input**: `raw/source_text.md`.
- **Output**: `translated/source_text.md`.
- **Workflow**: Language detection -> LLM translation preserving structure.
- **Review**: Not required.

### 3. Extract & Understand (Structuring)

- **Objective**: Identify requirements and risks.
- **Input**: Normalized text.
- **Output**: `nodes/extract/state.json`.
- **Workflow**: LLM extraction -> Entity mapping.
- **Human Review (HITL)**: Via Text Tagger. User validates text "spans" and ensures the system understood how and where to apply (destination metadata).

### 4. Match (Evidence Alignment)

- **Objective**: Link requirements with CV Profile.
- **Input**: Extraction JSON + CV Profile.
- **Output**: `nodes/match/state.json` with scores and reasoning.
- **Workflow**: Semantic comparison -> Justification generation.
- **Human Review (HITL)**: User can insert new links (additional evidence) that weren't automatically detected, enriching the match graph.

### 5. Strategy and Generation (Split into Two Sub-stages)

#### 5.1 Selection and Delta (JSON)

- **Objective**: Select which match evidence to use and enter "motivations" specific to this job posting.
- **Input**: `nodes/match/state.json`.
- **Output**: `nodes/strategy/delta.json` - Contains logical modifications to apply to Base Documents.
- **Workflow**: Evidence selection -> Enter specific motivations.

#### 5.2 Drafting and Composition (Markdown)

- **Objective**: Apply Delta to Base Documents to generate final text versions.
- **Input**: `nodes/strategy/delta.json` + Base Documents.
- **Output**: `nodes/drafting/{cv,cover_letter,email}.md` - Ready for editorial editing.
- **Workflow**: Templating (Jinja2) -> Context injection -> LLM refinement.

### 6. Render

- **Objective**: Convert final .md files to presentable formats.
- **Input**: `nodes/drafting/*.md`.
- **Output**: `final/*.pdf` or `*.docx` using defined templates.
- **Workflow**: LaTeX/PDF or Pandoc/Docx conversion.

### 7. Autopostulation / Package

- **Objective**: Execute application according to the method identified in Stage 1.
- **Input**: Final files.
- **Workflow**: If by email, prepare draft; if internal site, generate organized file package.

### 8. Feedback Loop (Closing the Loop)

- **Objective**: Inject user corrections back into the system.
- **Input**: All edits made in the UI.
- **Output**: `feedback/` - Corrections captured for future cycles.
- **Workflow**: All edits (Tagger, Match, final format) are saved and added to the "Evidence Tree".
- **UI Capability**: Interface must list and show all corrections from past pipelines influencing the current prompt.

## Gates (HITL Requirements)

| Stage | Required Gate |
|-------|---------------|
| Scrape | Approve/Reject visual capture |
| Extract | Approve/Reject text spans |
| Match | Approve/Reject evidence and links |
| Strategy | Approve/Reject delta |
| Render | Final checklist before sending |
