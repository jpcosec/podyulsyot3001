# Comments Inventory

Date: 2026-03-11

## Scope and Exclusions

This inventory is ordered as a path tree and scans comment-like markers in:

- `src/`
- `docs/`

using these wrappers:

- `# ...`
- `#TODO` / `# TODO`
- `<!-- ... -->`
- `<--`

Explicit exclusions for this analysis:

- everything under `data/`
- everything under `pipeline/`
- `docs/reference/comments_inventory.md` itself (to avoid self-referential matches)

## Summary (excluding `data/` and `pipeline/`)

- `#TODO` markers: **14**
- non-TODO `#` comments in `src/**/*.py`: **18**
- `<!-- ... -->` markers: **0**
- `<--` markers: **0**

Docs-only summary (excluding this inventory file):

- `#TODO` markers: **0**
- `<!-- ... -->` markers: **0**
- `<--` markers: **0**

## Tree View

```text
src/
├── graph.py
│   ├── L2   #TODO: IS THIS USING LANGRAPH?
│   └── L21  #TODO: what does this step do? please make the code more explicit here
│
├── cli/
│   ├── render_cv.py
│   │   ├── L23  #TODO : Enforce order, deterministic code belongs in core.
│   │   └── L67  # Normalize optional fields — template uses StrictUndefined so all accessed keys must exist
│   └── run_prep_match.py
│       ├── L99   # Intentionally do not convert profile summary/tagline text into evidence.
│       ├── L100  # Narrative fields are regenerated during CV/motivation generation phases.
│       └── L101  # Matching evidence must come from concrete, auditable records.
│
├── core/
│   └── tools/
│       └── render/
│           ├── docx.py
│           │   └── L16  #TODO: Pydocs, would be a good idea being able to use templates here
│           ├── latex.py
│           │   ├── L13  #TODO: This could be incorporated onto templates
│           │   ├── L85  # Copy support assets (Einstellungen/ and Abbildungen/)
│           │   ├── L93  # Override photo if caller supplies one
│           │   ├── L97  # Render .tex
│           │   └── L102 # Compile — run twice for stable cross-references
│           └── letter.py
│               ├── L33   # Find the two --- separators
│               ├── L36   # Everything between first and second separator is the header block
│               ├── L50   # Everything after second separator is the letter body
│               ├── L53   # Split body into paragraphs on blank lines
│               ├── L66   # Find closing: "Yours sincerely," and everything after
│               ├── L108  # Date (right-aligned)
│               ├── L117  # Recipient and Re:
│               ├── L125  # Horizontal rule via border
│               ├── L139  # Body paragraphs
│               └── L146  # Closing block
│
└── nodes/
    ├── extract_understand/
    │   ├── contract.py
    │   │   ├── L21  #TODO: puede que ayude un poco aca hacer una especie de "preordenamiento"
    │   │   ├── L23  #TODO: Faltan campos base como Tematica (puede ser un par de tags), descripcion, contacto y el formulario exacto que va arriba
    │   │   └── L25  #TODO: ENGLISH PLEASE!
    │   └── logic.py
    │       ├── L27  #TODO: We are missing crucial extra info here such as job description!!
    │       └── L37  #TODO: isn't this automatic from the pydantic data?
    ├── match/
    │   └── contract.py
    │       ├── L10  #TODO: Seria interesante que el agente le ponga alguna valoracion a los requerimientos...
    │       ├── L19  #TODO: Documentar, no se entiende para que es esto
    │       └── L30  #TODO: Creo que hay un ligero drift entre esto y la logica real que estamos usando, Se usa esta clase?
    └── review_match/
        └── contract.py
            └── L10  #TODO: Se esta usando esto?

docs/
└── (no comment-like markers found after exclusions)
```

## Notes

- This inventory intentionally excludes generated/raw artifacts under `data/`.
- There were no `<!-- ... -->` or `<--` markers outside excluded folders.
