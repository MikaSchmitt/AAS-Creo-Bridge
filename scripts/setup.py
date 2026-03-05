from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


CREOSON_URL_NO_JRE = (
    "https://github.com/SimplifiedLogic/creoson/releases/download/v3.0.0/"
    "CreosonServer-3.0.0-win64.zip"
)
CREOSON_URL_WITH_JRE = (
    "https://github.com/SimplifiedLogic/creoson/releases/download/v3.0.0/"
    "CreosonServerWithSetup-3.0.0-win64.zip"
)

CREOSON_SHA256_NO_JRE = "ef3e9bb4870bf2e4888956571820c1133a00e5e0ec716bf3abeda08dd0cde77b"
CREOSON_SHA256_WITH_JRE = "93a4b4d0abd31f0d91fb771407ca6e362ca5a66e29cdb404c3dc9f96382c4ef9"


def project_root_from_this_file() -> Path:
    # This file is expected at <repo>/scripts/setup.py
    return Path(__file__).resolve().parents[1]


def download_file(url: str, dest_path: Path) -> None:
    """
    Download using stdlib only (no `requests` dependency).
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    req = Request(
        url,
        headers={
            # Some endpoints behave better with a UA.
            "User-Agent": "AAS-Creo-Bridge-setup/1.0 (+python urllib)",
        },
        method="GET",
    )

    with urlopen(req, timeout=60) as resp:
        # Basic HTTP status handling (urlopen raises for many errors already)
        status = getattr(resp, "status", 200)
        if status and status >= 400:
            raise RuntimeError(f"Download failed with HTTP status {status} for URL: {url}")

        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_sha256(path: Path, expected_hex: str) -> None:
    expected_hex = expected_hex.strip().lower()
    actual_hex = sha256_file(path).lower()
    if actual_hex != expected_hex:
        raise RuntimeError(
            "SHA-256 verification failed.\n"
            f"  File: {path}\n"
            f"  Expected: {expected_hex}\n"
            f"  Actual:   {actual_hex}\n"
        )
    print(f"[ok] SHA-256 verified: {actual_hex}")


def extract_zip(zip_path: Path, dest_dir: Path, force: bool) -> None:
    if dest_dir.exists():
        if not force:
            print(f"[skip] '{dest_dir}' already exists. Use --force to overwrite.")
            return
        print(f"[info] Removing existing '{dest_dir}' (forced).")
        shutil.rmtree(dest_dir)

    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    print(f"[ok] Extracted to: {dest_dir}")


def is_running_in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def venv_python_executable(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_venv(repo_root: Path, venv_dir_name: str = "venv") -> Path:
    """
    Returns a Python executable to use for installing deps:
    - If already in a venv, uses the current interpreter.
    - Otherwise ensures <repo_root>/<venv_dir_name> exists and uses its interpreter.
    """
    if is_running_in_venv():
        return Path(sys.executable)

    venv_dir = repo_root / venv_dir_name
    py_exe = venv_python_executable(venv_dir)

    if not py_exe.exists():
        print(f"[info] Creating virtual environment at: {venv_dir}")
        venv.EnvBuilder(with_pip=True, clear=False, upgrade_deps=False).create(venv_dir)

    if not py_exe.exists():
        raise RuntimeError(f"Virtualenv Python not found at: {py_exe}")

    return py_exe


def pip_install_requirements(repo_root: Path) -> None:
    req_file = repo_root / "requirements.txt"
    if not req_file.exists():
        print(f"[skip] No requirements.txt found at: {req_file}")
        return

    py_exe = ensure_venv(repo_root)
    print(f"[info] Using Python for dependency install: {py_exe}")
    print(f"[info] Installing dependencies from: {req_file}")

    subprocess.check_call(
        [str(py_exe), "-m", "pip", "install", "-r", str(req_file)],
        cwd=str(repo_root),
    )
    print("[ok] Dependencies installed.")


def assert_java_21_jre_present() -> None:
    """
    Checks for a system Java runtime by invoking `java -version` and verifying major version 21.
    This is a practical check (PATH-based). It intentionally fails fast with a helpful message.
    """
    try:
        proc = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "Java 21 JRE is required when installing Creoson *without* the embedded JRE, "
            "but `java` was not found on PATH.\n"
            "Install a Java 21 JRE and ensure `java -version` works from a new terminal."
        ) from e

    # `java -version` typically writes to stderr, but we consider both.
    output = (proc.stderr or "") + "\n" + (proc.stdout or "")
    m = re.search(r'version\s+"(?P<ver>\d+)(?:\.\d+)?(?:\.\d+)?(?:[^\s"]*)"', output)
    if not m:
        raise RuntimeError(
            "Could not determine Java version from `java -version` output.\n"
            "Expected to find something like: version \"21.0.2\".\n"
            f"Actual output:\n{output.strip()}"
        )

    major = int(m.group("ver"))
    if major != 21:
        raise RuntimeError(
            "Java 21 JRE is required when installing Creoson *without* the embedded JRE.\n"
            f"Detected Java major version: {major}\n"
            f"`java -version` output:\n{output.strip()}\n"
            f"Install a Java 21 JRE and ensure `java -version` works from a new terminal.\n"
            f"You can also install CREOSON with the embedded JRE by passing --embedded-jre to setup.py."
        )

    print("[ok] Java 21 detected on system (java -version).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up repo: download/unpack Creoson and optionally install Python deps."
    )
    parser.add_argument(
        "--embedded-jre",
        action="store_true",
        help="Download Creoson bundle that includes an embedded JRE (larger ZIP).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing creoson directory if it exists",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install Python dependencies from requirements.txt (ensures/uses venv).",
    )
    args = parser.parse_args()

    repo_root = project_root_from_this_file()
    creoson_dir = repo_root / "creoson"

    url = CREOSON_URL_WITH_JRE if args.embedded_jre else CREOSON_URL_NO_JRE
    expected_sha = CREOSON_SHA256_WITH_JRE if args.embedded_jre else CREOSON_SHA256_NO_JRE

    print(f"[info] Project root: {repo_root}")
    print(f"[info] Creoson destination: {creoson_dir}")
    print(f"[info] Creoson package: {'with embedded JRE' if args.embedded_jre else 'without embedded JRE'}")

    if not args.embedded_jre:
        assert_java_21_jre_present()

    with tempfile.TemporaryDirectory() as td:
        zip_path = Path(td) / "creoson.zip"
        print(f"[info] Downloading Creoson ZIP:\n  {url}")
        download_file(url, zip_path)
        print(f"[ok] Downloaded to: {zip_path}")

        print(f"[info] Verifying SHA-256:\n  expected {expected_sha}")
        verify_sha256(zip_path, expected_sha)

        extract_zip(zip_path, creoson_dir, force=args.force)

    if args.install_deps:
        pip_install_requirements(repo_root)

    print("[done] Setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())