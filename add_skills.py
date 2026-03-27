import asyncio
from playwright.async_api import async_playwright
import time

SKILLS = [
    "Airflow", "Arduino", "Audio Processing", "AWS", "Azure", "Azure Data Factory", 
    "Beanie/Pydantic", "BigQuery", "C", "CI/CD", "Circuit Design", "Control Interfaces", 
    "Databricks", "Delta Lake", "Docker", "Document Processing", "Embedded Solutions", 
    "English", "Experiment Design", "FastAPI", "G-code", "GenAI", "German", "Git", 
    "Google Cloud", "guardrails", "ITS", "Java", "JavaScript", "Jinja2", "Kafka", 
    "Learning Analytics", "LLM prompting", "LLMs", "model evaluation", "OCR", 
    "Power BI", "Prefect", "PySpark", "Python", "PyTorch", "React/TypeScript", 
    "ROS", "S3", "scikit-learn", "Spanish", "Spark", "SPICE", "TensorFlow", 
    "TensorFlow/Keras", "Verilog", "Vertex AI"
]

async def add_skills():
    print("Conectando a Chrome en puerto 9222...", flush=True)
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            # Aseguramos que estamos en la página de skills
            if "skills/add" not in page.url:
                print(f"Navegando a la página de skills... (URL actual: {page.url})")
                await page.goto("https://www.xing.com/profile/my_profile/skills/add")
                await page.wait_for_load_state("domcontentloaded")

            input_selector = 'input[role="combobox"], input[placeholder*="Añadir"], input[id*="input"]'
            
            for skill in SKILLS:
                print(f"Añadiendo: {skill}...", end=" ", flush=True)
                try:
                    # Buscamos el input (XING a veces refresca el DOM)
                    input_field = page.locator(input_selector).first
                    await input_field.fill(skill)
                    await asyncio.sleep(0.5) # Pequeña pausa para que el dropdown cargue si es necesario
                    await input_field.press("Enter")
                    await asyncio.sleep(0.8) # Pausa para que XING procese el tag
                    print("OK")
                except Exception as e:
                    print(f"Error con {skill}: {e}")
            
            print("\nProceso finalizado. ¡Revisa tu navegador!")
            
        except Exception as e:
            print(f"\n[ERROR]: No se pudo conectar. Asegúrate de tener Chrome abierto con --remote-debugging-port=9222")
            print(f"Detalles: {e}")

if __name__ == "__main__":
    asyncio.run(add_skills())
