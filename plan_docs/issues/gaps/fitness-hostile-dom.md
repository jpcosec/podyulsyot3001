# Fitness Function 3: Hostile DOM Sandbox

**Explanation:** Protect against DOM crash on void elements (input, img, br, hr) - hinting.js must not use appendChild on void elements.

**Reference:** `tests/unit/automation/fitness/test_hostile_dom.py`

**What to fix:** Test that hinting script doesn't crash on HTML with void elements, hidden elements, overflow:hidden.

**How to do it:**
1. Create hostile HTML fixture with void elements
2. Run hinting.js injection
3. Assert no DOMException raised

**Depends on:** none