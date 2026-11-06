# Privacidad y soporte — plugin `normativa-iccp` (borrador para el directorio de Anthropic)

> Vigencia: BORRADOR — 2026-09-24. Escrito por el plan 136, PASO 2, del toolkit
> (`urbanizacion-toolkit/plans/136-marketplace-publico-anthropic-alcance-y-gate.md`).
> Exigido por la [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
> para cualquier plugin enviado al directorio público: política de privacidad accesible +
> contacto de soporte verificado. **Contacto de soporte confirmado por JL el 2026-11-05
> (ver «Soporte» abajo). No enviar nada a Anthropic sin que JL apruebe también el resto
> de este texto.**

## Qué hace el plugin

`normativa-iccp` conecta Claude a un corpus normativo de obra civil (PG-3, 6.1-IC,
6.3-IC, Decreto 293/2009, VIV/561/2010 y similares) mediante un servidor MCP local que
hace búsqueda por texto (BM25) sobre una carpeta que el propio usuario indica al
instalar el plugin (`userConfig.corpus_root`). Incluye dos skills (`consulta-normativa`,
`segundo-dictamen-tecnico`) y un agente (`normativa-iccp`) que citan siempre la fuente
literal del corpus consultado.

## Qué datos toca y qué hace con ellos

- **Lee, en local, solo la carpeta que el usuario declara** (`CORE_NORMATIVA_ROOT`).
  Verificado en el PASO 2 del plan 136: el servidor MCP (`server/search_engine.py`,
  `server/procedencia_index.py`, `server/vigencia_index.py`) no contiene ninguna llamada
  de red saliente (`requests`, `urllib`, `httpx`, URLs `http(s)://`) — la búsqueda es
  enteramente local, sobre el índice BM25 que el propio servidor construye al arrancar.
- **No envía nada a servidores del despacho ni de terceros.** No hay telemetría, no hay
  llamada a ningún backend propio: el plugin no "llama a casa".
- **No lee memoria, historial de chat ni ficheros del usuario fuera de la carpeta
  declarada.** El agente y las skills citan solo lo que encuentran en
  `CORE_NORMATIVA_ROOT`; su propia regla inviolable (`agents/normativa-iccp/AGENT.md`)
  es "no citar normativa de memoria".
- **El corpus de demostración** (`corpus_muestra/` del repo publicado) es texto legal
  público (BOE/BOJA), sin datos de ningún cliente ni proyecto real — regla dura heredada
  del ecosistema (`bases-precios-compartidas/CLAUDE.md` y `PAQUETE_VENDIBLE.md` §«Sin
  datos de cliente»).
- **Datos del corpus real del usuario, si sustituye la muestra por el suyo**: siguen en
  su máquina o en la ruta que él controle; el plugin no los copia ni los transmite a
  ningún sitio.

## Qué NO hace (frente a la Anthropic Software Directory Policy)

- No mueve dinero ni cripto.
- No genera imágenes, audio ni vídeo con IA.
- No sirve publicidad.
- No instala ni ejecuta software adicional más allá del propio servidor MCP local en
  Python (sin dependencias de red).

## Soporte

- Contacto: **pepeluantunez@gmail.com** (email del despacho). Confirmado por JL
  2026-11-05.
- Alcance del soporte: dudas de instalación del plugin (`userConfig.corpus_root`),
  errores del servidor MCP, y reporte de normas mal citadas o desactualizadas en el
  corpus de muestra.
- Fuera de alcance del soporte del plugin: asesoría jurídica o interpretación normativa
  vinculante — el propio agente ya lo declara (cita literal + "interpretación" marcada
  aparte, nunca como dictamen legal).

## Versionado de este documento

Vive en este repo (`urbanizacion-marketplace-prototype/docs/`) porque aplica al plugin
que se publique desde aquí. Si el PASO 0 del plan 136 decide publicar desde un repo
distinto (más limpio, sin `DOSSIER_COMERCIAL.md`/`MAPA_CUMPLIMIENTO.md` al lado), este
fichero se copia allí tal cual, con el contacto ya confirmado.
