import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
    import_success = True
    import_error = None
except Exception as import_e:
    tb = traceback.format_exc()
    import_error = f"IMPORT ERROR: {import_e}\n\nTRACEBACK:\n{tb}"
    import_success = False

def handler(request):
    if not import_success:
        return import_error, 500
    return "Bot code imported successfully. Polling not supported on Vercel Serverless — use webhook.", 200

# Для Vercel Serverless Function
app = handler
