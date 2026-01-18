# WhiteBot

## Запуск (Windows)

1. Установите Python 3.11+.
2. В папке проекта создайте файл `.env` по примеру `.env.example` и заполните:

- `BOT_TOKEN`
- `ADMIN_ID`

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Запуск:

```bash
python bot.py
```

## Использование

- `/start` — приветствие
- `/submit` — начать отправку mp3
- `/cancel` — отменить

Админ:
- `/feed` или `/feed 20` — последние заявки
- `/get <id>` — открыть заявку по id
