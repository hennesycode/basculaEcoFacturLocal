# -----------------------------
# File: main.py
# -----------------------------
import threading
import tkinter as tk
from ui import ConfigView
from reader import ScaleReader


def main():
    root = tk.Tk()
    root.title("Báscula EcoFactur Local")
    root.geometry("500x400")
    # Tema ttk moderno con sv_ttk
    try:
        import sv_ttk
        sv_ttk.set_theme("dark")  # o "light"
    except ImportError:
        pass

    # Vista de configuración
    app = ConfigView(root)

    # Lector de báscula en segundo plano
    reader = ScaleReader(app)
    reader_thread = threading.Thread(target=reader.run, daemon=True)
    reader_thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()