# Utils Module

Utility scripts for document packaging and workspace maintenance.

## Scripts

- `pdf_merger.py`: merge and optionally compress application PDF bundles.
- `build_backup_compendium.py`: regenerate backup manifest for `data/pipelined_data` and `data/reference_data`.

## Usage

```bash
python src/utils/build_backup_compendium.py
python src/utils/pdf_merger.py -o Final_Application.pdf <file1.pdf> <file2.pdf>
```

Manifest output:
- `data/reference_data/backup/backup_compendium.json`
