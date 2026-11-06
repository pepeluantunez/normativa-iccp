---
name: segundo-dictamen-tecnico
description: 'Verificacion tecnica contra normativa del proyecto (CONFORME/NO_CONFORME). Invocar: "cumple normativa", "dictamen tecnico".'
---

# Segundo Dictamen Técnico

## Cuando invocar esta skill

Verificacion tecnica estructurada contra la normativa activa del proyecto. Emite CONFORME/NO_CONFORME/REQUIERE_VERIFICACION con citas literales. Invocar: "cumple normativa", "dictamen tecnico", "valida esta decision de diseno".


## Objetivo

Verificar que una decisión técnica concreta cumple la normativa aplicable disponible en el corpus local, emitiendo un veredicto explícito con citas literales — sin inventar artículos ni completar con memoria general.

Este proceso no reemplaza la responsabilidad del técnico. Actúa como capa de verificación antes de incorporar la decisión a un documento o BC3.

> **Diferencia con skills cercanas (S8 PLAN_PULIDO)**:
> - `abogado-del-diablo` simula objeciones de revisores externos (ayuntamiento, interventor). Usar al cerrar entregables.
> - `challenge-ecosistema` cuestiona la adopción de tecnología nueva en el ecosistema, no decisiones de expediente.
> - `segundo-dictamen-tecnico` (esta skill) verifica una decisión técnica concreta contra normativa con citas literales.

---

## Protocolo de ejecución

### Paso 1 — Recibir la decisión a verificar

El usuario debe formular la decisión como:

```text
DECISIÓN: <descripción concreta>
CONTEXTO: <disciplina, anejo o documento afectado>
NORMATIVA SOSPECHOSA: <norma o código si se conoce, opcional>
```

Ejemplo:
```text
DECISIÓN: Pendiente longitudinal de 7% en vial de 40 m de longitud, sin escalera ni rampa alternativa.
CONTEXTO: Anejo 12 — Accesibilidad, vial secundario
NORMATIVA SOSPECHOSA: Decreto 293/2009
```

### Paso 2 — Consultar el corpus normativo

Ejecutar `query_normativa` (tool del MCP normativa-mcp) con los términos clave de la decisión.
Si hay dominio claro, añadir `domain_filter`.

Si normativa-mcp no está disponible, buscar en `core_normativa/04_conocimiento/<dominio>/<dominio>_base.md`.

Si no existe ficha para el dominio, declarar **REQUIERE_VERIFICACION** sin emitir CONFORME/NO_CONFORME.

### Paso 3 — Identificar artículos pertinentes

De los resultados, extraer los párrafos o artículos directamente aplicables a la decisión.
Citar literalmente. No parafrasear si hay texto disponible.

Formato de cita:
```
[FUENTE: <nombre_documento>, <artículo/apartado si consta>]
"<texto literal>"
```

Si el fragmento está truncado, indicarlo: `[fragmento parcial]`.

### Paso 4 — Emitir veredicto

Elegir **uno** de los tres estados:

| Estado | Criterio |
|---|---|
| **CONFORME** | La decisión cumple los requisitos literales de la norma aplicable sin excepciones. |
| **NO_CONFORME** | La decisión incumple uno o más requisitos literales de la norma. Indicar qué incumple y el valor correcto si consta. |
| **REQUIERE_VERIFICACION** | No hay texto suficiente en el corpus para emitir un veredicto seguro. Puede ser norma no extraída, stub, fragmento parcial, o caso no cubierto. |

### Paso 5 — Formato de salida

```
## Segundo Dictamen Técnico

**Decisión evaluada:** <descripción>
**Dominio:** <dominio>
**Corpus consultado:** <lista de documentos consultados>

### Citas normativas aplicables

[FUENTE: ...]
"..."

[FUENTE: ...]
"..."

### Veredicto: CONFORME | NO_CONFORME | REQUIERE_VERIFICACION

<Una o dos frases explicando el veredicto. Si es NO_CONFORME, indicar el valor o requisito correcto. Si es REQUIERE_VERIFICACION, indicar qué falta y cómo resolverlo.>

### Acción recomendada

<Qué debe hacer el técnico: corregir el diseño, verificar manualmente, añadir norma al corpus, etc.>
```

---

## Reglas de comportamiento

- **Nunca inventar artículos.** Si no consta en el corpus, decirlo explícitamente.
- **Nunca emitir CONFORME sin cita literal** que lo respalde.
- **NO_CONFORME implica indicar el valor correcto** cuando la norma lo especifica.
- **REQUIERE_VERIFICACION no es un fallo** — es información honesta sobre el límite del corpus disponible.
- Si la decisión involucra varias normas (p. ej. IC + Decreto autonómico), verificar ambas por separado.
- No evaluar decisiones eléctricas (anejos 9-11) ni de telecomunicaciones (18) — fuera del alcance civil.

---

## Casos de uso frecuentes

| Decisión | Dominio | Norma típica |
|---|---|---|
| Pendiente longitudinal de rampa o vial | accesibilidad | Decreto 293/2009, VIV/561/2010 |
| DN de colector de pluviales | drenaje | 5.2-IC, EMASA |
| Caudal de diseño T=10/25 años | drenaje | 5.2-IC |
| Anchura de acera o IPA | accesibilidad | Decreto 293/2009 |
| Espesor de capa de firme | firmes | 6.1-IC |
| Material de tubería saneamiento | saneamiento | EMASA Normas Técnicas |
| Velocidad máxima en colector | saneamiento | EMASA Normas Técnicas |
| Plazas PMR en aparcamiento | accesibilidad | Decreto 293/2009 |
| Señal de obra en intersección | señalización | 8.3-IC |

---

## Integración con el flujo de proyecto

Este skill se invoca típicamente:

1. Antes de cerrar un anejo con soluciones dimensionales.
2. Cuando el BC3 recoge unidades que implican dimensionamiento normado.
3. Ante discrepancias entre documentos (Excel ≠ Memoria ≠ Plano).
4. Cuando un check QA detecta una anomalía que requiere contraste normativo.
5. Como filtro de revisión antes de remitir a compañías suministradoras.

No invocar para redacción pura de texto ni para reorganización de documentos.
