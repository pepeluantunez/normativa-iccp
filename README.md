# normativa-iccp

Plugin de Claude Code para consulta y verificación de normativa técnica de obra civil
(PG-3, 6.1-IC, 6.3-IC, 5.2-IC, Decreto 293/2009, VIV/561/2010, EMASA) sobre un corpus
normativo local aportado por el usuario. Cita siempre la fuente literal; no responde
de memoria.

## Qué incluye

- `plugins/normativa-iccp/`: servidor MCP (`.mcp.json`), un agente (`agents/`) y dos
  skills (`consulta-normativa`, `segundo-dictamen-tecnico`).
- El servidor solo lee el corpus local que el usuario declara en `corpus_root`
  (ver `userConfig` en `plugin.json`) — no hace llamadas de red salientes.

## Instalación

```
claude plugin marketplace add pepeluantunez/normativa-iccp
claude plugin install normativa-iccp
```

Al instalar, Claude Code pedirá la ruta local a tu corpus normativo
(`corpus_root`: carpeta con `01_texto_extraido/`, `02_indices/` y `04_conocimiento/`).

## Privacidad y soporte

Ver [`docs/PRIVACIDAD_SOPORTE_MARKETPLACE.md`](docs/PRIVACIDAD_SOPORTE_MARKETPLACE.md).
Contacto de soporte: pepeluantunez@gmail.com

## Licencia

MIT — ver [`LICENSE`](LICENSE).
