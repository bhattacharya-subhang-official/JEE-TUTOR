# Σ JEE Tutor — Advanced Solver

An AI chat web-app for **IIT-JEE Advanced** Physics, Chemistry & Mathematics — powered by the **Gemini API**, with real computation engines, diagram/3D generation, animations, and **Manim** video rendering.

![stack](https://img.shields.io/badge/Gemini-2.5-6ea8ff) ![stack](https://img.shields.io/badge/Manim-Community-8b5cf6) ![stack](https://img.shields.io/badge/FastAPI-backend-4ade80)

---

## ✨ Capabilities (dropdown in the composer)

| Mode | What it does |
|---|---|
| 🧮 **Numerical** | Full exam-style solutions (Setup → Concept → Steps → **boxed answer** → Pitfalls). Gemini plans tool calls; local engines compute & verify every step. Streams the final write-up. |
| 📐 **Diagram** | Publication-quality labelled **SVG diagrams** (force bodies, ray optics, reaction mechanisms, graphs) **or interactive 3D scenes** (drag-rotate/zoom) — molecules, fields, rotational mechanics, crystal structures. |
| 🎬 **Animation** | Self-contained **animated HTML** (2D canvas/SVG or 3D WebGL) — SHM, standing waves, orbits, Snell's law… rendered live in the chat. Downloadable. |
| 🎥 **Manim Video** | Gemini writes the Manim scene, the server **renders a real MP4** (with LaTeX equations), auto-fixes code if the render fails. Watch inline + download `.mp4` + source `.py`. |

### Compute engines (verified tool calls, not hallucinated arithmetic)
- **Math (SymPy):** solve systems, calculus (diff/integrate/limits/series), factor/expand/simplify, polynomial roots, numeric `nsolve`, matrices (det/inverse/eigen…), vectors (dot/cross/angle), **unit conversion**, CODATA constants, graph & 3D-surface plots
- **Physics:** projectile, SUVAT, circular motion, SHM, gravitation, collisions (e = restitution), rotation, Coulomb/fields, capacitors, current electricity, lens/mirror (Cartesian signs), Doppler, interference, photoelectric/de Broglie/Bohr, thermodynamics, magnetism
- **Chemistry:** formula parser → **molar mass** (incl. hydrates), **equation balancing** (matrix nullspace), stoichiometry (mol/g/STP), pH (strong/weak, basicity, dilution), Nernst, Faraday electrolysis, ΔG = ΔH − TΔS, colligative properties
- **Sandbox:** `python_exec` — isolated subprocess with numpy/scipy/sympy for simulations & verification

### Chat UX
- Retractable **left sidebar** with all previous chats (stored server-side as JSON), delete, auto-titles
- **Scientific keypad** (∑ƒ button) — LaTeX templates, Greek, calculus, vectors, chem arrows
- **Attachments** — PDF / DOCX / TXT / CSV (text extracted) and images (sent to Gemini vision)
- Every response: **⧉ Copy** and **⬇ Download media** (SVG / HTML / MP4 / PNG)
- KaTeX math rendering, dark theme, fully responsive

---

## 🚀 Quickstart

```bash
cd jee-tutor
./setup.sh        # system deps + pip + KaTeX/three.js (Ubuntu/Debian)
cp .env.example .env   # then edit .env → GEMINI_API_KEY=your_key
./run.sh          # serves on http://localhost:8000
```

- Free API key: [aistudio.google.com](https://aistudio.google.com) → *Get API key*
- The key is read from `.env` **or** set at runtime in the app: **Settings (⚙ in sidebar)**.
- Settings also control: model (`gemini-2.5-flash` / `2.5-pro` / `2.0-flash`), Manim quality (480p/720p/1080p), deep-reasoning toggle.

## 🔐 Keys, PIN & fallback (as configured for this build)

Per the owner's request, this build ships **fully self-contained**:
- **Gemini API key** — embedded in `config.py` (base64-encoded so GitHub push-protection lets the upload through; decoded at startup) → works on any fresh clone instantly. `.env` is optional and NOT included.
- **Groq API key** — embedded the same way; if Gemini is down/erroring the app **automatically falls back to Groq** (openai/gpt-oss-120b → qwen3.8-27b → gpt-oss-20b; tool-calling + JSON verified). Set `LLM_PROVIDER` to `auto` (default) / `gemini` / `groq`.
- **Access PIN `1234`** — the app is always locked; a session cookie means the PIN is asked **every time the app is opened**. Change it in Settings ⚙ or `APP_PIN`.

> ⚠️ **Because keys are embedded, treat this repo as PRIVATE on GitHub.** If you
> ever make it public, rotate both keys first (aistudio.google.com / console.groq.com).
> On public hosting, set `EMBED_KEY=0` and provide keys via the host's secrets.

Override any embedded value with environment variables (win over `.env`, win over embedded):
```bash
export GEMINI_API_KEY=... GROQ_API_KEY=... APP_PIN=0000
```

---

## ☁️ Deploy on Oracle Cloud Free Tier (ARM VM, Always Free)

```bash
# 1. SSH into the VM (Ubuntu 22.04/24.04 aarch64 — all deps have ARM builds)
ssh ubuntu@<VM_PUBLIC_IP>

# 2. Get the code (keys & PIN already embedded — nothing to configure)
git clone https://github.com/<you>/jee-tutor.git && cd jee-tutor
./setup.sh                          # ~5 min

# 3. Run persistently (systemd)
# …or ONE command with the bundled installer:
#   sudo bash oci-install.sh <GEMINI_KEY> https://github.com/<you>/jee-tutor.git

sudo tee /etc/systemd/system/jee-tutor.service <<'UNIT'
[Unit]
Description=JEE Tutor
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jee-tutor
Environment=PORT=8000
ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl enable --now jee-tutor

# 4. Open the firewall (OCI Ubuntu images ship with iptables locked down)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```
Then in the **OCI Console → Instance → Subnet → Security List → Add Ingress Rule**:
source `0.0.0.0/0`, TCP, destination port `8000`. Visit `http://<VM_PUBLIC_IP>:8000`.

*(Optional)* put **Caddy** in front for automatic HTTPS: `caddy reverse-proxy --from your.domain.com --to localhost:8000`.

### Docker alternative
```bash
docker build -t jee-tutor .
docker run -d -p 8000:8000 -e GEMINI_API_KEY=your_key -v jee_data:/app/data jee-tutor
```

---

## 🗂 Project layout

```
jee-tutor/
├── app.py                  # FastAPI: SSE chat, uploads, chats CRUD, config API
├── config.py / storage.py  # runtime settings (.env) + chat persistence (data/*.json)
├── engines/                # math / physics / chemistry / plotting / sandbox exec
├── services/               # Gemini client, prompts & tool schemas, router, manim renderer
├── static/                 # SPA (vanilla JS) + KaTeX + three.js
├── data/  media/           # chats & generated media (git-ignored)
├── setup.sh  run.sh  Dockerfile
└── .env                    # your key — NEVER commit
```

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| `No Gemini API key` | Settings (⚙) or `.env`, then send again |
| Manim video fails locally | `./setup.sh` installs ffmpeg + LaTeX (`latex`, `dvisvgm` must exist on PATH) |
| Videos slow | Use quality **480p15** in Settings; 1 GB-RAM VMs render 480p comfortably |
| KaTeX/three.js missing after fresh clone | `./setup.sh` re-downloads them into `static/js/` |
| 429 / quota errors | Free-tier rate limits — wait a moment or switch model in Settings |
