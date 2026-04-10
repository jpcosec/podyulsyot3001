# BrowserOS AppImage Path Is Hardcoded

**Explanation:** The BrowserOS runtime logic currently uses a hardcoded default path `/home/jp/BrowserOS.AppImage`. While it respects `BROWSEROS_APPIMAGE_PATH`, the fallback should be managed via environment configuration or discovery rather than a hardcoded string in the source code.

**Reference:**
- `src/automation/motors/browseros/runtime.py`

**What to fix:** Remove the hardcoded `/home/jp/` path and ensure the runtime only proceeds if `BROWSEROS_APPIMAGE_PATH` is set or if the AppImage is found in a standard configurable location.

**How to do it:**
1. Move `DEFAULT_APPIMAGE_PATH` to an environment-loaded configuration.
2. Update `ensure_browseros_running` to require this configuration.
3. Update documentation to reflect the required environment variable.

**Depends on:** none
