#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  JEE Tutor — Oracle Cloud one-command installer
#
#  On a fresh Ubuntu VM (22.04/24.04), run ONE command:
#
#    sudo bash oci-install.sh <your-gemini-api-key>
#
#  If your code is in a git repo:
#    sudo bash oci-install.sh <your-gemini-api-key> https://github.com/you/jee-tutor.git
#
#  If you uploaded jee-tutor.zip to the VM instead:
#    sudo bash oci-install.sh <your-gemini-api-key> local-jee-tutor.zip
# ═══════════════════════════════════════════════════════════════════════════
set -e

KEY="${1:?Usage: sudo bash oci-install.sh <gemini-api-key> [repo-url | local-zip]}"
SRC="${2:-}"
APP_DIR="/opt/jee-tutor"
RUN_USER="${SUDO_USER:-ubuntu}"

echo "── [1/7] System packages ─────────────────────────────────────────────"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv git curl unzip ffmpeg \
    libcairo2-dev libpango1.0-dev pkg-config python3-dev \
    texlive-latex-base texlive-latex-recommended texlive-fonts-recommended \
    texlive-science texlive-latex-extra dvisvgm >/dev/null

echo "── [2/7] Fetching app source ─────────────────────────────────────────"
rm -rf "$APP_DIR"
if [ -n "$SRC" ] && [[ "$SRC" == *.zip ]]; then
    mkdir -p "$APP_DIR"
    unzip -q "$SRC" -d /tmp/jeeunpack
    TOPDIR=$(find /tmp/jeeunpack -mindepth 1 -maxdepth 1 -type d | head -1)
    if [ -n "$TOPDIR" ] && [ -f "$TOPDIR/app.py" ]; then
        cp -r "$TOPDIR"/. "$APP_DIR"/
    else
        cp -r /tmp/jeeunpack/. "$APP_DIR"/
    fi
    rm -rf /tmp/jeeunpack
elif [ -n "$SRC" ]; then
    git clone --depth 1 "$SRC" "$APP_DIR"
else
    echo "ERROR: give me a repo URL or a zip file (see usage at the top)."
    echo "Or upload the jee-tutor folder contents to the VM first and pass its zip."
    exit 1
fi
cd "$APP_DIR"

echo "── [3/7] Python environment ──────────────────────────────────────────"
python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

echo "── [4/7] Frontend assets (KaTeX + three.js) ─────────────────────────"
mkdir -p static/js
if [ ! -f static/js/katex/katex.min.js ]; then
    curl -sL https://github.com/KaTeX/KaTeX/releases/download/v0.16.11/katex.tar.gz -o /tmp/katex.tar.gz
    tar xzf /tmp/katex.tar.gz -C static/js
fi
[ -f static/js/three.min.js ] || curl -sL -o static/js/three.min.js \
    https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js

echo "── [5/7] Configuration (.env) ────────────────────────────────────────"
if [ -f .env.example ]; then cp .env.example .env; fi
if [ -f .env ]; then
    grep -v '^GEMINI_API_KEY=' .env > .env.tmp || true
    { cat .env.tmp; echo "GEMINI_API_KEY=$KEY"; rm .env.tmp; } > .env
else
    printf 'GEMINI_API_KEY=%s\nGEMINI_MODEL=gemini-3.6-flash\nMANIM_QUALITY=-ql\nTHINKING=1\n' "$KEY" > .env
fi
chown -R "$RUN_USER":"$RUN_USER" "$APP_DIR"

echo "── [6/7] systemd service (auto-start + auto-restart) ────────────────"
cat > /etc/systemd/system/jee-tutor.service <<UNIT
[Unit]
Description=JEE Tutor - Advanced Solver
After=network.target
[Service]
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now jee-tutor

echo "── [7/7] Firewall (in-VM iptables) ───────────────────────────────────"
if command -v iptables >/dev/null && [ -d /etc/iptables ]; then
    iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
    if command -v netfilter-persistent >/dev/null; then netfilter-persistent save >/dev/null || true; fi
fi

sleep 2
systemctl --no-pager -l status jee-tutor | head -6 || true
IP=$(curl -s --max-time 4 ifconfig.me || echo "<VM_PUBLIC_IP>")
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  ✅ DONE.  Open:   http://${IP}:8000"
echo "  If it doesn't load yet: open port 8000 in the OCI Console →"
echo "  Instance → Subnet → Security List → Add Ingress Rule:"
echo "  Source 0.0.0.0/0 · TCP · Destination port 8000"
echo "  Then: Settings (⚙) in the app → set an Access PIN!"
echo "════════════════════════════════════════════════════════════════════"
