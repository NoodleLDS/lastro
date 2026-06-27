import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

# Caminho fixo do projeto: o .exe pode ser movido (ex.: área de trabalho),
# então não derivamos isso de __file__/sys.executable.
PROJECT_ROOT = Path(r"C:\Users\Lucas\Downloads\lastro")
LOG_PATH = PROJECT_ROOT / "launcher" / "lastro_launcher.log"
WEB_URL = "http://localhost:5173"
API_HEALTH_URL = "http://localhost:8000/health"
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
DOCKER_FALLBACK_PATHS = [
    r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
]


def find_docker() -> str:
    found = shutil.which("docker")
    if found:
        return found
    for fallback in DOCKER_FALLBACK_PATHS:
        if Path(fallback).exists():
            return fallback
    return "docker"


def docker_compose_up() -> subprocess.CompletedProcess:
    docker_exe = find_docker()
    return subprocess.run(
        [docker_exe, "compose", "up", "-d"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def wait_for_api(timeout_seconds: int = 120) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = httpx.get(API_HEALTH_URL, timeout=2)
            if response.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1)
    return False


def open_in_chrome(url: str) -> None:
    for chrome_path in CHROME_PATHS:
        if Path(chrome_path).exists():
            subprocess.Popen([chrome_path, "--new-window", url])
            return
    webbrowser.open(url)


def log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def show_error(message: str) -> None:
    log(message)
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "Lastro", 0x10)
    except Exception:
        pass


def main() -> int:
    LOG_PATH.write_text("", encoding="utf-8")
    log("Subindo containers do Lastro...")
    try:
        result = docker_compose_up()
    except FileNotFoundError:
        show_error("Comando 'docker' não encontrado. Instale o Docker Desktop e tente novamente.")
        return 1

    log(f"returncode={result.returncode} stderr={result.stderr}")
    if result.returncode != 0:
        show_error(
            "Falha ao rodar 'docker compose up -d'. O Docker Desktop está aberto?\n\n"
            + result.stderr
        )
        return 1

    log("Esperando a API ficar pronta...")
    if not wait_for_api():
        show_error("A API não respondeu em tempo. Confira 'docker compose logs api'.")
        return 1

    log("Abrindo o Lastro no Chrome...")
    open_in_chrome(WEB_URL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
