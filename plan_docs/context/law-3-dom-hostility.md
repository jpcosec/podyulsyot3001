---
type: guardrail
law: 3
domain: ariadne
source: src/automation/ariadne/capabilities/hinting.js:40
---

# Pill: Law 3 — DOM Hostility

## Rule
JS capabilities must never mutate existing DOM nodes or event listeners. All injected elements must attach to a single dedicated overlay anchored to `document.body`.

## ❌ Forbidden
```javascript
const el = document.querySelector('.btn');
el.innerHTML += '<span>AA</span>';  // wipes event listeners
el.appendChild(hint);               // can trigger SPA re-renders
```

## ✅ Correct
```javascript
// hinting.js:40 — current implementation
const overlay = document.createElement('div');
overlay.setAttribute('data-ariadne-hint-overlay', 'true');
overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2147483647';
document.body.appendChild(overlay);

const rect = target.getBoundingClientRect();
label.style.top = rect.top + 'px';
overlay.appendChild(label);
```

Cleanup: remove by `[data-ariadne-hint-overlay]` attribute, never by id or class.

## Verify
```bash
python -m pytest tests/architecture/test_hostile_dom.py -q
```
Loads a poisoned HTML fixture (void elements, iframes, shadow roots) and asserts `hinting.js` injects without errors or side effects.
