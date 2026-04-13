# Fitness Function 3: DOM Sandbox Hostil (JS Execution)
# Verifica que hinting.js no crashee con DOM venenoso

import pytest
from pathlib import Path
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_hinting_js_survives_hostile_dom():
    """Fitness: hinting.js no crashea con elementos void o invisibles."""

    js_path = Path("src/automation/ariadne/capabilities/hinting.js")
    script = js_path.read_text()

    hostile_html = """
    <!DOCTYPE html>
    <html><body>
        <input type="text" id="void-input" value="No me puedes hacer appendChild">
        <img src="fake.jpg" id="void-img" alt="Yo tampoco">
        <hr>
        <div style="overflow: hidden; height: 0;">
            <button>Botón invisible</button>
        </div>
    </body></html>
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(hostile_html)

        try:
            result = await page.evaluate(script)
        except Exception as e:
            await browser.close()
            pytest.fail(f"🚨 hinting.js rompió el DOM: {str(e)}")

        assert isinstance(result, dict), "Hinting debe retornar un dict"
        await browser.close()
