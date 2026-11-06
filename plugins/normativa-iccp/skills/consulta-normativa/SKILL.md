---
name: consulta-normativa
description: 'Responde normativa de obra civil con el corpus CORE-NOR, siempre con cita. Usar: retorno, diametros, pendientes, accesibilidad.'
---

# Skill: Consulta Normativa

## Cuando invocar esta skill

Responde preguntas de normativa de obra civil usando el corpus CORE-NOR. Cita siempre el codigo CORE-NOR. Nunca inventa valores. Usar: periodos de retorno, diametros, pendientes, anchuras, accesibilidad, materiales de saneamiento.


## Cuando usar esta skill

Cuando el usuario pregunte por:
- Periodos de retorno, caudales de calculo o metodologia hidrologica (pluviales)
- Diametros minimos, pendientes, materiales de colectores o acometidas (saneamiento)
- Anchuras de acera, pendientes de rampa, medidas de vados o plazas PMR (accesibilidad)
- Cualquier valor numerico regulado por las normas del corpus CORE-NOR

Palabras clave: "que diametro", "pendiente minima", "periodo de retorno", "anchura de acera", "vado", "accesibilidad", "normativa de", "que dice la norma", "cual es el maximo", "cual es el minimo", "EMASA exige", "Decreto 293".

---

## Proceso

### Paso 1 — Identificar el ambito tematico

Determinar si la pregunta corresponde a:
- **Pluviales / drenaje** → leer `04_conocimiento/drenaje/drenaje_pluviales_base.md`
- **Saneamiento fecales** → leer `04_conocimiento/saneamiento/saneamiento_fecales_base.md`
- **Accesibilidad** → leer `04_conocimiento/accesibilidad/accesibilidad_base.md`
- **Agua potable / abastecimiento** → leer `04_conocimiento/agua/agua_emasa_base.md`
- **Ambito desconocido** → leer `04_conocimiento/INDEX.md` para localizar la ficha correcta

### Paso 2 — Leer la ficha de conocimiento

Leer el archivo `*_base.md` completo del ambito identificado. Extraer:
- El nucleo normativo (codigos CORE-NOR activos)
- Los valores numericos solicitados con su procedencia (seccion "Nucleo normativo" o "Decisiones" o tabla de "Parametros")
- El articulo o apartado exacto que respalda el valor

### Paso 3 — Verificar en el texto fuente si el valor no esta en la ficha

Si el valor no consta en la ficha de conocimiento:
- Localizar el archivo fuente en `01_texto_extraido/` usando el codigo CORE-NOR (ver `02_indices/core_aliases.csv` para la correspondencia nombre → codigo)
- Buscar el articulo o apartado especifico
- Si tampoco consta en el texto fuente: declarar "no consta en fuentes disponibles del corpus"

### Paso 4 — Formular la respuesta

La respuesta debe:
1. Citar el codigo CORE-NOR del que procede el valor: `CORE-NOR-XXXX, art. Y`
2. Indicar el valor literal tal como aparece en la fuente (entre comillas si es cita textual)
3. Si hay condiciones de aplicacion (ej. en funcion del periodo de retorno, del diametro de la conduccion incidente, de la longitud del tramo), indicarlas
4. Si el valor no consta en el corpus: decirlo explicitamente — "no consta en fuentes disponibles del corpus"

---

## Reglas de veracidad

- **Nunca inventar valores numericos.** Si un dato no esta en las fichas ni en los textos fuente del corpus, la unica respuesta valida es "no consta en fuentes disponibles".
- **Nunca citar normativa de memoria.** Todos los valores citados deben estar respaldados por texto literal en `01_texto_extraido/` o por las fichas de `04_conocimiento/`.
- **Nunca mezclar valores de normas distintas** sin indicar claramente a que norma corresponde cada uno.
- Si hay conflict entre una norma estatal y una autonómica (ej. Decreto 293/2009 vs RD 505/2007), indicar la jerarquia aplicable: en Andalucia prevalece la norma autonómica mas exigente salvo disposicion expresa en contrario.

---

## Ejemplo de respuesta correcta

**Pregunta:** "Cual es el diametro minimo de la red de saneamiento fecal por gravedad en EMASA?"

**Respuesta:** Segun `CORE-NOR-0039` (Normas Tecnicas de Saneamiento EMASA, apartado 2.2), el diametro minimo de las tuberias por gravedad de la red de alcantarillado es DN 300 mm. Para la red de pluviales por gravedad el minimo es DN 400 mm. Para acometidas de viviendas el minimo es DN 200 mm.

---

## Ejemplo de respuesta cuando falta el dato

**Pregunta:** "Cual es la velocidad minima de autolimpieza exigida por EMASA para colectores?"

**Respuesta:** El indice del Capítulo 4.5.1.3 de las Normas Tecnicas de Saneamiento EMASA menciona "Velocidad del agua" y el 4.5.1.6 "Autolimpieza de los colectores", pero el contenido de esos articulos no consta en las fuentes disponibles del corpus (solo se ha incorporado el indice del documento). Para obtener el valor exacto hay que consultar el documento original `CORE-NOR-0039`.

---

## Codigos CORE-NOR activos por ambito

Consultar `02_indices/core_aliases.csv` para el mapeo completo. Codigos mas frecuentes:

| Ambito | Codigo | Norma |
|---|---|---|
| Pluviales | CORE-NOR-0026 | 5.2-IC Drenaje Superficial |
| Pluviales | CORE-NOR-0053 | PG-3 Parte 4 Drenaje |
| Pluviales | CORE-NOR-0033 | IH-100 Maximas Precipitaciones |
| Pluviales | CORE-NOR-0038 | Recomendaciones Drenaje Carreteras |
| Saneamiento | CORE-NOR-0039 | Normas Tecnicas Saneamiento EMASA |
| Saneamiento | CORE-NOR-0040 | EMASA Injerencias 2022 |
| Saneamiento | CORE-NOR-0031 | RDL 11/1995 Aguas Residuales |
| Saneamiento | CORE-NOR-0032 | RD 509/1996 Aguas Residuales |
| Accesibilidad | CORE-NOR-0002 | Decreto 293/2009 (Andalucia) |
| Accesibilidad | CORE-NOR-0003 | RDL 1/2013 Discapacidad |
| Accesibilidad | CORE-NOR-0047 | Ley 1/1999 Accesibilidad Andalucia |
| Abastecimiento | CORE-NOR-0041 | Normas Tecnicas Abastecimiento EMASA |
| Abastecimiento | CORE-NOR-0040 | EMASA Injerencias 2022 |
