#!/usr/bin/env bash
# ═══ JEE Tutor — one-time environment setup (Ubuntu/Debian) ═══
set -e
cd "$(dirname "$0")"

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null; then SUDO="sudo"; fi

echo "── [1/4] System packages (ffmpeg, Manim libs, LaTeX) ──────────"
$SUDO apt-get update -qq
$SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev \
    texlive-latex-base texlive-latex-recommended texlive-fonts-recommended \
    texlive-science texlive-latex-extra dvisvgm

echo "── [2/4] Python dependencies ──────────────────────────────────"
pip install -r requirements.txt

echo "── [3/4] Frontend assets (KaTeX + three.js) ───────────────────"
mkdir -p static/js
if [ ! -f static/js/katex/katex.min.js ]; then
    curl -sL https://github.com/KaTeX/KaTeX/releases/download/v0.16.11/katex.tar.gz -o /tmp/katex.tar.gz
    tar xzf /tmp/katex.tar.gz -C static/js
    echo "   KaTeX installed"
else
    echo "   KaTeX already present"
fi
if [ ! -f static/js/three.min.js ]; then
    curl -sL -o static/js/three.min.js https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js
    echo "   three.js installed"
else
    echo "   three.js already present"
fi

echo "── [4/4] API key ──────────────────────────────────────────────"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Created .env — put your Gemini API key in it (GEMINI_API_KEY=...)"
else
    echo "   .env present"
fi

echo ""
echo "✅ Setup complete. Run the app with:  ./run.sh   (then open http://localhost:8000)"
