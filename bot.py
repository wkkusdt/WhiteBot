from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

from db import SubmissionsDb


class SubmitFlow(StatesGroup):
    waiting_mp3 = State()
    waiting_nickname = State()
    waiting_genre = State()
    waiting_comment = State()
    waiting_confirm = State()


@dataclass
class PendingSubmission:
    file_id: str
    file_unique_id: str
    file_kind: str
    nickname: Optional[str] = None
    genre: Optional[str] = None
    comment: Optional[str] = None


def _kbd_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
            ]
        ]
    )


def _kbd_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🎵 Отправить заявку", callback_data="start_submit")]]
    )


def _is_mp3_document(message: Message) -> bool:
    if not message.document:
        return False
    mime = (message.document.mime_type or "").lower()
    if mime == "audio/mpeg":
        return True
    name = (message.document.file_name or "").lower()
    return name.endswith(".mp3")


def _extract_file(message: Message) -> Optional[PendingSubmission]:
    if message.audio:
        return PendingSubmission(
            file_id=message.audio.file_id,
            file_unique_id=message.audio.file_unique_id,
            file_kind="audio",
        )
    if _is_mp3_document(message):
        return PendingSubmission(
            file_id=message.document.file_id,
            file_unique_id=message.document.file_unique_id,
            file_kind="document",
        )
    return None


def _preview_text(p: PendingSubmission, *, from_user: Message) -> str:
    username = f"@{from_user.from_user.username}" if from_user.from_user and from_user.from_user.username else "(нет)"
    full_name = from_user.from_user.full_name if from_user.from_user else "(unknown)"
    user_id = from_user.from_user.id if from_user.from_user else 0

    return (
        "Проверьте данные перед отправкой:\n\n"
        f"Ник: {p.nickname}\n"
        f"Жанр: {p.genre}\n"
        f"Комментарий: {p.comment}\n\n"
        f"От кого: {full_name} {username} (id {user_id})"
    )


def _admin_caption(submission_id: int, p: PendingSubmission, msg: Message) -> str:
    username = f"@{msg.from_user.username}" if msg.from_user and msg.from_user.username else "(нет)"
    full_name = msg.from_user.full_name if msg.from_user else "(unknown)"
    user_id = msg.from_user.id if msg.from_user else 0
    return (
        f"Заявка #{submission_id}\n"
        f"Ник: {p.nickname}\n"
        f"Жанр: {p.genre}\n"
        f"Комментарий: {p.comment}\n"
        f"От кого: {full_name} {username} (id {user_id})"
    )


