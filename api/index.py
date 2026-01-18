import os
import sys
import traceback
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from bot import main

# Vercel вызывает этот handler при запросе к /api
async def handler(request):
    try:
        await main()
        return "OK"
    except Exception as e:
        tb = traceback.format_exc()
        return f"ERROR: {e}\n\nTRACEBACK:\n{tb}", 500

# Для Vercel Serverless Function
app = handler
