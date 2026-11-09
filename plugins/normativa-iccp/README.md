# normativa-iccp

Plugin de Claude Code para consultar normativa técnica de obra civil sobre un corpus de texto
local, citando siempre la fuente literal. No responde de memoria: si una norma no está en el
corpus cargado, lo dice.

## Qué incluye

- Un servidor MCP local (`server/`) que busca por texto (BM25) en la carpeta que tú indiques.
- Un agente (`normativa-iccp`) y dos skills: `consulta-normativa` y `segundo-dictamen-tecnico`.
- Una etiqueta de vigencia: si el corpus incluye el registro de vigencia, las normas derogadas se
  devuelven marcadas como DEROGADAS y con su sucesora, no como derecho vigente.
- `corpus_muestra/`: tres disposiciones oficiales (BOE) para probarlo sin cargar nada tuyo.

## Qué NO incluye

El plugin no trae el corpus normativo completo (PG-3, 6.1-IC, normas de compañías, UNE, etc.).
Lo que pueda citar es exactamente lo que cargues en tu propio corpus. Muchas de esas normas tienen
derechos de terceros: cárgalas solo si tienes derecho a usarlas.

## Instalación

```
claude plugin marketplace add pepeluantunez/normativa-iccp
claude plugin install normativa-iccp
```

Al instalar te pedirá `corpus_root`: la carpeta con `01_texto_extraido/` (texto en `.txt` o `.md`) y,
opcionalmente, `04_conocimiento/`, `_registry/` y `05_vigencia/`. Para probar, apunta a la carpeta
`corpus_muestra/` de este plugin.

Requisitos: Python 3 con la biblioteca estándar. Para que se marquen las normas derogadas hace falta
además PyYAML (`pip install pyyaml`); sin él el plugin funciona pero no etiqueta la vigencia.

## Ejemplos de uso (con el corpus de muestra)

1. «Qué dice la Orden TMA/851/2021 sobre la anchura mínima de un itinerario peatonal accesible.»
   Devuelve fragmentos literales con su norma de origen.
2. «Criterios sanitarios de calidad del agua de consumo.» Devuelve el Real Decreto 3/2023 y el
   Real Decreto 140/2003, este último marcado como DEROGADA con su sucesora.
3. «Cuál es el criterio de la compañía de aguas local para las acometidas.» Ese dato no está en el
   corpus de muestra: el agente debe responder que no aparece en la normativa cargada, en lugar de
   inventarlo.

## Privacidad y datos

Todo es local. El servidor no hace llamadas de red, no tiene telemetría y no escribe en disco; solo
lee la carpeta que declaras. Con el nivel de log `DEBUG` las consultas se vuelcan al registro de
error estándar (stderr) de tu equipo. Detalle en
[`docs/PRIVACIDAD_SOPORTE_MARKETPLACE.md`](../../docs/PRIVACIDAD_SOPORTE_MARKETPLACE.md).

## Aviso de uso

Es una ayuda de consulta: cita texto y marca aparte lo que es interpretación. No es asesoramiento
jurídico ni sustituye la verificación de la norma vigente en su fuente oficial ni el criterio del
técnico responsable del proyecto.

## Soporte

Incidencias: https://github.com/pepeluantunez/normativa-iccp/issues · pepeluantunez@gmail.com

## Licencia

MIT, ver [`LICENSE`](LICENSE). Los textos de `corpus_muestra/` son disposiciones oficiales
(art. 13 del texto refundido de la Ley de Propiedad Intelectual) y se distribuyen sin modificar.