async def main() -> None:
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    port = int(os.getenv("PORT", "8080"))
    
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not admin_id_raw:
        raise RuntimeError("ADMIN_ID is not set")

    admin_id = int(admin_id_raw)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    db = SubmissionsDb(Path(__file__).with_name("data").joinpath("submissions.sqlite3"))

    async def require_admin(message: Message) -> bool:
        return bool(message.from_user and message.from_user.id == admin_id)

    @dp.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "👋 Привет! Отправь mp3, а я передам его админу с твоим ником, жанром и комментарием.",
            reply_markup=_kbd_start(),
        )

    @dp.callback_query(F.data == "start_submit")
    async def cb_start_submit(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(SubmitFlow.waiting_mp3)
        await cb.message.answer("🎶 Пришлите mp3 (Audio или Document).")
        await cb.answer()

    @dp.message(Command("submit"))
    async def cmd_submit(message: Message, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(SubmitFlow.waiting_mp3)
        await message.answer("🎶 Пришлите mp3 (Audio или Document).")

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=_kbd_start())

    @dp.callback_query(F.data == "cancel")
    async def cb_cancel(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await cb.message.answer("❌ Отменено.", reply_markup=_kbd_start())
        await cb.answer()

    @dp.message(SubmitFlow.waiting_mp3)
    async def on_mp3(message: Message, state: FSMContext) -> None:
        extracted = _extract_file(message)
        if extracted is None:
            await message.answer("🚫 Нужен mp3. Пришлите как аудио или как файл .mp3")
            return

        await state.update_data(pending=extracted.__dict__)
        await state.set_state(SubmitFlow.waiting_nickname)
        await message.answer("👤 Укажите ник.")

    @dp.message(SubmitFlow.waiting_nickname)
    async def on_nickname(message: Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if not text:
            await message.answer("🚫 Ник не должен быть пустым. Напишите ник.")
            return
        data = await state.get_data()
        p = PendingSubmission(**data["pending"])
        p.nickname = text
        await state.update_data(pending=p.__dict__)
        await state.set_state(SubmitFlow.waiting_genre)
        await message.answer("🎸 Укажите жанр.")

    @dp.message(SubmitFlow.waiting_genre)
    async def on_genre(message: Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if not text:
            await message.answer("🚫 Жанр не должен быть пустым. Напишите жанр.")
            return
        data = await state.get_data()
        p = PendingSubmission(**data["pending"])
        p.genre = text
        await state.update_data(pending=p.__dict__)
        await state.set_state(SubmitFlow.waiting_comment)
        await message.answer("💬 Добавьте комментарий (можно коротко).")

    @dp.message(SubmitFlow.waiting_comment)
    async def on_comment(message: Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        if not text:
            await message.answer("🚫 Комментарий не должен быть пустым. Напишите комментарий.")
            return
        data = await state.get_data()
        p = PendingSubmission(**data["pending"])
        p.comment = text
        await state.update_data(pending=p.__dict__)
        await state.set_state(SubmitFlow.waiting_confirm)
        await message.answer(_preview_text(p, from_user=message), reply_markup=_kbd_confirm())

    @dp.callback_query(SubmitFlow.waiting_confirm, F.data == "confirm")
    async def cb_confirm(cb: CallbackQuery, state: FSMContext) -> None:
        if cb.message is None or cb.from_user is None:
            await cb.answer()
            return

        data = await state.get_data()
        p = PendingSubmission(**data["pending"])
        if not (p.nickname and p.genre and p.comment):
            await cb.message.answer("🚫 Не хватает данных. Начните заново /submit", reply_markup=_kbd_start())
            await state.clear()
            await cb.answer()
            return

        submission_id = db.add(
            from_user_id=cb.from_user.id,
            from_username=cb.from_user.username,
            from_full_name=cb.from_user.full_name,
            file_id=p.file_id,
            file_unique_id=p.file_unique_id,
            file_kind=p.file_kind,
            nickname=p.nickname,
            genre=p.genre,
            comment=p.comment,
        )

        caption = _admin_caption(submission_id, p, cb.message)

        try:
            if p.file_kind == "audio":
                await bot.send_audio(chat_id=admin_id, audio=p.file_id, caption=caption)
            else:
                await bot.send_document(chat_id=admin_id, document=p.file_id, caption=caption)
        except Exception as e:
            await cb.message.answer(f"⚠️ Ошибка при отправке админу: {e}", reply_markup=_kbd_start())
            await state.clear()
            await cb.answer()
            return

        await cb.message.answer("✅ Отправлено админу. Спасибо!", reply_markup=_kbd_start())
        await state.clear()
        await cb.answer()

    @dp.message(Command("feed"))
    async def cmd_feed(message: Message, command: CommandObject) -> None:
        if not await require_admin(message):
            return
        limit = 10
        if command.args:
            try:
                limit = max(1, min(50, int(command.args.strip())))
            except ValueError:
                limit = 10

        items = db.list_latest(limit)
        if not items:
            await message.answer("📭 Лента пустая.")
            return

        lines = [f"📋 Последние {len(items)} заявок:"]
        for s in items:
            who = f"@{s.from_username}" if s.from_username else s.from_full_name
            lines.append(f"#{s.id} | {s.nickname} | {s.genre} | {who}")
        lines.append("\nКоманда: /get <id>")
        await message.answer("\n".join(lines))

    @dp.message(Command("get"))
    async def cmd_get(message: Message, command: CommandObject) -> None:
        if not await require_admin(message):
            return
        if not command.args:
            await message.answer("🚫 Использование: /get <id>")
            return
        try:
            submission_id = int(command.args.strip())
        except ValueError:
            await message.answer("🚫 id должен быть числом")
            return

        s = db.get(submission_id)
        if s is None:
            await message.answer("🚫 Не найдено")
            return

        who = f"@{s.from_username}" if s.from_username else s.from_full_name
        caption = (
            f"Заявка #{s.id}\n"
            f"Ник: {s.nickname}\n"
            f"Жанр: {s.genre}\n"
            f"Комментарий: {s.comment}\n"
            f"От кого: {who} (id {s.from_user_id})"
        )

        if s.file_kind == "audio":
            await bot.send_audio(chat_id=message.chat.id, audio=s.file_id, caption=caption)
        else:
            await bot.send_document(chat_id=message.chat.id, document=s.file_id, caption=caption)

    # Webhook or polling mode
    if webhook_url:
        # Webhook mode for deployment
        app = web.Application()
        
        # Register webhook handler
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        
        # Set webhook
        await bot.set_webhook(webhook_url)
        
        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"Webhook server started on port {port}")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour intervals
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
            await bot.session.close()
    else:
        # Local polling mode
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
