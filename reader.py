import serial
import time
import re
from threading import Lock

class ScaleReader:
    def __init__(self, ui=None):
        self.ui = ui
        self.scales = []  # cada elemento: {name, port, serial, last_weight}
        self.lock = Lock()

    def register_scale(self, name, port, baudrate=9600):
        # Evitar duplicados
        if any(s['name']==name and s['port']==port for s in self.scales):
            return
        try:
            # timeout=0 para no bloquear
            ser = serial.Serial(port, baudrate=baudrate, timeout=0)
            time.sleep(0.1)
            try:
                ser.reset_input_buffer()
            except (serial.SerialException, OSError) as e:
                if self.ui:
                    self.ui.log_message(f"[Advertencia buffer {name}@{port}]: {e}")
        except Exception as e:
            if self.ui:
                self.ui.log_message(f"[Error al conectar {name}@{port}]: {e}")
            return

        with self.lock:
            self.scales.append({
                'name': name,
                'port': port,
                'serial': ser,
                'last_weight': None
            })
        if self.ui:
            self.ui.log_message(f"Registrada báscula '{name}' en {port} @ {baudrate}bps")

    def run(self):
        while True:
            with self.lock:
                copy_scales = list(self.scales)
            for s in copy_scales:
                ser = s['serial']
                try:
                    n = ser.in_waiting
                    if n:
                        data = ser.read(n).decode('utf-8', errors='ignore')
                        m = re.search(r'(\d+(\.\d+)?)', data)
                        if m:
                            w = float(m.group(1))
                            if s['last_weight'] != w:
                                s['last_weight'] = w
                                if self.ui:
                                    self.ui.update_weight(s['name'], w)
                except (serial.SerialException, OSError) as e:
                    if self.ui:
                        self.ui.log_message(f"[Advertencia lectura {s['name']}]: {e}")
                except Exception as e:
                    if self.ui:
                        self.ui.log_message(f"[Error inesperado {s['name']}]: {e}")
                # pausa mínima para no saturar CPU
                time.sleep(0.005)
            time.sleep(0.001)
