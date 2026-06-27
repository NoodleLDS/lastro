import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path

import httpx

# Caminho fixo do projeto: o .exe pode ser movido (ex.: área de trabalho),
# então não derivamos isso de __file__/sys.executable.
PROJECT_ROOT = Path(r"C:\Users\Lucas\Downloads\lastro")
LOG_PATH = PROJECT_ROOT / "launcher" / "lastro_launcher.log"
SYMBOL_PATH = PROJECT_ROOT / "frontend" / "public" / "branding" / "lastro-symbol.png"
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


class LoadingWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Lastro")
        self.root.geometry("360x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#14110f")
        self._center()

        if SYMBOL_PATH.exists():
            self._image = tk.PhotoImage(file=str(SYMBOL_PATH))
            self._image = self._image.subsample(
                max(1, self._image.width() // 96), max(1, self._image.height() // 96)
            )
            tk.Label(self.root, image=self._image, bg="#14110f").pack(pady=(24, 8))

        tk.Label(
            self.root,
            text="Lastro",
            fg="#f1ece6",
            bg="#14110f",
            font=("Segoe UI", 16, "bold"),
        ).pack()

        self.status_label = tk.Label(
            self.root,
            text="Subindo containers...",
            fg="#b3a89d",
            bg="#14110f",
            font=("Segoe UI", 10),
        )
        self.status_label.pack(pady=(8, 0))

    def _center(self) -> None:
        self.root.update_idletasks()
        width, height = 360, 220
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def set_status(self, text: str) -> None:
        self.status_label.config(text=text)

    def show_error(self, text: str) -> None:
        self.status_label.config(text=text, fg="#f0654f", wraplength=320)

    def close(self) -> None:
        self.root.destroy()


def run_startup(window: LoadingWindow) -> None:
    LOG_PATH.write_text("", encoding="utf-8")
    log("Subindo containers do Lastro...")
    window.root.after(0, window.set_status, "Subindo containers...")

    try:
        result = docker_compose_up()
    except FileNotFoundError:
        message = "Docker não encontrado. Instale o Docker Desktop e tente novamente."
        log(message)
        window.root.after(0, window.show_error, message)
        return

    log(f"returncode={result.returncode} stderr={result.stderr}")
    if result.returncode != 0:
        message = "Falha ao subir os containers. O Docker Desktop está aberto?"
        window.root.after(0, window.show_error, message)
        return

    log("Esperando a API ficar pronta...")
    window.root.after(0, window.set_status, "Esperando a API ficar pronta...")
    if not wait_for_api():
        message = "A API não respondeu em tempo. Confira o log do launcher."
        log(message)
        window.root.after(0, window.show_error, message)
        return

    log("Abrindo o Lastro no Chrome...")
    window.root.after(0, window.set_status, "Abrindo o Chrome...")
    open_in_chrome(WEB_URL)
    time.sleep(1)
    window.root.after(0, window.close)


def main() -> int:
    window = LoadingWindow()
    thread = threading.Thread(target=run_startup, args=(window,), daemon=True)
    thread.start()
    window.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
