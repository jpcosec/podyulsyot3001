
# 🕵️‍♂️ Scraper Adapter Framework

Este Framework permite agregar nuevos portales de empleo de forma determinista usando **Crawl4AI**. La lógica está separada por **Responsabilidades**.

## 🏗️ Arquitectura de un Adaptador

Cada adaptador (ej. `StepStoneAdapter`) debe heredar de `BaseScraperAdapter` e implementar estos 4 hitos:

1.  **`supported_params` (Propiedad)**:
    Lista de flags del CLI que el portal sabe manejar (ej. `['city', 'job_query']`).
    
2.  **`get_search_url(**kwargs)`**:
    Lógica para inyectar los filtros del CLI (`city`, `job_query`, `categories`) en la URL de búsqueda del portal.
    
3.  **`extract_links(crawl_result)`**:
    Recibe el resultado de Crawl4AI de la página de resultados y debe devolver una lista de URLs absolutas de las ofertas encontradas.
    
4.  **`get_extraction_schema()`**:
    El mapa (JSON/CSS) que le dice a Crawl4AI exactamente qué campos técnicos extraer de la vacante (título, email, salario, etc.).

---

## 🚀 Cómo agregar una nueva Source

1.  Crea la carpeta en `src/scraper/providers/{source_name}/`.
2.  Crea el archivo `adapter.py` implementando la clase.
3.  Registra la instancia en el diccionario `PROVIDERS` de `src/scraper/main.py`.

## ⚙️ Uso del CLI

```bash
python -m src.scraper.main --source {tuberlin|stepstone} --job_query "Data Scientist" --overwrite
```

**Beneficios:**
- **Indoloro:** El `BaseScraperAdapter` ya maneja por ti el guardado de archivos, el chequeo de duplicados y la configuración de Crawl4AI.
- **Limpio:** El `main.py` no sabe nada de selectores o URLs específicas.
