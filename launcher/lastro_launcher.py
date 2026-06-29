import json
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

# Caminho fixo do projeto: o .exe pode ser movido (ex.: área de trabalho),
# então não derivamos isso de __file__/sys.executable.
PROJECT_ROOT = Path(r"C:\Users\Lucas\Downloads\lastro")
LOG_PATH = PROJECT_ROOT / "launcher" / "lastro_launcher.log"
LOGO_PATH = PROJECT_ROOT / "frontend" / "public" / "branding" / "lastro-logo-horizontal-dark-bg.png"
WEB_URL = "http://localhost:5173"
API_HEALTH_URL = "http://localhost:8000/health"
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
DOCKER_FALLBACK_PATHS = [
    r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
]
DOCKER_DESKTOP_EXE = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
CONTROL_SERVER_PORT = 9100
ALLOWED_ORIGINS = {"http://localhost:5173"}


def find_docker() -> str:
    found = shutil.which("docker")
    if found:
        return found
    for fallback in DOCKER_FALLBACK_PATHS:
        if Path(fallback).exists():
            return fallback
    return "docker"


def docker_engine_is_running() -> bool:
    docker_exe = find_docker()
    result = subprocess.run(
        [docker_exe, "info"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return result.returncode == 0


def start_docker_desktop() -> None:
    subprocess.Popen([DOCKER_DESKTOP_EXE], stdin=subprocess.DEVNULL)


def wait_for_docker_engine(timeout_seconds: int = 90) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if docker_engine_is_running():
            return True
        time.sleep(2)
    return False


def docker_compose_up(force_recreate: bool = False) -> subprocess.CompletedProcess:
    docker_exe = find_docker()
    args = [docker_exe, "compose", "up", "-d"]
    if force_recreate:
        args.append("--force-recreate")
    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def docker_compose_down() -> subprocess.CompletedProcess:
    docker_exe = find_docker()
    return subprocess.run(
        [docker_exe, "compose", "down"],
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
        self.root.geometry("420x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#14110f")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_requested)
        self.on_exit_requested: Callable[[], None] | None = None
        self._center()

        if LOGO_PATH.exists():
            self._image = tk.PhotoImage(file=str(LOGO_PATH))
            self._image = self._image.subsample(
                max(1, self._image.width() // 240), max(1, self._image.height() // 80)
            )
            tk.Label(self.root, image=self._image, bg="#14110f").pack(pady=(32, 16))

        self.status_label = tk.Label(
            self.root,
            text="Subindo containers...",
            fg="#b3a89d",
            bg="#14110f",
            font=("Segoe UI", 10),
        )
        self.status_label.pack(pady=(8, 0))

        self.exit_button = tk.Button(
            self.root,
            text="Sair (desliga os containers)",
            command=self.on_close_requested,
            state=tk.DISABLED,
        )
        self.exit_button.pack(pady=(16, 0))

    def _center(self) -> None:
        self.root.update_idletasks()
        width, height = 420, 220
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def set_status(self, text: str) -> None:
        self.status_label.config(text=text)

    def show_error(self, text: str) -> None:
        self.status_label.config(text=text, fg="#f0654f", wraplength=320)

    def enable_exit_button(self) -> None:
        self.exit_button.config(state=tk.NORMAL)

    def disable_exit_button(self) -> None:
        self.exit_button.config(state=tk.DISABLED)

    def on_close_requested(self) -> None:
        if self.on_exit_requested is not None:
            self.on_exit_requested()

    def close(self) -> None:
        self.root.destroy()


class ControlRequestHandler(BaseHTTPRequestHandler):
    window: "LoadingWindow"

    def _send_json(self, status: int, body: dict[str, str]) -> None:
        origin = self.headers.get("Origin", "")
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/restart":
            threading.Thread(target=run_restart, args=(self.window,), daemon=True).start()
            self._send_json(200, {"status": "restarting"})
        elif self.path == "/shutdown":
            threading.Thread(target=run_shutdown, args=(self.window,), daemon=True).start()
            self._send_json(200, {"status": "shutting down"})
        else:
            self._send_json(404, {"status": "not found"})

    def log_message(self, format: str, *args: object) -> None:
        log(f"[control] {format % args}")


def start_control_server(window: "LoadingWindow") -> ThreadingHTTPServer:
    ControlRequestHandler.window = window
    server = ThreadingHTTPServer(("127.0.0.1", CONTROL_SERVER_PORT), ControlRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_restart(window: "LoadingWindow") -> None:
    window.root.after(0, window.set_status, "Reiniciando os containers...")
    log("Reiniciando os containers do Lastro (force-recreate)...")
    result = docker_compose_up(force_recreate=True)
    log(f"returncode={result.returncode} stderr={result.stderr}")
    if result.returncode != 0:
        window.root.after(0, window.show_error, "Falha ao reiniciar os containers.")
        return
    window.root.after(0, window.set_status, "Lastro rodando — pode minimizar esta janela.")


def run_startup(window: LoadingWindow) -> None:
    LOG_PATH.write_text("", encoding="utf-8")

    if not docker_engine_is_running():
        log("Docker Desktop não está rodando, iniciando...")
        window.root.after(0, window.set_status, "Iniciando o Docker Desktop...")
        try:
            start_docker_desktop()
        except FileNotFoundError:
            message = "Docker Desktop não encontrado. Instale o Docker Desktop e tente novamente."
            log(message)
            window.root.after(0, window.show_error, message)
            return

        if not wait_for_docker_engine():
            message = "O Docker Desktop não ficou pronto em tempo. Tente abrir manualmente."
            log(message)
            window.root.after(0, window.show_error, message)
            return

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
    window.root.after(0, window.set_status, "Lastro rodando — pode minimizar esta janela.")
    open_in_chrome(WEB_URL)
    window.root.after(0, window.enable_exit_button)


def run_shutdown(window: LoadingWindow) -> None:
    window.root.after(0, window.disable_exit_button)
    window.root.after(0, window.set_status, "Desligando os containers...")
    log("Desligando os containers do Lastro...")
    result = docker_compose_down()
    log(f"returncode={result.returncode} stderr={result.stderr}")
    window.root.after(0, window.close)


def main() -> int:
    window = LoadingWindow()
    window.on_exit_requested = lambda: threading.Thread(
        target=run_shutdown, args=(window,), daemon=True
    ).start()
    start_control_server(window)
    thread = threading.Thread(target=run_startup, args=(window,), daemon=True)
    thread.start()
    window.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
