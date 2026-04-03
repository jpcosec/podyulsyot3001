# Generate Documents - Pydantic Contracts

**Date:** 2026-03-31
**Scope:** Contratos de datos del pipeline, agrupados por responsabilidad y etapa.

---

## 1. Objetivo

Los modelos deben servir como contratos estrictos entre nodos. Deben asegurar:
- trazabilidad
- auditabilidad
- separacion clara entre semantica, redaccion y render
- compatibilidad con HITL y aprendizaje posterior

---

## 2. Modelos Base

## 2.1 `TextAnchor`

**Rol**
- localizar una cita exacta en una fuente original

**Campos**
- `document_id`
- `start_index`
- `end_index`
- `exact_quote`

**Uso**
- auditoria visual
- trazabilidad desde frase final a texto fuente

---

## 2.2 `IdeaFact`

**Rol**
- unidad minima de informacion conciliable

**Campos**
- `id`
- `provenance_refs`
- `core_content`
- `priority`
- `status`
- `source_anchors` opcional

**Reglas**
- `priority` entre 1 y 5
- `status` en `keep`, `hide`, `merge`

---

## 3. Modelos del Perfil

## 3.1 `ProfileKG`

**Rol**
- base persistente del candidato

**Campos esperados**
- `entries`
- `skills`
- `traits`
- `evidence_edges`

---

## 3.2 `SectionMapping`

**Rol**
- definir estrategia de secciones por documento, pais y contexto

**Campos consolidados**
- `section_id`
- `target_document`
- `country_context`
- `mandatory`
- `default_priority`
- `style_guideline`
- `default_fact_ids` opcional
- `target_tone` opcional

**Uso**
- alimentar al conciliador
- sostener decisiones regionales y academicas

---

## 4. Modelos del Job

## 4.1 `JobKG`

**Rol**
- version estructurada de la oferta

**Campos esperados**
- `hard_requirements`
- `soft_context`
- `logistics`
- `source_anchors`

---

## 4.2 `JobDelta`

**Rol**
- foco de relevancia para una postulacion puntual

**Campos consolidados**
- `must_highlight_ids` o `must_highlight_skills`
- `ignored_requirements`
- `custom_instructions`
- `soft_vibe_requirements`
- `logistics_flags`

**Uso**
- seleccionar que destacar y que omitir

---

## 5. Modelos de Matching

## 5.1 `MatchEdge`

**Rol**
- conectar requerimientos del job con evidencia del perfil

**Campos**
- `requirement_id`
- `profile_evidence_ids`
- `match_score`
- `reasoning`

---

## 6. Modelos de Blueprint

## 6.1 `SectionBlueprint`

**Rol**
- plan logico de una seccion

**Campos consolidados**
- `section_id`
- `logical_train_of_thought`
- `section_intent`
- `target_style` opcional
- `word_count_target` opcional

---

## 6.2 `GlobalBlueprint`

**Rol**
- plan maestro del bundle completo

**Campos consolidados**
- `application_id`
- `strategy_type`
- `sections` o `abstract_sections`

---

## 7. Modelos de Drafting

## 7.1 `DraftedSection`

**Rol**
- resultado textual de una seccion

**Campos**
- `section_id`
- `raw_markdown`
- `is_cohesive`
- `word_count`

---

## 7.2 `DraftedDocument`

**Rol**
- conjunto redactado por documento antes del ensamblado final

**Campos**
- `doc_type`
- `sections_md`
- `cohesion_score`

---

## 8. Modelos de Assembly

## 8.1 `MarkdownDocument`

**Rol**
- documento ensamblado con metadata inyectada

**Campos**
- `doc_type`
- `header_data`
- `body_markdown`
- `footer_data`

---

## 8.2 `FinalMarkdownBundle`

**Rol**
- artefacto final previo al render

**Campos consolidados**
- `cv_md` o `cv_full_md`
- `letter_md` o `letter_full_md`
- `email_md` o `email_body_md`
- `metadata_summary` o `rendering_metadata`

---

## 9. Modelo HITL

## 9.1 `GraphPatch`

**Rol**
- contrato universal para intervencion humana

**Campos consolidados**
- `action`
- `target_stage` opcional
- `target_type` opcional
- `target_id`
- `new_value`
- `feedback_note`
- `persist_to_profile`

**Valores esperados para `action`**
- `approve`
- `reject`
- `modify`
- `request_regeneration`
- `move_to_document` o `move_to_doc`

---

## 10. Modelos Regionales

## 10.1 `GermanSection`

**Rol**
- describir una seccion del esquema aleman

**Campos**
- `id`
- `label`
- `is_mandatory`
- `render_style`
- `allowed_fact_categories`

---

## 10.2 `GermanDocumentDefinition`

**Rol**
- contrato de layout para CV o carta alemanes

**Campos**
- `doc_type`
- `standard`
- `language`
- `layout_sequence`
- `require_photo`
- `require_signature`
- `date_format`

---

## 11. Criterios de Canonicalizacion

- elegir un solo nombre final para campos duplicados
- mantener alias de compatibilidad solo en etapa de transicion
- evitar mezclar semantica del grafo con metadata de render
- mantener modelos regionales separados de modelos core

---

## 12. Propuesta de Capas

- **Core contracts:** `TextAnchor`, `IdeaFact`, `MatchEdge`, `SectionBlueprint`, `GlobalBlueprint`, `GraphPatch`
- **Profile and job contracts:** `ProfileKG`, `SectionMapping`, `JobKG`, `JobDelta`
- **Output contracts:** `DraftedSection`, `DraftedDocument`, `MarkdownDocument`, `FinalMarkdownBundle`
- **Regional contracts:** `GermanSection`, `GermanDocumentDefinition`
