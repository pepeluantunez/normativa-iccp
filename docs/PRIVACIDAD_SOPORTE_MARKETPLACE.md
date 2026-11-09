# Privacidad y soporte — plugin `normativa-iccp`

## Qué hace el plugin

`normativa-iccp` conecta Claude Code con un corpus normativo de obra civil mediante un servidor
MCP local que busca por texto (BM25) en la carpeta que el usuario indica al instalar
(`corpus_root`). Incluye un agente y dos skills que citan la fuente literal del corpus consultado.

## Qué datos toca y qué hace con ellos

- Lee, en local, solo la carpeta declarada en `corpus_root` (variable `CORE_NORMATIVA_ROOT`).
- El código del servidor (`plugins/normativa-iccp/server/`) no contiene llamadas de red salientes
  ni escritura en disco; solo escribe respuestas por la salida estándar del propio protocolo MCP.
  Se comprobó revisando el código fuente publicado en este repositorio.
- No envía nada a servidores del autor ni de terceros. No hay telemetría ni servicio propio.
- No lee la memoria, el historial de conversación ni ficheros del usuario fuera de esa carpeta.
- No guarda datos: el índice de búsqueda se construye en memoria al arrancar y se descarta al cerrar.
- Con el nivel de log `DEBUG` las consultas se vuelcan a la salida de error (stderr) del equipo del
  usuario; con el nivel por defecto (`INFO`) no.
- Los datos del corpus del usuario se quedan en su equipo; el plugin no los copia ni los transmite.
  Los fragmentos que Claude reciba como respuesta de una consulta se tratan según las condiciones
  de Claude/Anthropic aplicables al usuario, ajenas a este plugin.

## Qué NO hace

- No mueve dinero ni criptoactivos, no genera imágenes, audio ni vídeo, no sirve publicidad.
- No instala ni ejecuta software adicional: solo su propio servidor MCP en Python.
- No incluye normativa de terceros con derechos de autor (UNE, normas de compañías, guías).

## Corpus de muestra

`plugins/normativa-iccp/corpus_muestra/` contiene cuatro disposiciones oficiales publicadas en el
BOE (Ley 4/2017 de Andalucía, Título VIII; Orden TMA/851/2021; Real Decreto 3/2023, Capítulo II;
Real Decreto 140/2003, solo como aviso de norma derogada). Las disposiciones oficiales no son
objeto de propiedad intelectual (art. 13 del texto refundido de la Ley de Propiedad Intelectual).
No contiene datos de ningún cliente ni proyecto. El texto procede de la legislación consolidada
publicada en el BOE; antes de citar una norma en un documento, debe contrastarse con su fuente
oficial.

## Aviso de uso

Es una herramienta de consulta. Cita texto y marca la interpretación aparte; no constituye
asesoramiento jurídico ni sustituye la verificación de la norma vigente ni el criterio del técnico
responsable.

## Soporte

- Incidencias y preguntas: https://github.com/pepeluantunez/normativa-iccp/issues
- Correo: pepeluantunez@gmail.com
- Alcance: dudas de instalación (`corpus_root`), errores del servidor MCP y normas mal citadas o
  desactualizadas en el corpus de muestra. Quedan fuera la asesoría jurídica y la interpretación
  normativa vinculante.
