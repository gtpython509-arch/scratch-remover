#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "=== 1. Installing system packages (Ubuntu/Debian) ==="
sudo apt-get update
sudo apt-get install -y \
  git python3 python3-venv python3-pip \
  cmake build-essential pkg-config \
  libgl1 libglib2.0-0 wget bzip2 nginx

echo "=== 2. Cloning Microsoft BOPBTL repository ==="
if [ ! -d "$APP_DIR/bringing-old-photos-back-to-life" ]; then
  git clone https://github.com/microsoft/bringing-old-photos-back-to-life "$APP_DIR/bringing-old-photos-back-to-life"
fi

echo "=== 3. Creating Python virtual environment ==="
python3 -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
pip install --upgrade pip

echo "=== 4. Installing PyTorch (CPU by default; swap index-url if VPS has NVIDIA GPU) ==="
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r "$APP_DIR/requirements.txt"

echo "=== 5. Downloading model checkpoints & dlib landmarks ==="
python "$APP_DIR/download_assets.py"

echo "=== 6. Applying compatibility patches ==="
python "$APP_DIR/patch_repo.py" "$APP_DIR/bringing-old-photos-back-to-life"

echo "=== Setup complete! ==="
echo "Next: install systemd service & nginx config (see DEPLOY_HOSTINGER_VPS.md)."

