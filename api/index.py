import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
except Exception as import_e:
    tb = traceback.format_exc()
    raise Exception(f"IMPORT ERROR: {import_e}\n\nTRACEBACK:\n{tb}")

def handler(request):
    raise Exception("Vercel Serverless does not support long polling. Use webhook instead of polling.")

# Для Vercel Serverless Function
app = handler
