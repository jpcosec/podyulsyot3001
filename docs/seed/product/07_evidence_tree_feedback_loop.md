# Evidence Tree & Feedback Loop

## 1. The Evidence Tree (Personalized Knowledge Base)

Dynamic aggregation of base sources and validated corrections:

- **CV Profile (Structured)**: Graph of sections (experience, education) with entries, descriptions, and skills.
- **Evidence Bank**: Inventory of "proofs" (links to projects, publications, certifications) linked to requirements in Match.
- **Master Docs Repository**: "Golden" versions of documents (CV, letters, emails) used as templates to apply deltas for each application.

## 2. Feedback Loop (Aggregator - Stage 8)

The system collects all ReviewNodes generated in the UI to update context for future executions.

### Aggregation Mechanism

**Preference Extraction**: Reads ReviewNodes of type STYLE and CORRECTION from past applications.

**Evidence Consolidation**: If you manually added an evidence link in Match (AUGMENTATION), it's permanently saved to the global Evidence Bank for automatic suggestion in similar future applications.

**Prompt Injection**: UI and Backend show which specific corrections are included in the current prompt (provenance transparency).

## 3. Updated Data Structure

```
data/
├── master/                     # Global "Evidence Tree"
│   ├── profile.json            # Structured CV Profile
│   ├── evidence_bank/          # Links and HITL-validated proofs
│   │   └── *.json
│   └── templates/              # Base documents
│       ├── master_cv.md
│       ├── master_cover_letter.md
│       └── master_email.md
└── jobs/
    └── <source>/<job_id>/
        ├── raw/                # Original text and screenshots
        ├── nodes/              # Artifacts by stage
        │   ├── extract/
        │   ├── match/
        │   ├── strategy/
        │   └── drafting/
        └── review/             # ReviewNodes from this application
```

## 4. UI Review Flow

### Text Tagger (Stage 3)
- Validate extracted requirements
- Define application method (email, form, etc.)
- Correct text spans

### Match Editor (Stage 4)
- Approve/reject requirement->evidence links
- Add manual evidence (AUGMENTATION)

### Delta & Motivations (Stage 5.1)
- Form-like view to enter the "why" of the application
- Select evidence to use

### Sculpt Editor (Stage 5.2)
- Text editor for fine-tuning final drafting
- Apply style corrections (STYLE)

## 5. Transparency Panel

UI must show:
- Which corrections from past applications are active
- Which global bank evidence was suggested
- Which style preferences are being applied

This allows the user to understand and audit LLM decisions.
