import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from bot import main
except Exception as import_e:
    # Если не удалось импортировать, вернём ошибку сразу
    def handler(request):
        tb = traceback.format_exc()
        return f"IMPORT ERROR: {import_e}\n\nTRACEBACK:\n{tb}", 500
else:
    # Если импорт прошел, обернём main
    async def handler(request):
        try:
            await main()
            return "OK"
        except Exception as e:
            tb = traceback.format_exc()
            return f"ERROR: {e}\n\nTRACEBACK:\n{tb}", 500

# Для Vercel Serverless Function
app = handler
