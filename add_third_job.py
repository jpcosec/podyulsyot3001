import asyncio
import argparse
import sys
from playwright.async_api import async_playwright

async def fill_xing_experience(args):
    # Volvemos a usar tu ruta principal de Chrome
    USER_DATA_DIR = "/home/jp/.config/google-chrome"

    print("Iniciando Playwright...", flush=True)
    async with async_playwright() as p:
        try:
            # Nos conectamos a un Chrome ya abierto en el puerto de depuración 9222
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            # Obtenemos el contexto (perfil) que ya está cargado
            context = browser.contexts[0]
            page = await context.new_page()
        except Exception as e:
            print("\n[ERROR CRÍTICO]: No se pudo conectar a tu Chrome abierto.")
            print("Por favor, CIERRA todo Chrome, y luego ábrelo DESDE LA TERMINAL ejecutando exactamente:")
            print("google-chrome --remote-debugging-port=9222")
            sys.exit(1)
        
        print("Navegando a la página de nueva experiencia en XING...", flush=True)
        await page.goto("https://www.xing.com/profile/my_profile/timeline/add/employee")
        await page.wait_for_load_state("domcontentloaded")

        print("Rellenando campos principales...", flush=True)
        await page.get_by_label("Descripción del cargo", exact=False).fill(args.job_title)
        
        if args.employment_type:
            await page.locator("select[name='employment']").select_option(label=args.employment_type)
        if args.career_level:
            await page.locator("select[name='careerLevel']").select_option(label=args.career_level)
        if args.discipline:
            await page.locator("select[name='discipline']").select_option(label=args.discipline)
            
        await page.get_by_label("Empresa", exact=True).fill(args.company)
        
        # El campo de lugar puede requerir clics previos si está colapsado, aunque a veces funciona directo
        # expandiendo "Lugar (opcional)"
        if args.location:
            lugar_btn = page.get_by_role("button", name="Lugar  (opcional)")
            if await lugar_btn.is_visible():
                await lugar_btn.click()
            await page.locator('input[aria-label="Lugar"], input[name="location"], input[id*="location"]').first.fill(args.location) if await page.locator('input[aria-label="Lugar"], input[name="location"], input[id*="location"]').count() > 0 else await page.get_by_label("Lugar", exact=False).fill(args.location)
        
        # Expandir "Descripción (opcional)"
        if args.description:
            desc_btn = page.get_by_role("button", name="Descripción  (opcional)")
            if await desc_btn.is_visible():
                await desc_btn.click()
            await page.get_by_role("textbox", name="Descripción").fill(args.description)

        print("Configurando fechas...", flush=True)
        
        # Settings for currently working check box
        actualmente = page.get_by_label("Actualmente")
        if args.currently_working:
            if await actualmente.is_visible() and not await actualmente.is_checked():
                await actualmente.check()
        else:
            if await actualmente.is_visible() and await actualmente.is_checked():
                await actualmente.uncheck()

        # Inicio
        if args.start_month:
            await page.locator("select[data-qa='startDate-month-dropdown']").select_option(label=args.start_month)
        if args.start_year:
            await page.locator("select[data-qa='startDate-year-dropdown']").select_option(label=args.start_year)

        # Fin
        if not args.currently_working:
            if args.end_month:
                await page.locator("select[data-qa='endDate-month-dropdown']").select_option(label=args.end_month)
            if args.end_year:
                await page.locator("select[data-qa='endDate-year-dropdown']").select_option(label=args.end_year)

        print("Bypass dropdowns bugueados y guardando...", flush=True)
        # Hacemos scroll abajo
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Click en Guardar
        await page.get_by_role("button", name="Guardar").click()

        try:
            # Esperamos que todo cargue correctamente
            await page.wait_for_navigation(timeout=10000)
            print(f"\n¡Registro Exitoso: {args.job_title} en {args.company} guardado!", flush=True)
        except:
            print("\nEl botón guardar se presionó, pero la página tardó en navegar, por favor verifica.")

        await browser.close()

def main():
    parser = argparse.ArgumentParser(description="Añade una experiencia laboral a XING.")
    parser.add_argument("--job-title", required=True, help="El puesto de trabajo")
    parser.add_argument("--company", required=True, help="El nombre de la empresa")
    parser.add_argument("--employment-type", default="Empleado(a) (Jornada completa)", help="Situación laboral")
    parser.add_argument("--career-level", default="Con experiencia profesional", help="Nivel profesional")
    parser.add_argument("--discipline", default="TI y desarrollo de software", help="Área profesional")
    parser.add_argument("--location", default="", help="Lugar de trabajo")
    parser.add_argument("--description", default="", help="Descripción de las tareas")
    parser.add_argument("--start-month", default="", help="Mes de inicio (ej. abril)")
    parser.add_argument("--start-year", default="", help="Año de inicio (ej. 2024)")
    parser.add_argument("--end-month", default="", help="Mes de fin (ej. junio)")
    parser.add_argument("--end-year", default="", help="Año de fin (ej. 2025)")
    parser.add_argument("--currently-working", action="store_true", help="Marca si sigues trabajando ahí (ignora mes/año fin)")

    args = parser.parse_args()
    
    asyncio.run(fill_xing_experience(args))

if __name__ == "__main__":
    main()
