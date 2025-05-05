import serial
import time
import re
from threading import Lock

class ScaleReader:
    def __init__(self, ui=None):
        self.ui = ui
        self.scales = []  # cada elemento: {name, port, serial, last_weight}
        self.lock = Lock()

    def register_scale(self, name, port):
        if any(s['name']==name and s['port']==port for s in self.scales):
            return
        try:
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            time.sleep(2)
            ser.reset_input_buffer()
        except Exception as e:
            if self.ui:
                self.ui.log_message(f"[Error conectar {name}@{port}]: {e}")
            return
        with self.lock:
            self.scales.append({'name': name, 'port': port, 'serial': ser, 'last_weight': None})
        if self.ui:
            self.ui.log_message(f"Registrada báscula '{name}' en {port}")

    def run(self):
        while True:
            with self.lock:
                copy_scales = list(self.scales)
            for s in copy_scales:
                try:
                    line = s['serial'].readline().decode('utf-8', errors='ignore').strip()
                    m = re.search(r'(\d+(\.\d+)?)', line)
                    if m:
                        w = float(m.group(1))
                        if s['last_weight'] != w:
                            s['last_weight'] = w
                            if self.ui:
                                self.ui.update_weight(s['name'], w)
                except Exception as e:
                    if self.ui:
                        self.ui.log_message(f"[Error lectura {s['name']}]: {e}")
                time.sleep(0.1)
            time.sleep(0.4)