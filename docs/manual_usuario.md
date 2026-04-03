# Postulator 3000 - Manual de Usuario

## Qué es

Pipeline modular para crear CVs y cartas de motivación personalizadas a partir de ofertas de trabajo. Combina:
- Web scraping de portales de empleo
- Matching de perfil con requisitos (con revisión humana)
- Generación de documentos con IA
- Renderizado a PDF

## Flujo de trabajo completo

```
1. Scraping     → 2. Matching    → 3. Revisión    → 4. Generación   → 5. Renderizado
(obtener oferta) (analizar match) (HITL TUI)     (crear docs)      (PDF final)
```

---

## Comandos de operación

### 1. Obtener ofertas de trabajo

```bash
# Scraping básico
python -m src.scraper.main --source stepstone --limit 5

# Fuentes disponibles: stepstone, xing, tuberlin, demo
```

### 2. Matching de perfil

```bash
python -m src.core.ai.match_skill.main \
  --source stepstone \
  --job-id <ID> \
  --requirements path/to/requirements.json \
  --profile-evidence path/to/evidence.json
```

Esto inicia el grafo LangGraph y **se pausa en el breakpoint de revisión** esperando intervención humana.

### 3. Revisión humana (HITL)

```bash
python -m src.cli.main review --source stepstone --job-id <ID>
```

Esto abre la interfaz TUI donde puedes:
- **Aprobar** el match → continúa el pipeline
- **Solicitar regeneración** → vuelve al paso de matching
- **Rechazar** → termina el proceso

### 4. Generar documentos

```bash
# Genera CV y carta automáticamente
python -m src.core.ai.generate_documents.main \
  --source stepstone \
  --job-id <ID>
```

### 5. Renderizar a PDF

```bash
# Renderizar CV
python -m src.core.tools.render.main cv \
  --source stepstone \
  --job-id 12683570 \
  --language en

# Renderizar carta de motivación
python -m src.core.tools.render.main letter \
  --source stepstone \
  --job-id 12683570 \
  --language de
```

---

## Dónde encontrar los datos

```
data/jobs/
├── stepstone/
│   └── 12683570/
│       ├── meta.json                    # Metadata del job
│       └── nodes/
│           ├── ingest/                  # Datos originales del scraping
│           │   └── proposed/
│           │       ├── content.md       # Contenido original
│           │       ├── listing.json     # Datos de la oferta
│           │       └── scrape_meta.json
│           ├── match_skill/             # Resultados del matching
│           ├── generate_documents_v2/   # Documentos generados
│           │   ├── localized_cv/
│           │   ├── localized_letter/
│           │   └── localized_email/
│           └── render/                  # PDFs finales
│               └── proposed/
│                   ├── cv.pdf
│                   └── cover_letter.pdf
├── xing/
├── tuberlin/
└── demo/
```

---

## Cómo revisar una postulación

### Paso 1: Ver la oferta original
```bash
cat data/jobs/stepstone/12683570/nodes/ingest/proposed/content.md
```

### Paso 2: Ver documentos generados (JSON)
```bash
# Carta de motivación
cat data/jobs/stepstone/12683570/nodes/generate_documents_v2/localized_letter/current.json

# CV
cat data/jobs/stepstone/12683570/nodes/generate_documents_v2/localized_cv/current.json
```

### Paso 3: Ver PDFs finales
```bash
# Los PDFs están en:
data/jobs/stepstone/12683570/nodes/render/proposed/cv.pdf
data/jobs/stepstone/12683570/nodes/render/proposed/cover_letter.pdf
```

### Paso 4: Si hay errores, regenerar

```bash
# Opción A: Solo regenerar documentos
python -m src.core.ai.generate_documents.main --source stepstone --job-id 12683570

# Opción B: Todo desde matching (requiere revisión humana)
python -m src.core.ai.match_skill.main \
  --source stepstone \
  --job-id 12683570 \
  --requirements tu_profile/requirements.json \
  --profile-evidence tu_profile/evidence.json
```

---

## Estructura de archivos de perfil

### requirements.json
```json
{
  "experience_years": 2,
  "required_skills": ["Python", "SQL", "Machine Learning"],
  "preferred_skills": ["TensorFlow", "AWS"],
  "education_level": "master",
  "languages": ["German", "English"]
}
```

### evidence.json
```json
{
  "skills": ["Python programming", "Data analysis"],
  "experience": [
    {"company": "Tech Corp", "role": "Data Analyst", "duration": "2 years"}
  ],
  "education": [
    {"degree": "M.Sc. Data Science", "university": "TU Berlin"}
  ]
}
```

---

## Solución de problemas

### Error: "No hay API key"
```bash
# Verificar que el archivo .env tenga las variables
cat .env
# Debe contener: GOOGLE_API_KEY=...
```

### Error: "No se encuentra el job"
```bash
# Listar jobs disponibles
ls data/jobs/stepstone/
```

### Error: "Falta pandoc"
```bash
# Instalar pandoc
sudo apt install pandoc

# Instalar texlive para PDF
sudo apt install texlive-full
```

### Ver logs
```bash
# Logs del pipeline
ls logs/

# Logs de LangGraph
ls .langgraph_api/
```

---

## Referencia rápida

| Acción | Comando |
|--------|---------|
| Buscar ofertas | `python -m src.scraper.main --source stepstone --limit 10` |
| Matching | `python -m src.core.ai.match_skill.main --source stepstone --job-id ID --requirements req.json --profile-evidence ev.json` |
| Revisar | `python -m src.cli.main review --source stepstone --job-id ID` |
| Generar docs | `python -m src.core.ai.generate_documents.main --source stepstone --job-id ID` |
| Generar PDF | `python -m src.core.tools.render.main cv --source stepstone --job-id ID --language es` |
