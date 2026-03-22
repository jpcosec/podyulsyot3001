# Data Contracts & Deployment

## 1. Data Contract: `document_delta.json` (Stage 5.1)

The "Delta" is a set of instructions telling the drafting engine how to adapt Base Documents (Master Docs) for the specific job posting.

```json
{
  "master_doc_id": "string",       // Reference to original document (e.g., cv_academico_v2.md)
  "puntos_narrativos": [           // "Hooks" or motivations entered in UI
    "string"
  ],
  "transformaciones": [
    {
      "target": "string",          // Component to change (e.g., summary, experience_01, cover_letter_body)
      "op": "REPLACE | ENHANCE | HIDE",
      "evidencia_ref": ["string"], // Evidence Bank IDs
      "estilo_override": "string"  // Tone instructions from historical ReviewNodes
    }
  ]
}
```

## 2. Stage 7: Autopostulation and Packaging

This stage depends entirely on the Application Method identified in the initial scrape.

### Scenario A: Email Application

| Element | Description |
|---------|-------------|
| **UI Action** | "Prepare Email Draft" button |
| **Result** | Opens email client with body, subject, and PDFs attached |
| **Package** | Folder with `email_body.txt` and final rendered documents |

### Scenario B: Internal Portal / Form (Fast Apply)

| Element | Description |
|---------|-------------|
| **UI Action** | "Download Application Package" button |
| **Result** | `.zip` file named with `job_id` containing everything in correct order |
| **Checklist** | List of common fields (profile URL, LinkedIn, Phone) for quick copy-paste |

## 3. Stage 8: Evidence Tree and Learning

The system consolidates interactions so the "Tree" grows.

### Evidence Aggregation

```
ReviewNode (AUGMENTATION in Match)
        ↓
Promotion to Global Evidence Bank
        ↓
data/master/evidence/
```

### Prompt Transparency

Before each generation, system shows which "lessons" it's using:
- "Applying your format correction from application #201397"
- "Evidence 'Project Y' suggested from previous matches"

## 4. Final Data Architecture Summary

| Folder / File | Function | HITL |
|---------------|---------|------|
| `data/master/` | Your base identity and validated evidence | Read |
| `nodes/review/` | Generic ReviewNodes (comments and corrections) | Write |
| `nodes/strategy/` | `document_delta.json` with change logic | Write |
| `final/` | Ready-to-send artifacts (PDF, ZIP) | Visual Validation |

## 5. Complete Data Flow

```
[data/master]  ──evidences──>  [scrape]  ──text──>  [extract]  ──requirements──>  [match]
                                                                                        │
                                                                                        ↓
                                                           [global evidence_bank]  <──augmentation
                                                                                        │
                                                                                        ↓
                                                           [strategy/delta]  ──>  [drafting]
                                                                                        │
                                                                                        ↓
                                                           [render]  ──>  [final/package]
```
