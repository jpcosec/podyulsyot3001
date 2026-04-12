/**
 * Ariadne Hinting Script
 * Injects alphanumeric overlays (Set-of-Mark) on interactive elements.
 * Returns a mapping of Hint ID -> Element Metadata.
 */
(function() {
    const HINT_CONTAINER_ID = 'ariadne-hint-container';
    let container = document.getElementById(HINT_CONTAINER_ID);
    if (container) {
        container.remove();
    }

    container = document.createElement('div');
    container.id = HINT_CONTAINER_ID;
    container.style.position = 'absolute';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '2147483647'; // Max z-index
    document.body.appendChild(container);

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
        
        const label = document.createElement('div');
        label.textContent = hint;
        label.style.position = 'absolute';
        label.style.left = (rect.left + window.scrollX) + 'px';
        label.style.top = (rect.top + window.scrollY) + 'px';
        label.style.backgroundColor = 'yellow';
        label.style.color = 'black';
        label.style.border = '1px solid black';
        label.style.fontWeight = 'bold';
        label.style.fontSize = '12px';
        label.style.padding = '2px';
        label.style.borderRadius = '3px';
        label.style.lineHeight = '1';
        label.style.zIndex = '2147483647';
        label.style.pointerEvents = 'auto'; // Optional: allow clicking the hint itself? Usually none is safer.
        
        container.appendChild(label);

        // Generate a simple unique-ish selector or use a custom attribute
        el.setAttribute('data-ariadne-hint', hint);
        
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
