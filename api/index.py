import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
    print("IMPORT SUCCESS")
except Exception as import_e:
    tb = traceback.format_exc()
    print(f"IMPORT ERROR: {import_e}\n\nTRACEBACK:\n{tb}")
    def handler(request):
        return "IMPORT FAILED (see logs)", 500
else:
    async def handler(request):
        try:
            print("CALLING MAIN")
            await main()
            return "OK"
        except Exception as e:
            tb = traceback.format_exc()
            print(f"RUNTIME ERROR: {e}\n\nTRACEBACK:\n{tb}")
            return "RUNTIME FAILED (see logs)", 500

# Для Vercel Serverless Function
app = handler
