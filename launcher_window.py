from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

from src.runner import open_browser, resolve_base_dir, resolve_port, start_streamlit_thread, wait_and_notify


class DashboardLauncherWindow:
    def __init__(self, port: int) -> None:
        self.port = port
        self.root = tk.Tk()
        self.root.title("World Cup Action Flow")
        self.root.geometry("440x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#101826")

        self.status_var = tk.StringVar(value="Preparando inicializacao...")
        self.url_var = tk.StringVar(value=f"http://127.0.0.1:{port}")
        self.is_ready = False

        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, bg="#101826", padx=20, pady=18)
        frame.pack(fill="both", expand=True)

        title = tk.Label(
            frame,
            text="World Cup Action Flow",
            fg="#f5f7fb",
            bg="#101826",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            frame,
            text="Launcher do dashboard. O navegador sera aberto quando o servidor estiver pronto.",
            fg="#9db1c7",
            bg="#101826",
            justify="left",
            wraplength=390,
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(6, 18))

        status = tk.Label(
            frame,
            textvariable=self.status_var,
            fg="#ffb703",
            bg="#101826",
            font=("Segoe UI", 11, "bold"),
        )
        status.pack(anchor="w", pady=(0, 10))

        url = tk.Label(
            frame,
            textvariable=self.url_var,
            fg="#38bdf8",
            bg="#101826",
            font=("Consolas", 10),
        )
        url.pack(anchor="w", pady=(0, 18))

        buttons = tk.Frame(frame, bg="#101826")
        buttons.pack(anchor="w")

        self.open_button = tk.Button(
            buttons,
            text="Abrir navegador",
            command=self.open_browser,
            state="disabled",
            bg="#ff6b1a",
            fg="white",
            activebackground="#ff8c42",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.open_button.pack(side="left", padx=(0, 10))

        close_button = tk.Button(
            buttons,
            text="Fechar janela",
            command=self.root.destroy,
            bg="#1f2937",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
        )
        close_button.pack(side="left")

    def set_status(self, message: str) -> None:
        self.root.after(0, lambda: self.status_var.set(message))

    def mark_ready(self) -> None:
        def _apply() -> None:
            self.is_ready = True
            self.status_var.set("Servidor pronto. Clique em abrir navegador.")
            self.open_button.configure(state="normal")
            self.open_browser()

        self.root.after(0, _apply)

    def mark_failure(self) -> None:
        def _apply() -> None:
            self.status_var.set("Falha ao iniciar o dashboard.")
            messagebox.showerror(
                "Falha ao iniciar",
                "Nao foi possivel iniciar o servidor local do dashboard.",
            )

        self.root.after(0, _apply)

    def open_browser(self) -> None:
        open_browser(self.port)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    base_dir = resolve_base_dir()
    port = resolve_port()
    app = DashboardLauncherWindow(port)

    start_streamlit_thread(base_dir, port)

    watcher = threading.Thread(
        target=wait_and_notify,
        args=(port, app.set_status, app.mark_ready, app.mark_failure),
        daemon=True,
    )
    watcher.start()
    app.run()


if __name__ == "__main__":
    main()
