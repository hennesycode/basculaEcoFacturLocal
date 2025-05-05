# -----------------------------
# File: ui.py
# -----------------------------
import tkinter as tk
from tkinter import ttk, messagebox
from serial.tools import list_ports

class ConfigView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.scale_name_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.reader = None
        self.create_widgets()

    def create_widgets(self):
        # Título
        title = ttk.Label(self, text="Configuración de Báscula", font=("Helvetica", 16, "bold"))
        title.pack(pady=10)

        # Nombre de la báscula
        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Nombre de la Báscula:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(name_frame, textvariable=self.scale_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Selección de puerto COM
        port_frame = ttk.Frame(self)
        port_frame.pack(fill=tk.X, pady=5)
        ttk.Label(port_frame, text="Puerto COM:").pack(side=tk.LEFT, padx=(0,5))
        self.combobox = ttk.Combobox(port_frame, textvariable=self.port_var,
                                     values=self.get_com_ports(), state="readonly")
        self.combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        refresh_btn = ttk.Button(port_frame, text="Refrescar", command=self.refresh_ports)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Botón Agregar
        add_btn = ttk.Button(self, text="Agregar Báscula", command=self.add_scale)
        add_btn.pack(pady=10)

        # Área de log
        self.log = tk.Text(self, height=10, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, pady=5)

    def get_com_ports(self):
        ports = list_ports.comports()
        return [p.device for p in ports]

    def refresh_ports(self):
        self.combobox['values'] = self.get_com_ports()

    def add_scale(self):
        name = self.scale_name_var.get().strip()
        port = self.port_var.get()
        if not name or not port:
            messagebox.showerror("Error", "Debe ingresar nombre y seleccionar puerto.")
            return
        # Inicializar o actualizar el lector
        from reader import ScaleReader
        if not self.reader:
            self.reader = ScaleReader(self)
        self.reader.update_scale(name, port)
        self.log_message(f"Báscula '{name}' agregada en {port}")

    def log_message(self, msg):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)
