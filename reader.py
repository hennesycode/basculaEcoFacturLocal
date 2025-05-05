# -----------------------------
# File: reader.py
# -----------------------------
import serial
import time
import re

class ScaleReader:
    def __init__(self, ui):
        self.ui = ui
        self.name = None
        self.port = None
        self.serial = None

    def update_scale(self, name, port):
        self.name = name
        self.port = port
        if self.serial and self.serial.is_open:
            self.serial.close()
        try:
            self.serial = serial.Serial(port, baudrate=9600, timeout=1)
            self.ui.log_message(f"Conectado a {port}")
            time.sleep(2)
            self.serial.reset_input_buffer()
        except Exception as e:
            self.ui.log_message(f"Error al conectar: {e}")
            self.serial = None

    def read_weight(self):
        if not self.serial or not self.serial.is_open:
            return None
        try:
            line = self.serial.readline().decode('utf-8', errors='ignore').strip()
            m = re.search(r'(\d+(\.\d+)?)', line)
            if m:
                return float(m.group(1))
        except Exception as e:
            self.ui.log_message(f"Error lectura: {e}")
        return None

    def run(self):
        last_weight = None
        while True:
            if self.name and self.serial:
                # Intentar hasta 5 lecturas
                for _ in range(5):
                    weight = self.read_weight()
                    if weight is not None:
                        if weight != last_weight:
                            self.ui.log_message(f"Báscula {self.name}: {weight} kg")
                            last_weight = weight
                        break
                time.sleep(0.5)
            else:
                time.sleep(1)