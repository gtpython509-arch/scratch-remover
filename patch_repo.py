import os
import sys


def patch_repo(repo_dir: str) -> None:
    run_py = os.path.join(repo_dir, "run.py")
    if os.path.exists(run_py):
        with open(run_py, "r", encoding="utf-8") as f:
            code = f.read()
        if "import os" in code and "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD" not in code:
            patch = 'import os\nos.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"\n'
            code = code.replace("import os\n", patch, 1)
            with open(run_py, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"[+] Patched {run_py}")

    patched_count = 0
    for root, _, files in os.walk(repo_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file == "networks.py":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                target = "from detection_models.sync_batchnorm import DataParallelWithCallback"
                replacement = (
                    "try:\n"
                    "    from detection_models.sync_batchnorm import DataParallelWithCallback\n"
                    "except ImportError:\n"
                    "    from torch.nn import DataParallel as DataParallelWithCallback"
                )
                if target in content:
                    content = content.replace(target, replacement)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[+] Patched {file_path}")
                    patched_count += 1
            elif file == "normalization.py":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                target = "from models.networks.sync_batchnorm import SynchronizedBatchNorm2d"
                replacement = (
                    "try:\n"
                    "    from models.networks.sync_batchnorm import SynchronizedBatchNorm2d\n"
                    "except ImportError:\n"
                    "    from torch.nn import BatchNorm2d as SynchronizedBatchNorm2d"
                )
                if target in content:
                    content = content.replace(target, replacement)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[+] Patched {file_path}")
                    patched_count += 1

    print(f"Patch complete. Patched {patched_count} network files.")


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "bringing-old-photos-back-to-life")
    patch_repo(os.path.abspath(target_dir))

