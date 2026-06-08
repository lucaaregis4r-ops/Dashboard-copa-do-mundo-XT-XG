from __future__ import annotations

from src.runner import open_browser, resolve_base_dir, resolve_port, start_streamlit_thread, wait_and_notify


def main() -> None:
    base_dir = resolve_base_dir()
    port = resolve_port()

    print("World Cup Action Flow")
    print(f"Base do app: {base_dir}")
    print(f"Porta local: {port}")
    print("Iniciando dashboard...")

    streamlit_thread = start_streamlit_thread(base_dir, port)
    is_ready = wait_and_notify(port, on_status=print, on_ready=lambda: open_browser(port))

    if not is_ready:
        print("Falha ao subir o dashboard. Feche esta janela e tente novamente.")
        streamlit_thread.join(timeout=2)
        input("Pressione Enter para sair...")
        return

    print("Dashboard em execucao. Feche esta janela para encerrar.")
    streamlit_thread.join()


if __name__ == "__main__":
    main()
