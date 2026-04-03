# Generate Documents - Extension Guide

**Date:** 2026-03-31
**Scope:** Guia para agregar nuevos casos, estrategias, secciones o reglas al pipeline.

---

## 1. Agregar un nuevo pais o estrategia

## 1.1 Definir contexto

- nombre de estrategia
- pais o dominio
- tipo de documentos afectados
- tono objetivo

## 1.2 Definir reglas de secciones

- secciones obligatorias
- secciones opcionales
- orden base
- metadata obligatoria

## 1.3 Definir reglas de assembly

- formato de fecha
- direccion de remitente/destinatario
- firma, foto, anexos, referencias

---

## 2. Agregar una nueva seccion

Checklist:
- crear `section_id`
- definir target document
- definir si es obligatoria
- definir estilo esperado
- definir categorias de facts permitidas
- decidir si entra en blueprint, drafting y assembly

---

## 3. Agregar un nuevo tipo de hecho

Checklist:
- definir como se almacena en `P1`
- definir como se referencia en `IdeaFact`
- definir si puede entrar por HITL 1 como evidencia emergente
- definir en que secciones y mercados aplica

---

## 4. Agregar una nueva regla de matching

Checklist:
- definir el requerimiento del job que activa la regla
- definir la evidencia del perfil que puede satisfacerla
- definir prioridad
- definir si necesita confirmacion humana

---

## 5. Agregar una nueva regla de profile update

Checklist:
- definir si actualiza `P1` o `P2`
- definir bajo que acciones de `GraphPatch` corre
- definir si necesita validacion extra
- definir alcance: factual, estructural o tonal

---

## 6. Regla de oro

Cuando se agregue algo nuevo, decidir primero en que capa vive:
- matching
- blueprint
- drafting
- assembly
- render
- learning

Si no se define bien la capa, el pipeline se acopla mal.
