import serial
import time
import re
from threading import Lock

class ScaleReader:
    def __init__(self, ui=None):
        self.ui = ui
        # cada elemento: {name, port, baudrate, serial, last_reported_weight, pending_weight, pending_count, last_reconnect}
        self.scales = []
        self.lock = Lock()

    def register_scale(self, name, port, baudrate=9600):
        if any(s['name'] == name and s['port'] == port for s in self.scales):
            return
        scale = {
            'name': name,
            'port': port,
            'baudrate': baudrate,
            'serial': None,
            'last_reported_weight': None,
            'pending_weight': None,
            'pending_count': 0,
            'last_reconnect': 0
        }
        self.scales.append(scale)
        if self.ui:
            self.ui.log_message(f"[Info] Registrando '{name}' en {port} @ {baudrate}bps")
        self._connect(scale)

    def _connect(self, scale):
        try:
            ser = serial.Serial(
                port=scale['port'],
                baudrate=scale['baudrate'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0
            )
            time.sleep(0.05)
            try:
                ser.reset_input_buffer()
            except Exception as e:
                if self.ui:
                    self.ui.log_message(f"[Advertencia buffer {scale['name']}]: {e}")
            scale['serial'] = ser
            scale['last_reconnect'] = time.time()
            if self.ui:
                self.ui.log_message(f"[Conectada] '{scale['name']}' en {scale['port']}")
        except Exception as e:
            scale['serial'] = None
            scale['last_reconnect'] = time.time()
            if self.ui:
                self.ui.log_message(f"[Error conectar {scale['name']}]: {e}")

    def run(self):
        RECONNECT_INTERVAL = 5      # segundos para reintentar reconexión
        STABLE_THRESHOLD = 3        # lecturas iguales necesarias
        while True:
            with self.lock:
                copy = list(self.scales)
            for s in copy:
                ser = s['serial']
                # auto-reconexión
                if not ser or not ser.is_open:
                    if time.time() - s['last_reconnect'] > RECONNECT_INTERVAL:
                        self._connect(s)
                    continue

                try:
                    n = ser.in_waiting
                    if n:
                        data = ser.read(n).decode('utf-8', errors='ignore')
                        m = re.search(r'(\d+(?:\.\d+)?)', data)
                        if m:
                            w = float(m.group(1))
                            # si coincide con la última pendiente, incrementar contador
                            if s['pending_weight'] == w:
                                s['pending_count'] += 1
                            else:
                                s['pending_weight'] = w
                                s['pending_count'] = 1
                            # sólo confirmamos y mostramos tras STABLE_THRESHOLD lecturas
                            if s['pending_count'] >= STABLE_THRESHOLD and s['last_reported_weight'] != w:
                                s['last_reported_weight'] = w
                                if self.ui:
                                    self.ui.update_weight(s['name'], w)
                except (serial.SerialException, OSError) as e:
                    if self.ui:
                        self.ui.log_message(f"[Desconectada {s['name']}]: {e}")
                    try: ser.close()
                    except: pass
                    s['serial'] = None
                    s['last_reconnect'] = time.time()
                except Exception as e:
                    if self.ui:
                        self.ui.log_message(f"[Error lectura {s['name']}]: {e}")

                time.sleep(0.005)
            time.sleep(0.001)
