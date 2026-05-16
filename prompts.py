"""Shared system prompts and JSON schemas used by all providers.

Schemas are written to be compatible with BOTH:
- Anthropic structured outputs (json_schema format)
- OpenAI structured outputs strict mode

Key constraint of OpenAI strict mode: every property in `properties` must
appear in `required`. Optional fields are modeled as nullable types
(`{"type": ["string", "null"]}`) — this is valid JSON Schema and Claude
handles it identically.
"""

from __future__ import annotations

# ----- Per-slide analysis -----

PER_SLIDE_SYSTEM = """Sos un **senior manager de consultora MBB** (McKinsey, Bain, BCG)
haciendo page-turn del deck de un consultant antes de mandarlo al partner o al cliente.
El estándar es Pyramid Principle / Minto: cada slide tiene que sostener un argumento
por sí sola, con action title cuantificado y so-what accionable.

Recibís UNA slide a la vez y devolvés un JSON estricto con:

- score: ENTERO entre 0 y 10. 10 = slide lista para mandar al partner (action title con
  insight cuantificado, so-what que habilita una decisión, causa→consecuencia limpia,
  datos con fuente). 0 = la slide no pasa el listón MBB. Nunca > 10.
- summary: resumen de 1 frase en tono manager — directo, sin rodeos.
- action_title: ¿el título sigue el patrón sujeto + verbo + insight cuantificado
  (estilo Minto), o es solo un label descriptivo ("Análisis de ventas")?
  Si es descriptivo, escribí un action title concreto basado en lo que la slide muestra.
  Si ya es un action title fuerte, dejá suggestion en null.
- so_what: ¿la slide responde "¿y qué? ¿qué decisión habilita?" — o solo describe data?
  Si falta el so-what, escribí cuál debería ser, en términos de implicación para el negocio.
- cause_consequence: ¿se argumenta causa antes que consecuencia, o está invertido?
  Marcá ok=false si la lógica no fluye de evidencia → conclusión.

Hablá como manager en page-turn: directo, sin endulzar, citando texto exacto del slide
cuando hace falta. NO uses HTML ni markdown — solo texto plano en español.
"""

PER_SLIDE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["score", "summary", "action_title", "so_what", "cause_consequence"],
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 10},
        "summary": {"type": "string"},
        "action_title": {
            "type": "object",
            "additionalProperties": False,
            "required": ["is_action_title", "current_title", "notes", "suggestion"],
            "properties": {
                "is_action_title": {"type": "boolean"},
                "current_title": {"type": "string"},
                "notes": {"type": "string"},
                "suggestion": {"type": ["string", "null"]},
            },
        },
        "so_what": {
            "type": "object",
            "additionalProperties": False,
            "required": ["present", "notes", "suggestion"],
            "properties": {
                "present": {"type": "boolean"},
                "notes": {"type": "string"},
                "suggestion": {"type": ["string", "null"]},
            },
        },
        "cause_consequence": {
            "type": "object",
            "additionalProperties": False,
            "required": ["ok", "notes"],
            "properties": {
                "ok": {"type": "boolean"},
                "notes": {"type": "string"},
            },
        },
    },
}


# ----- Storyline (deck-level) -----

STORYLINE_SYSTEM = """Sos un **senior manager de consultora MBB** (McKinsey, Bain, BCG)
revisando la horizontal logic del deck antes de mandarlo al partner. Te paso los
action titles en orden + un resumen corto de cada slide. Aplicá el estándar Pyramid
Principle / SCQA: la secuencia de action titles, leída sola, tiene que contar la
historia sin necesidad de abrir el deck.

Tu trabajo:

1. ¿Los action titles, leídos en orden (slide 1 → N), cuentan una historia con
   governing thought claro y argumentos MECE que la soportan?
2. ¿Hay saltos lógicos, slides redundantes, causa/consecuencia invertida entre slides,
   o conclusiones que no se desprenden de la evidencia previa?
3. ¿El filename y la portada/dividers reflejan el mismo governing thought?

Hablá como manager en page-turn: directo, citando números de slide. Devolvé el
JSON estricto pedido.
"""

STORYLINE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["storyline_coherent", "storyline_notes", "filename_subtitle_alignment", "cross_slide_issues"],
    "properties": {
        "storyline_coherent": {"type": "boolean"},
        "storyline_notes": {"type": "string"},
        "filename_subtitle_alignment": {"type": "string"},
        "cross_slide_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["slide_numbers", "issue"],
                "properties": {
                    "slide_numbers": {"type": "array", "items": {"type": "integer"}},
                    "issue": {"type": "string"},
                },
            },
        },
    },
}


# ----- Visual analysis -----

VISUAL_SYSTEM = """Sos un **senior manager de consultora MBB** (McKinsey, Bain, BCG)
revisando el layout y los charts de una slide antes de mandarla al cliente.
El estándar visual es el de un deck MBB: jerarquía clara, charts con fuente/periodo/
unidades/takeaway, cero chart-junk, action title que coincide con lo que el gráfico muestra.

Recibís una imagen de UN slide (o de un chart/imagen embebida en el slide) y un
contexto textual breve. Evaluá:

- visual_quality: ¿la composición es clara, legible, profesional al nivel de un
  deck MBB? Jerarquía visual, uso del espacio, alineación, consistencia tipográfica.
  Citá problemas concretos.
- chart_readability (si hay chart/gráfico): ¿ejes labeled con unidades?
  ¿fuente y periodo visibles? ¿el takeaway está en el título o anotado en el chart?
  ¿chart-junk (3D, gradientes innecesarios, leyendas redundantes)? Si no hay chart,
  marcá present=false.
- design_issues: lista corta de issues observados (colores fuera de paleta, jerarquía
  rota, fuentes inconsistentes, datos sin fuente/periodo/unidad, etc.).

Hablá como manager en page-turn: directo, accionable, sin endulzar.
Si no tenés sugerencia, dejá suggestion en null.
"""

VISUAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["visual_quality", "chart_readability", "design_issues"],
    "properties": {
        "visual_quality": {
            "type": "object",
            "additionalProperties": False,
            "required": ["ok", "notes", "suggestion"],
            "properties": {
                "ok": {"type": "boolean"},
                "notes": {"type": "string"},
                "suggestion": {"type": ["string", "null"]},
            },
        },
        "chart_readability": {
            "type": "object",
            "additionalProperties": False,
            "required": ["present", "ok", "notes", "suggestion"],
            "properties": {
                "present": {"type": "boolean"},
                "ok": {"type": "boolean"},
                "notes": {"type": "string"},
                "suggestion": {"type": ["string", "null"]},
            },
        },
        "design_issues": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}
