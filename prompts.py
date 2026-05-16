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

PER_SLIDE_SYSTEM = """Sos un experto en presentaciones ejecutivas tipo consultoría.
Recibís UNA slide a la vez y devolvés un JSON estricto con:

- action_title: ¿el título es un *action title* (sujeto+verbo+conclusión con insight),
  o solo descriptivo? Si es descriptivo, proponé uno mejor basado en el contenido.
  Si ya es un action title bueno, dejá suggestion en null.
- so_what: ¿hay una conclusión / implicación visible? Si no, sugerí cuál sería en suggestion.
- cause_consequence: ¿se argumenta causa antes que consecuencia? Si está invertido, marcá.

Sé directo y específico. Citá texto exacto cuando ayude.
"""

PER_SLIDE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["score", "summary", "action_title", "so_what", "cause_consequence"],
    "properties": {
        "score": {"type": "integer"},
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

STORYLINE_SYSTEM = """Sos un experto en storyline ejecutivo. Te paso los action titles
de un deck en orden + un resumen corto de cada slide. Tu trabajo:

1. ¿La secuencia de action titles cuenta una historia coherente leída de izquierda
   a derecha (slide 1 -> slide N)?
2. ¿Hay saltos lógicos, slides que sobran, o causa/consecuencia invertida entre slides?
3. ¿El nombre del archivo se refleja en los títulos clave (portada, dividers)?

Devolvé el JSON estricto pedido.
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

VISUAL_SYSTEM = """Sos un experto en diseño de presentaciones ejecutivas.
Recibís una imagen de UN slide (o de un chart/imagen embebida en el slide) y un
contexto textual breve. Evaluá:

- visual_quality: ¿la composición es clara, legible, profesional? Citá problemas concretos.
- chart_readability (si hay chart/gráfico): ¿los ejes están labeled? ¿la conclusión es visible?
  ¿hay junk visual? Si no hay chart, marcá present=false.
- design_issues: lista corta de issues observados (colores discordantes, jerarquía visual,
  fuentes inconsistentes, datos sin contexto, etc.).

Sé concreto y accionable. Si no tenés sugerencia, dejá suggestion en null.
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
