import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
    import_success = True
except Exception as import_e:
    tb = traceback.format_exc()
    import_error = f"IMPORT ERROR: {import_e}\n\nTRACEBACK:\n{tb}"
    import_success = False

def handler(request):
    if not import_success:
        return import_error, 500
    try:
        # Vercel Serverless не поддерживает long polling, но для диагностики попробуем запустить
        import asyncio
        asyncio.run(main())
        return "OK"
    except Exception as e:
        tb = traceback.format_exc()
        return f"RUNTIME ERROR: {e}\n\nTRACEBACK:\n{tb}", 500

# Для Vercel Serverless Function
app = handler
