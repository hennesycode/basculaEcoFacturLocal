import tkinter as tk
from tkinter import ttk, messagebox
from serial.tools import list_ports
import storage

class ConfigView(ttk.Frame):
    def __init__(self, master, reader):
        super().__init__(master, padding=10)
        self.master = master
        self.reader = reader
        self.scales = []
        self.pack(fill=tk.BOTH, expand=True)
        self._build_ui()
        self._load_cached_scales()

    def _build_ui(self):
        ttk.Label(self, text="Básculas EcoFactur Local", font=("Helvetica", 16, "bold")).pack(pady=5)
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=15).pack(side=tk.LEFT)
        ttk.Label(frame, text="Puerto COM:").pack(side=tk.LEFT, padx=(15,5))
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(frame, textvariable=self.port_var,
                                     values=self._get_com_ports(), width=12, state="readonly")
        self.port_cb.pack(side=tk.LEFT)
        ttk.Button(frame, text="Refrescar", command=self._refresh_ports).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Agregar", command=self._add_scale).pack(side=tk.LEFT)

        cols = ("Puerto", "Peso (kg)")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log = tk.Text(self, height=6, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, pady=(0,10))

    def _get_com_ports(self):
        return [p.device for p in list_ports.comports()]

    def _refresh_ports(self):
        self.port_cb['values'] = self._get_com_ports()

    def _add_scale(self):
        name = self.name_var.get().strip()
        port = self.port_var.get().strip()
        if not name or not port:
            messagebox.showerror("Error", "Debe indicar nombre y puerto COM")
            return
        self.scales.append({"name": name, "port": port})
        storage.save_scales(self.scales)
        self.reader.register_scale(name, port)
        self.tree.insert("", tk.END, iid=name, values=(port, "--"))
        self._log(f"Báscula '{name}' agregada en {port}")

    def _load_cached_scales(self):
        saved = storage.load_scales()
        for s in saved:
            self.scales.append(s)
            self.tree.insert("", tk.END, iid=s['name'], values=(s['port'], "--"))
            self.reader.register_scale(s['name'], s['port'])

    def update_weight(self, name, weight):
        if self.tree.exists(name):
            self.tree.set(name, "Peso (kg)", f"{weight:.2f}")
            self._log(f"{name}: {weight:.2f} kg")

    def _log(self, msg):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def log_message(self, msg):
        """Alias público para registrar mensajes de log"""
        self._log(msg)