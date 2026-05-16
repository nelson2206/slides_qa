# PPT QA Agent

Web app que toma un `.pptx` y produce un reporte de calidad por slide.

Diseñado para validar localmente todo lo posible antes de gastar tokens: la mayoría de los checks (largo de párrafos, antetítulos, alineación con filename y subtítulos, formato de títulos, duplicados, roles de slide) son determinísticos y corren sin tocar Anthropic. Solo el análisis semántico (action title quality, so-what, causa-consecuencia, storyline) usa la API.

## Estructura

```
ppt-qa-agent/
├── app.py                   # Streamlit web app — entrypoint principal
├── extractor.py             # python-pptx -> dict
├── checks.py                # Checks determinísticos
├── qa.py                    # Orquestador: run_local_qa | run_full_qa
├── keyloader.py             # Carga ANTHROPIC_API_KEY de env / .env / api_key.txt
├── pricing.py               # Estimador de costos
├── fixtures/synth.py        # Decks sintéticos "good" / "bad" para tests
├── tests/                   # pytest: extractor, checks, qa local mode (41 tests)
├── scripts/
│   ├── local_validate.py    # Smoke end-to-end sin API
│   ├── review.py            # CLI: review local de un .pptx real
│   └── full_review.py       # CLI: review full (gasta tokens) con cost estimate
├── requirements.txt
├── .gitignore               # excluye .env, api_key.txt, .anthropic_key, .venv, build/
└── README.md
```

## Setup

```powershell
cd C:\Users\nebernal\ppt-qa-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Modos

| Modo     | Modelos                                  | Cuándo usar                                       |
|----------|------------------------------------------|---------------------------------------------------|
| `local`  | Ninguno (todo en Python)                 | Iterar mientras construís; smoke tests; CI        |
| `full`   | `claude-sonnet-4-6` (por slide, paralelo, cache) + `claude-opus-4-7` (storyline, una sola llamada con thinking adaptive) | Reporte completo cuando el deck está estable |

El split es deliberado:
- **Por slide** → decisiones acotadas, estructuradas, paralelizables → **Sonnet 4.6** con prompt caching (cache write 1×, cache read N-1×).
- **Storyline cross-slide** → razonamiento estratégico, low-volume → **Opus 4.7** con `thinking: adaptive` y `effort: high` (una sola llamada).

Costo estimado para un deck de 58 slides (modo full): **~$0.86** (~$0.71 Sonnet + ~$0.15 Opus). El app muestra la estimación antes de correr.

## Workflow

### 1. Validar todo localmente (sin API)

```powershell
.\.venv\Scripts\python.exe -m pytest -v          # 41 tests
.\.venv\Scripts\python.exe scripts\local_validate.py    # smoke end-to-end
```

### 2. Lanzar la app web

```powershell
streamlit run app.py
```

Abre `http://localhost:8501`. En el sidebar elegís modo (local / full), subís el `.pptx`, y la app:

- **Tab "Deck overview"**: filename↔títulos, filename↔subtítulos, antetítulos (geometría + caps), formato de títulos, duplicados, distribución de roles.
- **Tab "Por slide"**: filtros (solo flagged, por role), expanders con action title / so-what / causa-consecuencia / largo de párrafos / antetítulo. Sugerencias accionables por slide.
- **Tab "Storyline"**: análisis cross-slide (solo modo full).
- **Tab "Tokens"**: uso por modelo y por tipo (input / cache write / cache read / output).
- **Tab "Export"**: descargar Markdown o JSON.

### 3. Modo full — dejar la API key

La app busca la key en este orden:
1. Variable de entorno `ANTHROPIC_API_KEY`.
2. Archivo `.env` con `ANTHROPIC_API_KEY=sk-ant-...`.
3. Archivo `api_key.txt` con la key cruda.
4. Input manual en el sidebar (solo para esa sesión).

Todos los archivos están en `.gitignore`. La app muestra de dónde se cargó la key (mascarada).

### 4. CLI alternativo (sin levantar app)

```powershell
.\.venv\Scripts\python.exe scripts\review.py "ruta\al\deck.pptx"
.\.venv\Scripts\python.exe scripts\full_review.py "ruta\al\deck.pptx" --max-slides 5
.\.venv\Scripts\python.exe scripts\full_review.py "ruta\al\deck.pptx" --yes --out-md reporte.md
```

## Cobertura de checks

