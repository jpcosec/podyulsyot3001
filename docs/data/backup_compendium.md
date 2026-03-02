# Backup Compendium Layout

Canonical data layout has two top-level categories under `data/`.

## Canonical Structure

```text
data/
├── pipelined_data/
│   └── tu_berlin/
│       ├── <job_id>/
│       │   ├── raw.html
│       │   ├── proposal_text.md
│       │   ├── summary.json
│       │   ├── job.md
│       │   └── motivation_letter.md
│       └── summary.csv
└── reference_data/
    ├── application_assets/
    ├── agent_feedback/
    ├── profile/
    ├── archive/
    └── backup/backup_compendium.json
```

## Build / Refresh Compendium

Run:

```bash
python src/utils/build_backup_compendium.py
```

Preview only:

```bash
python src/utils/build_backup_compendium.py --dry-run
```

The compendium manifest is written to:
- `data/reference_data/backup/backup_compendium.json`
