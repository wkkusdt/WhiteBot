# Деплой WhiteBot на Vercel (Serverless)

> ⚠️ Важно: Vercel Serverless Functions имеют лимит времени выполнения (10 с на бесплатном плане).  
> Для Telegram-бота с polling это не подходит. Рекомендуемый способ — **setWebhook**.  
> Ниже приведён минимальный вариант с polling для демонстрации, но для продакшена лучше настроить webhook.

---

## 1. Подготовка локально

1. **Убедитесь, что проект работает локально**:
   ```bash
   python bot.py
   ```

2. **Добавьте `.env` в `.gitignore`** (уже добавлен).  
   Не коммитьте `.env` с токеном!

3. **Залейте проект на GitHub**:
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/yourusername/WhiteBot.git
   git push -u origin main
   ```

---

## 2. Настройка Vercel

1. **Зарегистрируйтесь на [Vercel](https://vercel.com)** через GitHub.

2. **Import Project** → выберите репозиторий `WhiteBot`.

3. **Framework Preset**: `Other`.

4. **Root Directory**: оставьте корневой.

5. **Build & Development Settings**:
   - **Build Command**: оставьте пустым
   - **Output Directory**: оставьте пустым
   - **Install Command**: `pip install -r requirements.txt`

6. **Environment Variables** (в настройках проекта Vercel):
   - `BOT_TOKEN` → ваш токен от @BotFather
   - `ADMIN_ID` → ваш Telegram user id

7. **Deploy**.

---

## 3. Webhook (рекомендуется для продакшена)

Чтобы бот работал на Vercel стабильно, лучше использовать **webhook** вместо polling.

### Шаги

1. **Добавьте в проект `api/webhook.py`** (см. ниже).

2. **Установите webhook после первого деплоя**:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.vercel.app/api/webhook"
   ```

3. **В `vercel.json` замените маршрут** на `/api/webhook`.

---

## 4. Пример `api/webhook.py` (webhook-режим)

```python
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from bot import bot, dp, db
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web

# Включите webhook в bot.py (уберите polling)
async def on_startup():
    webhook_url = os.getenv("VERCEL_URL") + "/api/webhook"
    await bot.set_webhook(webhook_url)

async def on_shutdown():
    await bot.session.close()

async def handle_webhook(request):
    update_data = await request.json()
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(update=update)
    return web.Response(status=200)

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/api/webhook")
setup_application(app, dp, bot=bot)
```

---

## 5. Проверка

- После деплоя откройте `https://your-project.vercel.app/api` — должен ответить (или 404, если настроен webhook).
- Отправьте боту `/start`.
- Проверьте логи в Vercel Dashboard → Functions.

---

## 6. Ограничения Vercel

- **Время выполнения**: 10 с (бесплатно), 60 с (Pro).
- **Хранение**: нет постоянного файлового хранилища между вызовами (кроме `/tmp`). SQLite в `data/` не будет сохраняться между запросами.  
  Решение: используйте внешнюю БД (Supabase, PlanetScale, PostgreSQL) или Vercel KV.

---

## 7. Альтернативы

Если вам нужен **долгоживущий бот** с polling и локальной SQLite:
- **Render** (free tier, background worker)
- **Railway**
- **DigitalOcean App Platform**
- **VPS** (любой)

---

## 8. Краткий итог

- Для **демо/прототипа** — можно задеплоить на Vercel с polling (но будет работать нестабильно).
- Для **продакшена** — используйте webhook + внешнюю БД или выберите другой хостинг (Render/Railway/VPS).

---

### Готово к деплою?

- Залейте на GitHub.
- Импортируйте в Vercel.
- Добавьте `BOT_TOKEN` и `ADMIN_ID` в Environment Variables.
- Deploy.

Если хотите — я помогу настроить webhook и перейти на внешнюю БД.
