# Deploying BOPBTL Photo Restoration API on Hostinger VPS

This folder is ready to run both locally on Windows and on a Hostinger Ubuntu/Debian VPS.

## Files Included
- `app.py` — FastAPI server (`GET /`, `POST /restore`), auto-detects CUDA GPU or falls back to CPU (`--GPU -1`).
- `download_assets.py` — Downloads Hugging Face checkpoints (`databuzzword/bringing-old-photos-back-to-life`) and `shape_predictor_68_face_landmarks.dat`.
- `patch_repo.py` — Applies `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` and `sync_batchnorm` compatibility patches.
- `requirements.txt` — Python dependencies.
- `setup_vps.sh` — Automated Ubuntu/Debian VPS installer.
- `bopbtl.service` — `systemd` service to keep Uvicorn running in the background.
- `nginx.conf` — Nginx reverse proxy (port 80 -> `127.0.0.1:8000`, 50 MB upload limit, 300s timeout).

---

## Step-by-Step Hostinger VPS Deployment

1. **Connect to your Hostinger VPS via SSH:**
   ```bash
   ssh root@YOUR_VPS_IP
   ```

2. **Clone your GitHub repository into `/opt/scratch-remover`:**
   ```bash
   git clone https://github.com/ansaftab-1/scratch-remover-model.git /opt/scratch-remover
   cd /opt/scratch-remover
   ```
   *(`.gitignore` excludes `.venv`, model checkpoints, and `bringing-old-photos-back-to-life` from GitHub — `setup_vps.sh` downloads and sets them up cleanly on the VPS.)*

3. **Run the VPS setup script:**
   ```bash
   cd /opt/scratch-remover
   chmod +x setup_vps.sh
   ./setup_vps.sh
   ```
   > **Note:** On a CPU-only VPS, `dlib` compiles from source (requires at least 2 GB RAM or swap; if your VPS has 1–2 GB RAM, add a 2G swapfile first).

4. **Enable and start the `systemd` service:**
   ```bash
   sudo cp /opt/scratch-remover/bopbtl.service /etc/systemd/system/bopbtl.service
   sudo systemctl daemon-reload
   sudo systemctl enable bopbtl
   sudo systemctl start bopbtl
   sudo systemctl status bopbtl
   ```

5. **Configure Nginx reverse proxy:**
   ```bash
   sudo cp /opt/scratch-remover/nginx.conf /etc/nginx/sites-available/bopbtl
   sudo ln -sf /etc/nginx/sites-available/bopbtl /etc/nginx/sites-enabled/bopbtl
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Allow HTTP traffic in firewall (if UFW is enabled):**
   ```bash
   sudo ufw allow 'Nginx Full'
   ```

7. **Verify:**
   - Health check: `http://YOUR_VPS_IP/`
   - Swagger UI: `http://YOUR_VPS_IP/docs`
   - Restore endpoint: `POST http://YOUR_VPS_IP/restore`

