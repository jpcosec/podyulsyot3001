# Fix: Robust Hint Anchoring in Scrollable Containers

**Explanation:** The current `hinting.js` script uses absolute body-relative positioning. In modern portals like LinkedIn, interactive elements often live inside scrollable divs or modales with `overflow-y: scroll`. Standard `window.scrollY` doesn't capture these offsets, causing hints to disconnect from their elements during scrolling.

**Reference:**
- `src/automation/ariadne/capabilities/hinting.js`

**What to fix:** Hints must be anchored directly to their parent elements or use a robust relative positioning strategy that survives internal container scrolls.

**How to do it:**
1.  Change hint injection to use `element.insertAdjacentHTML` or `element.appendChild`.
2.  Use `position: relative` on the parent or `position: absolute` relative to the element's direct bounding box.
3.  Ensure the hint div has a higher `z-index` and doesn't disrupt the page layout.

**Depends on:** none
