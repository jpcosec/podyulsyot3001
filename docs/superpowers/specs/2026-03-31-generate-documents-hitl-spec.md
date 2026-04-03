# Generate Documents - HITL Spec

**Date:** 2026-03-31
**Scope:** Puntos de intervencion humana, objetivos, entradas, salidas y persistencia.

---

## 1. Objetivo

El pipeline requiere tres puntos HITL distintos porque cada uno corrige una capa diferente:
- match semantico
- logica estructural
- narrativa final

---

## 2. HITL 1 - Match and Emergent Evidence

## 2.1 Momento

Despues del matching entre `P1` y `J2`.

## 2.2 Objetivo

- validar relevancia tecnica
- corregir falsos positivos o falsos negativos
- agregar evidencia emergente no presente en el perfil base

## 2.3 Tipos de intervencion

- aprobar match
- rechazar match
- agregar nueva evidencia
- cambiar prioridad de evidencia

## 2.4 Ejemplos

- "Olvide mencionar que participe en un proyecto de musica"
- "Para esta empresa importa mi hobby ferroviario"
- "Este match tecnico esta forzado; no lo uses"

## 2.5 Resultado

- delta de match aprobado
- nuevos facts o edges para la postulacion actual

---

## 3. HITL 2 - Blueprint Logic

## 3.1 Momento

Despues de generar el `GlobalBlueprint`.

## 3.2 Objetivo

- validar estrategia y orden del documento
- revisar si falta alguna idea
- quitar redundancias antes de redactar

## 3.3 Tipos de intervencion

- mover ideas entre secciones
- cambiar orden del tren de frases
- insertar una idea faltante
- pedir regeneracion del blueprint

## 3.4 Restriccion

No corrige estilo literario; corrige logica.

## 3.5 Resultado

- blueprint aprobado o regenerado

---

## 4. HITL 3 - Content and Style

## 4.1 Momento

Despues del assembly en Markdown y antes del render.

## 4.2 Objetivo

- validar tono
- validar narrativa
- ajustar fluidez
- revisar que los documentos ya se sientan reales

## 4.3 Tipos de intervencion

- modificar una frase
- reemplazar un tono
- simplificar una afirmacion
- pedir rerender si el cambio es visual

## 4.4 Resultado

- bundle Markdown aprobado
- salida lista para render

---

## 5. Contrato Universal de Patch

El sistema debe usar un modelo unico tipo `GraphPatch`.

**Campos minimos**
- `action`
- `target_id`
- `new_value`
- `feedback_note`
- `persist_to_profile`

**Acciones frecuentes**
- `approve`
- `reject`
- `modify`
- `request_regeneration`

---

## 6. Persistencia del Feedback

## 6.1 Regla

Solo se persiste si `persist_to_profile=True`.

## 6.2 Destinos

- `P1` para evidencia y datos del perfil
- `P2` para reglas de mapeo y estrategia

## 6.3 Tipos de aprendizaje

- evidencia nueva
- reorden de secciones
- preferencia tonal

---

## 7. Riesgos si se mezclan los HITL

- si HITL 1 se usa para estilo, se contamina el matching
- si HITL 2 se usa para reescribir frases, se rompe la separacion entre logica y redaccion
- si HITL 3 intenta reordenar toda la estrategia, el cambio llega demasiado tarde
