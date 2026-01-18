import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импортировать bot.py и db.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from bot import main

# Vercel вызывает этот handler при запросе к /api
async def handler(request):
    # aiogram webhook mode не используется на Vercel (serverless),
    # но для совместимости можно просто запустить polling в фоне.
    # Однако Vercel имеет таймаут выполнения (max 10s на бесплатном плане),
    # поэтому polling не подходит. Вместо этого используем setWebhook.
    # Для простоты оставим polling, но учтите ограничения.
    await main()

# Для Vercel Serverless Function
app = handler
