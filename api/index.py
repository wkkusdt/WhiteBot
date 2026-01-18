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
        return {"status": "ok"}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Для Vercel Serverless Function
app = handler
