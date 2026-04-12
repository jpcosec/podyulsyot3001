/**
 * Ariadne Hinting Script
 * Injects alphanumeric overlays (Set-of-Mark) on interactive elements.
 * Returns a mapping of Hint ID -> Element Metadata.
 */
(function() {
    const LABEL_ATTRIBUTE = 'data-ariadne-hint-label';
    const HINT_ATTRIBUTE = 'data-ariadne-hint';

    document.querySelectorAll('[' + LABEL_ATTRIBUTE + ']').forEach(label => label.remove());
    document.querySelectorAll('[' + HINT_ATTRIBUTE + ']').forEach(el => el.removeAttribute(HINT_ATTRIBUTE));

    const interactiveSelectors = [
        'a', 'button', 'input', 'select', 'textarea',
        '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="menuitem"]',
        '[onclick]', '.btn', '.button'
    ];

    const elements = Array.from(document.querySelectorAll(interactiveSelectors.join(',')))
        .filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && 
                   window.getComputedStyle(el).visibility !== 'hidden' &&
                   window.getComputedStyle(el).display !== 'none';
        });

    function generateHint(index) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        let hint = '';
        let n = index + 26; // Start from 26 to get 'AA' for index 0
        while (n >= 0) {
            hint = chars[n % 26] + hint;
            n = Math.floor(n / 26) - 1;
        }
        return hint;
    }

    const hintMap = {};

    elements.forEach((el, index) => {
        const hint = generateHint(index);
        const rect = el.getBoundingClientRect();

        const computedStyle = window.getComputedStyle(el);
        if (computedStyle.position === 'static') {
            el.style.position = 'relative';
        }

        const label = document.createElement('span');
        label.setAttribute(LABEL_ATTRIBUTE, hint);
        label.textContent = hint;
        label.style.position = 'absolute';
        label.style.top = '0';
        label.style.left = '0';
        label.style.transform = 'translate(-20%, -45%)';
        label.style.backgroundColor = 'yellow';
        label.style.color = 'black';
        label.style.border = '1px solid black';
        label.style.fontWeight = 'bold';
        label.style.fontSize = '12px';
        label.style.padding = '2px';
        label.style.borderRadius = '3px';
        label.style.lineHeight = '1';
        label.style.zIndex = '2147483647';
        label.style.pointerEvents = 'none';
        label.style.whiteSpace = 'nowrap';

        // Generate a simple unique-ish selector or use a custom attribute
        el.setAttribute(HINT_ATTRIBUTE, hint);
        el.appendChild(label);
        
        hintMap[hint] = {
            tagName: el.tagName,
            text: el.innerText || el.value || '',
            type: el.type || '',
            placeholder: el.placeholder || '',
            selector: `[data-ariadne-hint="${hint}"]`,
            rect: {
                x: rect.left,
                y: rect.top,
                w: rect.width,
                h: rect.height
            }
        };
    });

    return hintMap;
})();