| Check                       | Local | Full | Cómo se evalúa                                                                                |
|-----------------------------|:----:|:---:|-----------------------------------------------------------------------------------------------|
| Largo de párrafos           | ✅   | ✅  | Estimación de líneas + word count. Detecta candidatos a bulletear.                            |
| Antetítulos — presencia     | ✅   | ✅  | Heurística geométrica: shape encima del título con altura menor.                              |
| Antetítulos — alineación    | ✅   | ✅  | Rango de `top_in` y `height_in` entre slides con antetítulo.                                  |
| Antetítulos — caps          | ✅   | ✅  | Title case vs ALL CAPS vs mixto.                                                              |
| Slide role                  | ✅   | ✅  | cover / divider / content_with_title / content_no_title / minimal.                            |
| Filename ↔ títulos          | ✅   | ✅  | Overlap de keywords (normalizado, sin stopwords).                                             |
| Filename ↔ subtítulos       | ✅   | ✅  | Específicamente sobre placeholders SUBTITLE.                                                  |
| Consistencia formato títulos| ✅   | ✅  | Detecta mix de cortos (1-3 palabras) + largos (8+).                                           |
| Títulos duplicados          | ✅   | ✅  | Slides con título idéntico.                                                                   |
| **Action title (calidad)**  | ❌   | ✅  | Sonnet 4.6 juzga + propone uno mejor si es descriptivo.                                       |
| **So-what por slide**       | ❌   | ✅  | Sonnet 4.6 detecta presencia de conclusión.                                                   |
| **Causa → consecuencia**    | ❌   | ✅  | Sonnet 4.6 detecta inversiones intra-slide.                                                   |
| **Storyline cross-slide**   | ❌   | ✅  | Opus 4.7 + thinking adaptive sobre la secuencia.                                              |

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

41 tests cubren:
- Extractor de pptx contra fixtures sintéticas
- Cada check determinístico individual (paragraph length, ante-title, caps, role, filename, subtitle, format consistency, duplicates)
- Comportamiento end-to-end del modo local sobre good/bad fixtures
- Que el modo local **no importe `anthropic`** (corre incluso si la SDK no está instalada)

## Deployment (compartir con otros)

El app está pensado para correr en cualquier host con Python — Streamlit Cloud, Hugging Face Spaces, Render, Railway, Fly.io, o un VM propio.

### Lo que funciona en cualquier deployment

- Extracción del .pptx (`python-pptx`, puro Python)
- Todos los checks determinísticos
- Análisis full con Claude o OpenAI (solo necesitás las API keys)
- Análisis visual de charts embebidos
- **Miniaturas Schematic** (Pillow) — funciona donde sea

### Miniaturas fieles: requiere LibreOffice en el servidor

| Backend | Funciona en | Setup |
|---|---|---|
| Schematic | Cualquier host | Cero |
| LibreOffice | Linux / Mac / Windows con Office libre | Instalar `libreoffice` + `poppler-utils` |
| PowerPoint COM | Solo Windows local con Office | **No deployable** |

### Deploy a Streamlit Cloud (gratis)

1. Push el repo a GitHub
2. En [share.streamlit.io](https://share.streamlit.io), conectá el repo
3. El archivo `packages.txt` ya está pre-configurado con `libreoffice` y `poppler-utils` — Streamlit Cloud los instala automáticamente
4. Agregar `ANTHROPIC_API_KEY` y/o `OPENAI_API_KEY` en Settings → Secrets

### Deploy con Docker (self-host)

```bash
docker build -t ppt-qa .
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e OPENAI_API_KEY=sk-... \
  ppt-qa
```

El `Dockerfile` incluido instala LibreOffice + poppler + fonts. La imagen final pesa ~1.5GB.

### Notas para compartir el app

- **Cada usuario consume API tokens de TU cuenta** (si compartís keys). Considerá implementar auth, billing, o pedir que traigan su propia key.
- En modo local (sin API), el app es 100% gratis de operar — solo el costo del hosting.
- Cache de miniaturas se hace por `st.session_state` — cada usuario re-rendera al subir un archivo.

## Limitaciones conocidas

- El extractor no toca imágenes ni gráficos — solo texto (el análisis visual de modo full sí los analiza).
- La detección de pie de página es heurística (basada en posición geométrica); funciona bien cuando el footer está en la parte inferior-izquierda.
- La estimación de líneas asume ~80 chars por línea — útil para flag, pero el render real depende del tamaño de fuente y del ancho del placeholder.
- En modo full, decks muy grandes (>50 slides) pueden tardar 30-60s por el análisis paralelo. La app muestra status en vivo.
- Las heurísticas de action title y so-what en modo local son aproximadas (basadas en conteo de palabras y marcadores de conclusión). Para juicios semánticos confiables, modo full.
