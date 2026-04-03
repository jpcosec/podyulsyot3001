# Generate Documents - Regional and Special Cases

**Date:** 2026-03-31
**Scope:** Casos particulares por pais, dominio y tipo de documento.

---

## 1. Objetivo

Este documento separa las variantes regionales y academicas para que no queden mezcladas con el pipeline core.

---

## 2. Alemania - Profesional

## 2.1 CV / Lebenslauf

- incluir foto
- incluir fecha de nacimiento
- incluir nacionalidad
- incluir firma
- usar estructura tabulada o cronologica clara
- priorizar residencia actual y permiso de trabajo si aplica

## 2.2 Carta / Anschreiben

Secciones esperadas:
- `Absender`
- `Empfangerbezeichnung`
- `Ort_Datum`
- `Betreffzeile`
- `Anrede`
- `Einleitung`
- `Hauptteil_1`
- `Hauptteil_2`
- `Schlusssatz`
- `Grussformel`
- `Anlagenverzeichnis`

## 2.3 Email

- formalidad alta
- asunto claro
- referencia de oferta si existe

---

## 3. Chile - Profesional

## 3.1 CV

- priorizar resumen ejecutivo
- priorizar logros cuantificados
- ocultar datos sensibles si no aportan

## 3.2 Carta

- propuesta de valor directa
- foco en resolver necesidades concretas del empleador

## 3.3 Email

- breve
- ejecutivo
- enfocado en disponibilidad y cierre rapido

---

## 4. Academico

## 4.1 CV academico

- research interests
- research experience
- education con tesis
- publications
- teaching
- grants/awards
- referencias academicas

## 4.2 Carta academica

- proposito del programa o fondo
- background academico
- investigacion actual
- alineacion con supervisor o laboratorio
- vision futura

---

## 5. Selector de Estrategia

El pipeline debe activar una estrategia segun metadata del job.

Ejemplos:
- `Professional_German`
- `Academic_German`
- `Professional_Chile`

Cada estrategia activa:
- set de secciones
- reglas de metadata
- tono base
- hechos obligatorios o prohibidos

---

## 6. Casos Logistico-Contextuales

## 6.1 Visa o permiso de trabajo

- se incluye solo si el mercado o el job lo vuelve relevante
- en Alemania puede subir de prioridad
- en Chile normalmente se omite si no aporta

## 6.2 Doble direccion o residencia internacional

- el assembler debe elegir la direccion correcta segun pais del job
- esta decision no debe quedar en manos del redactor

## 6.3 Hobbies o afinidad cultural

- entran solo si mejoran el match
- pueden aparecer en carta y no en CV
- pueden sobrevivir por afinidad sectorial, por ejemplo transporte ferroviario
