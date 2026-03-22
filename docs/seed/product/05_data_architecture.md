# Data Architecture: Folder Structure

## Root Convention

The job folder follows this convention to support local-first flow and feedback loop:

```
data/jobs/<source>/<job_id>/
├── raw/                      # Original text and screenshots
│   ├── source_text.md
│   └── error_screenshot.png
├── nodes/
│   ├── extract/              # Text Tagger results
│   │   └── state.json
│   ├── match/                # Requirements <-> Evidence (JSON)
│   │   └── state.json
│   ├── strategy/             # Delta and motivations (JSON)
│   │   └── delta.json
│   ├── drafting/             # Final .md documents
│   │   ├── cv.md
│   │   ├── cover_letter.md
│   │   └── email.md
│   └── review/               # User decisions and comments
│       └── decisions.json
├── feedback/                 # Corrections captured for future cycles
│   └── *.md
└── final/                    # PDFs and application packages
    ├── cv.pdf
    ├── cover_letter.pdf
    └── package.zip
```

## Candidate (CV Profile)

```
data/candidate/
├── cv_profile/               # Candidate Knowledge Graph
│   ├── sections.json
│   └── skills.json
├── base_docs/               # Master Docs - starting points
│   ├── master_cv.md
│   ├── master_cover_letter.md
│   └── master_email_template.md
└── evidence_bank/           # Reusable evidence
    └── *.md
```

## State Files

Each `state.json` follows the contract defined in the node's `contract.py`:

- **extract/state.json**: Extracted requirements, validated spans, application metadata.
- **match/state.json**: Requirement->evidence links, scores, justifications.
- **strategy/delta.json**: Logical modifications to apply to Base Documents.

## Feedback Loop

The `feedback/` directory accumulates corrections from past cycles to:
1. Enrich prompts for future extractions.
2. Learn from user edits in Match.
3. Improve evidence selection.
