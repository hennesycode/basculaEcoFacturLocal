import json
import os

CACHE_FILE = 'scales.json'

def load_scales():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_scales(scales):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(scales, f, indent=2, ensure_ascii=False)
