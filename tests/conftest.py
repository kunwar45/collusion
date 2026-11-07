import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def load_workbench():
    """Import the in-image workbench CLI by path (it is not part of our package)."""
    path = REPO / "sandbox/rootfs/opt/workbench/workbench.py"
    spec = importlib.util.spec_from_file_location("workbench", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


requires_docker = pytest.mark.skipif(not docker_available(), reason="Docker daemon not available")
