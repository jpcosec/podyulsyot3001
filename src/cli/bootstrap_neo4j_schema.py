from __future__ import annotations

import json

from src.interfaces.api.config import load_settings
from src.interfaces.api.neo4j_schema import apply_schema_constraints


def main() -> int:
    settings = load_settings()
    result = apply_schema_constraints(settings)
    print(
        json.dumps(
            {"ok": result.ok, "applied": result.applied, "message": result.message},
            ensure_ascii=False,
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
