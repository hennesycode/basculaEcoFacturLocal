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
        # — Título —
        ttk.Label(self, text="Básculas EcoFactur Local",
                  font=("Helvetica", 16, "bold")).pack(pady=5)

        # — Panel de configuración —
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Nombre:").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=15).pack(side=tk.LEFT)

        ttk.Label(frame, text="Puerto COM:").pack(side=tk.LEFT, padx=(15,5))
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(
            frame,
            textvariable=self.port_var,
            values=self._get_com_ports(),
            width=12,
            state="readonly"
        )
        self.port_cb.pack(side=tk.LEFT)
        # Refresca al abrir el desplegable
        self.port_cb.bind("<Button-1>", lambda e: self._refresh_ports())

        ttk.Label(frame, text="Baudrate:").pack(side=tk.LEFT, padx=(15,5))
        self.baud_var = tk.StringVar(value="9600")
        ttk.Combobox(
            frame,
            textvariable=self.baud_var,
            values=["9600","19200","38400","57600","115200"],
            width=8,
            state="readonly"
        ).pack(side=tk.LEFT)

        ttk.Button(frame, text="Refrescar", command=self._refresh_ports).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Agregar",  command=self._add_scale).pack(side=tk.LEFT)

        # — Treeview de básculas y su peso —
        cols = ("Puerto", "Peso (kg)")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # — Log de mensajes —
        self.log = tk.Text(self, height=6, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH)

    def _get_com_ports(self):
        return [p.device for p in list_ports.comports()]

    def _refresh_ports(self):
        ports = self._get_com_ports()
        self.port_cb['values'] = ports

    def _add_scale(self):
        name = self.name_var.get().strip()
        port = self.port_var.get().strip()
        baud = int(self.baud_var.get())
        if not name or not port:
            messagebox.showerror("Error", "Debe indicar nombre y puerto COM")
            return

        # Guarda en caché
        self.scales.append({"name": name, "port": port, "baud": baud})
        storage.save_scales(self.scales)

        # Registra en el lector
        self.reader.register_scale(name, port, baud)

        # Inserta en la tabla
        self.tree.insert("", tk.END, iid=name, values=(port, "--"))
        self.log_message(f"Báscula '{name}' agregada en {port} @ {baud}bps")

        # Limpia campos
        self.name_var.set("")
        self.port_var.set("")

    def _load_cached_scales(self):
        saved = storage.load_scales()
        for s in saved:
            name, port, baud = s['name'], s['port'], s.get('baud',9600)
            self.scales.append({"name": name, "port": port, "baud": baud})
            self.tree.insert("", tk.END, iid=name, values=(port, "--"))
            self.reader.register_scale(name, port, baud)

    def update_weight(self, name, weight):
        """Recibe una lectura estable y actualiza SOLO esa fila."""
        text = f"{weight:.2f}"
        if self.tree.exists(name):
            self.tree.set(name, "Peso (kg)", text)
        self.log_message(f"{name}: {text} kg")

    def log_message(self, msg):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)
