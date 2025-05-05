# -----------------------------
# File: README.md
# -----------------------------
# basculaEcoFacturLocal

## Requisitos

- Python 3.x
- pyserial

Instalación:
```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Generar .exe

1. Instalar PyInstaller:
```bash
pip install pyinstaller
```
2. Empaquetar:
```bash
pyinstaller --onefile --windowed main.py
```

El ejecutable se generará en la carpeta `dist/`.
