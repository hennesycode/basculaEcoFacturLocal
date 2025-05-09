# main.py
import tkinter as tk
import threading
from ui import ConfigView
from reader import ScaleReader

def main():
    root = tk.Tk()
    root.title("Básculas EcoFactur Local")
    root.geometry("600x550")
    try:
        import sv_ttk
        sv_ttk.set_theme("dark")
    except ImportError:
        pass

    reader = ScaleReader()
    app = ConfigView(root, reader)
    reader.ui = app

    # Arranca el hilo de lectura de básculas
    thr = threading.Thread(target=reader.run, daemon=True)
    thr.start()

    root.mainloop()

if __name__ == "__main__":
    main()
