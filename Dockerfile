# PPT QA Agent — production image
# Builds on Debian slim with LibreOffice + poppler so the thumbnail
# renderer has a deployment-safe backend.

FROM python:3.12-slim

# System deps: LibreOffice (for slide rendering), poppler (for pdf2image),
# fonts so Inter renders consistently.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice \
        libreoffice-impress \
        poppler-utils \
        fonts-inter \
        fonts-noto \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Streamlit defaults: no headless flag → set explicitly for container
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# API keys should be passed at runtime, not baked into the image:
#   docker run -e ANTHROPIC_API_KEY=... -e OPENAI_API_KEY=... -p 8501:8501 ppt-qa

CMD ["streamlit", "run", "app.py"]
