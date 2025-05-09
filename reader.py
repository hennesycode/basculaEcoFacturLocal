# reader.py
import serial
import time
import re
import requests
from threading import Lock

# URL base de tu API Django
API_BASE = 'https://heroesdelplaneta-ecofactur.hennesy.pro/servicios/api'

class ScaleReader:
    def __init__(self, ui=None):
        self.ui = ui
        # Cada elemento contendrá:
        # { name, port, baudrate, serial, id, last_reported_weight,
        #   pending_weight, pending_count, last_reconnect }
        self.scales = []
        self.lock = Lock()

    def register_scale(self, name, port, baudrate=9600):
        # Evita duplicados locales
        if any(s['name']==name and s['port']==port for s in self.scales):
            return

        scale = {
            'name': name,
            'port': port,
            'baudrate': baudrate,
            'serial': None,
            'id': None,
            'last_reported_weight': None,
            'pending_weight': None,
            'pending_count': 0,
            'last_reconnect': time.time()
        }
        self.scales.append(scale)
        if self.ui:
            self.ui.log_message(f"[Info] Registrando '{name}' en {port} @ {baudrate}bps")

        # 1) Conexión física
        self._connect(scale)

        # 2) Registrar en Django (efímero)
        try:
            resp = requests.post(
                f"{API_BASE}/discover-scale/",
                json={'nombre': name, 'puerto': port, 'baudrate': baudrate},
                timeout=1
            )
            resp.raise_for_status()
            data = resp.json()
            scale['id'] = data['id']
            if self.ui:
                self.ui.log_message(f"[API] ID {scale['id']} para '{name}'")
        except Exception as e:
            if self.ui:
                self.ui.log_message(f"[API Error] discover-scale: {e}")

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
            except:
                pass
            scale['serial'] = ser
            scale['last_reconnect'] = time.time()
            if self.ui:
                self.ui.log_message(f"[Conectada] '{scale['name']}'")
        except Exception as e:
            scale['serial'] = None
            scale['last_reconnect'] = time.time()
            if self.ui:
                self.ui.log_message(f"[Error conectar {scale['name']}]: {e}")

    def run(self):
        RECONNECT_INTERVAL = 5
        STABLE_THRESHOLD    = 3

        while True:
            with self.lock:
                copy = list(self.scales)
            for s in copy:
                ser = s['serial']

                # Reconectar si se cayó
                if not ser or not ser.is_open:
                    if time.time() - (s['last_reconnect'] or 0) > RECONNECT_INTERVAL:
                        self._connect(s)
                    continue

                try:
                    n = ser.in_waiting
                    if n:
                        data = ser.read(n).decode('utf-8', errors='ignore')
                        m = re.search(r'(\d+(?:\.\d+)?)', data)
                        if m:
                            w = float(m.group(1))

                            # Lectura estable
                            if s['pending_weight'] == w:
                                s['pending_count'] += 1
                            else:
                                s['pending_weight'] = w
                                s['pending_count'] = 1

                            if s['pending_count'] >= STABLE_THRESHOLD and s['last_reported_weight'] != w:
                                s['last_reported_weight'] = w

                                # 3) Actualizar UI
                                if self.ui:
                                    self.ui.update_weight(s['name'], w)

                                # 4) Enviar al backend
                                if s.get('id') is not None:
                                    try:
                                        requests.post(
                                            f"{API_BASE}/update-weight/",
                                            json={'scale': s['id'], 'weight': w},
                                            timeout=1
                                        )
                                    except Exception as e:
                                        if self.ui:
                                            self.ui.log_message(f"[API Error lectura]: {e}")

                except (serial.SerialException, OSError) as e:
                    if self.ui:
                        self.ui.log_message(f"[Desconectada {s['name']}]: {e}")
                    try:
                        ser.close()
                    except:
                        pass
                    s['serial'] = None
                    s['last_reconnect'] = time.time()

                except Exception as e:
                    if self.ui:
                        self.ui.log_message(f"[Error lectura {s['name']}]: {e}")

                time.sleep(0.005)
            time.sleep(0.001)
