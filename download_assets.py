import bz2
import os
import shutil
import urllib.request
from huggingface_hub import snapshot_download

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(BASE_DIR, "bringing-old-photos-back-to-life")
CACHE_DIR = os.path.join(BASE_DIR, "hf_checkpoints")


def download_hf_checkpoints() -> None:
    print("Downloading Hugging Face checkpoints (databuzzword/bringing-old-photos-back-to-life)...")
    os.makedirs(CACHE_DIR, exist_ok=True)
    snapshot_download(
        repo_id="databuzzword/bringing-old-photos-back-to-life",
        local_dir=CACHE_DIR,
        ignore_patterns=["*.dat"],
    )

    for folder in ("Face_Enhancement", "Global"):
        src = os.path.join(CACHE_DIR, folder, "checkpoints")
        dest = os.path.join(REPO_DIR, folder, "checkpoints")
        if os.path.exists(src):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"[+] Copied {folder}/checkpoints")
        else:
            print(f"[!] Warning: {src} not found in downloaded snapshot")

    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
        print("[+] Cleaned up temporary hf_checkpoints cache")


def download_dlib_landmarks() -> None:
    dat_name = "shape_predictor_68_face_landmarks.dat"
    bz2_path = os.path.join(BASE_DIR, f"{dat_name}.bz2")
    dat_path = os.path.join(BASE_DIR, dat_name)

    if not os.path.exists(dat_path):
        url = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
        print(f"Downloading {dat_name}.bz2...")
        urllib.request.urlretrieve(url, bz2_path)
        print("Decompressing with bz2...")
        with bz2.open(bz2_path, "rb") as src_f, open(dat_path, "wb") as dst_f:
            shutil.copyfileobj(src_f, dst_f)
        os.remove(bz2_path)

    for subdir in ("Face_Enhancement", "Face_Detection"):
        dest_dir = os.path.join(REPO_DIR, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(dat_path, os.path.join(dest_dir, dat_name))
        print(f"[+] Placed {dat_name} in {subdir}/")

    if os.path.exists(dat_path):
        os.remove(dat_path)
        print(f"[+] Cleaned up temporary root {dat_name}")


if __name__ == "__main__":
    if not os.path.isdir(REPO_DIR):
        raise SystemExit(f"Repository not found at {REPO_DIR}")
    download_hf_checkpoints()
    download_dlib_landmarks()
    print("All assets downloaded and placed successfully!")

