from __future__ import annotations

import uvicorn

from src.interfaces.api.config import load_settings


def main() -> int:
    settings = load_settings()
    uvicorn.run(
        "src.interfaces.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
