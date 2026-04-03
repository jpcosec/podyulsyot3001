# Generate Documents - Examples

**Date:** 2026-03-31
**Scope:** Casos de ejemplo para seguir el flujo de datos end-to-end.

---

## 1. Caso Base - Data Engineer para Deutsche Bahn

## 1.1 Perfil

- candidato chileno
- vive en Berlin
- tiene `Chancenkarte`
- experiencia en Data Engineering
- hobby de modelismo ferroviario

## 1.2 Job

- Data Engineer en Munich
- requiere Rust y Python
- ofrece relocalizacion

## 1.3 Flujo

### Ingestion
- `J1` se transforma en `J2`
- `J2` detecta Rust, Python, cultura de estabilidad y contexto ferroviario
- `J3` prioriza Rust y relocation

### Matching
- el motor conecta experiencia previa con Rust/Python/Kafka
- en HITL 1 se agrega hobby ferroviario como evidencia emergente

### Blueprint
- la carta prioriza motivacion por infraestructura ferroviaria
- el CV prioriza Rust y residencia en Alemania
- se agrega disponibilidad para mudanza a Munich

### Drafting
- se redacta narrativa tecnica y afinidad cultural
- smoothing conecta hobby, sector y experiencia profesional

### Assembly
- se inyecta direccion de Berlin
- se inyecta estado de visa
- se compilan CV, carta y email

### HITL 3
- el usuario baja el tono del hobby para que suene mas profesional

### Render
- se genera PDF con layout aleman

---

## 2. Mismo perfil, Job en Chile

## 2.1 Cambio de estrategia

- el assembler usa direccion chilena si corresponde
- desaparece la referencia a `Chancenkarte`
- el hobby ferroviario puede omitirse
- el CV vuelve a priorizar resumen ejecutivo y logros cuantificados

---

## 3. Mismo hecho, tres salidas

Hecho fuente:
- "Disene un algoritmo de optimizacion de rutas en Rust"

### CV profesional
- foco en resultado y eficiencia

### CV academico
- foco en metodologia y problema tecnico

### Carta academica
- foco en trayectoria intelectual y linea de interes

---

## 4. Caso de feedback persistente

### Entrada
- en HITL 3 el usuario cambia "Soy experto" por "Cuento con amplia trayectoria"

### Efecto
- si `persist_to_profile=True`, el Profile Updater guarda una preferencia tonal en `P1` o `P2`
