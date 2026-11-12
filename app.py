import ctypes
import os
import shutil
import subprocess
import sys
import uuid
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

app = FastAPI(title="BOPBTL Photo Restoration API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(BASE_DIR, "bringing-old-photos-back-to-life")
WORKSPACE_DIR = os.path.join(BASE_DIR, "api_workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def safe_cli_path(path: str) -> str:
    """Return Windows 8.3 short path (no spaces) when available so run.py's unquoted shell commands work."""
    if sys.platform == "win32":
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024):
            return buf.value
    return path


def get_gpu_arg() -> str:
    env_gpu = os.environ.get("BOPBTL_GPU")
    if env_gpu is not None:
        return env_gpu
    return "0" if torch.cuda.is_available() else "-1"


def cleanup_job(job_dir: str) -> None:
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir, ignore_errors=True)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "model": "Bringing Old Photos Back to Life",
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/restore")
async def restore_photo(
    file: UploadFile = File(...),
    with_scratch: bool = Form(True),
):
    if not os.path.isdir(REPO_DIR):
        raise HTTPException(
            status_code=500,
            detail="BOPBTL repository directory not found. Run setup first.",
        )

    job_id = str(uuid.uuid4())
    job_dir = os.path.abspath(os.path.join(WORKSPACE_DIR, job_id))
    input_dir = os.path.join(job_dir, "input")
    output_dir = os.path.join(job_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1] or ".png"
    safe_filename = f"image_{job_id[:8]}{ext}"
    input_path = os.path.join(input_dir, safe_filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cmd = [
        sys.executable,
        "run.py",
        "--input_folder",
        safe_cli_path(input_dir),
        "--output_folder",
        safe_cli_path(output_dir),
        "--GPU",
        get_gpu_arg(),
    ]
    if with_scratch:
        cmd.append("--with_scratch")

    env = os.environ.copy()
    venv_bin = os.path.dirname(sys.executable)
    env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

    result = subprocess.run(cmd, cwd=REPO_DIR, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        cleanup_job(job_dir)
        raise HTTPException(
            status_code=500,
            detail=f"Restoration failed: {result.stderr or result.stdout}",
        )

    final_output_dir = os.path.join(output_dir, "final_output")
    restored_files = (
        os.listdir(final_output_dir) if os.path.exists(final_output_dir) else []
    )
    if not restored_files:
        cleanup_job(job_dir)
        raise HTTPException(status_code=500, detail="No output image was generated.")

    output_file_path = os.path.join(final_output_dir, restored_files[0])

    return FileResponse(
        path=output_file_path,
        media_type="image/png",
        filename=f"restored_{file.filename or 'output.png'}",
        background=BackgroundTask(cleanup_job, job_dir),
    )

