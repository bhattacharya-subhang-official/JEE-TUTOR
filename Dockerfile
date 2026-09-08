# ═══ JEE Tutor — container image (includes full Manim + LaTeX stack) ═══
FROM python:3.12-slim

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev curl \
    texlive-latex-base texlive-latex-recommended texlive-fonts-recommended \
    texlive-science texlive-latex-extra dvisvgm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# frontend assets (baked into image)
RUN mkdir -p static/js \
    && curl -sL https://github.com/KaTeX/KaTeX/releases/download/v0.16.11/katex.tar.gz -o /tmp/katex.tar.gz \
    && tar xzf /tmp/katex.tar.gz -C static/js \
    && curl -sL -o static/js/three.min.js https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js

ENV PORT=8000
EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
