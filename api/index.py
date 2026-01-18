import os
import sys
import traceback
import json
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
    import_success = True
    import_error = None
except Exception as import_e:
    tb = traceback.format_exc()
    import_error = {"type": "import_error", "msg": str(import_e), "traceback": tb}
    import_success = False

def handler(request):
    if not import_success:
        return json.dumps(import_error), {"status": 500, "headers": {"Content-Type": "application/json"}}
    return json.dumps({"status": "ok", "msg": "Bot code imported successfully. Polling not supported on Vercel Serverless — use webhook."}), {"status": 200, "headers": {"Content-Type": "application/json"}}

# Для Vercel Serverless Function
app = handler
