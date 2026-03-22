# Document Delta & Evidence Tree

## 1. The "Delta" Concept

The Delta is not the complete document, but a series of transformation instructions applied to your "Master Docs". This allows, if you update your base CV in the future, new applications will automatically inherit those improvements.

## 2. Contract Schema: `document_delta.json`

File generated at the end of Stage 5.1, input for final drafting.

```json
{
  "documento_id": "string",        // Reference to Master Doc (e.g., master_cv_v2, standard_letter_en)
  "motivaciones_clave": [          // Narrative hooks for this specific application
    "string"
  ],
  "modificaciones": [
    {
      "selector": "string",        // Section/paragraph ID (e.g., experience:company_a, letter:intro)
      "accion": "REPLACE | HIGHLIGHT | OMIT | APPEND",
      "evidencia_ref": "string",   // Evidence tree ID
      "instrucciones_estilo": "string"  // Tone preferences from historical ReviewNodes
    }
  ]
}
```

## 3. Consolidated Evidence Tree (Stage 8)

Stage 8 takes all corrections and organizes them into the Global Evidence Arrangement:

| Type | Source | Description |
|------|--------|-------------|
| **Static Evidence** | `profile.json` | Titles, past jobs (base data) |
| **Dynamic Evidence (HITL)** | ReviewNodes AUGMENTATION | Links and achievements manually added in Stage 4 |
| **Exclusion Filters** | ReviewNodes REJECTION | Skills/experiences marked as undesirable for certain roles |

### Consolidation Flow

```
data/jobs/<source>/<job_id>/review/*.json
                ↓
    [Stage 8: Aggregator]
                ↓
    data/master/evidence_bank/
    data/master/filters/
```

## 4. UI Visualization (Transparency)

To fulfill the requirement of showing everything that generates the prompt:

### "Influences" Panel

Before generating the document, UI shows:
- "Style correction applied from application X"
- "New evidence 'Project Y' included from previous suggestion"

### Origin Tracking (Provenance)

When clicking on a generated paragraph, UI highlights:
- Which ReviewNode originated that phrase
- Which part of the CV Profile was used as base

## 5. Data Architecture Summary

| Component | Location | Function |
|-----------|----------|---------|
| CV Profile | `data/master/profile.json` | Your structured base history |
| Evidence Bank | `data/master/evidence/` | HITL-validated links and proofs |
| Review Nodes | `data/jobs/<source>/<job_id>/review/` | Stage-specific corrections |
| Document Delta | `data/jobs/<source>/<job_id>/strategy/` | Change instructions for current application |
| Filters | `data/master/filters/` | Learned exclusions from past applications |
