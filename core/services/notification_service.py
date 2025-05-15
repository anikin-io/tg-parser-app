import asyncio
import os
from datetime import timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardRemove


class NotificationService:
    def __init__(self, token: str, admin_chat_id: int):
        self.bot = Bot(
            token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        # self.dp = Dispatcher()
        self.admin_chat_id = admin_chat_id
        self.notifications_enabled = True

        # Регистрируем обработчики команд
        # self.dp.message(Command("notifications_on"))(self.notifications_on)
        # self.dp.message(Command("notifications_off"))(self.notifications_off)

        # Запускаем бота в фоне
        # asyncio.create_task(self.dp.start_polling(self.bot))

    async def send_notification(self, message: str):
        if self.notifications_enabled:
            try:
                await self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=f"🔔 <b>Уведомление от системы:</b>\n{message}",
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception as e:
                print(f"[!] Ошибка отправки уведомления: {str(e)}")

    # async def notifications_on(self, message: types.Message):
    #     self.notifications_enabled = True
    #     await message.answer("🔔 Уведомления включены")

    # async def notifications_off(self, message: types.Message):
    #     self.notifications_enabled = False
    #     await message.answer("🔕 Уведомления отключены")

    async def shutdown(self):
        await self.bot.session.close()

    async def send_report_files(self, filename: str, csv_path: str, excel_path: str):
        """Отправляет CSV и Excel отчеты"""
        try:
            # Отправка CSV
            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
                csv_file = FSInputFile(csv_path, filename=f"groups_{filename}.csv")
                await self.bot.send_document(
                    chat_id=self.admin_chat_id,
                    document=csv_file,
                    caption=f"📊 CSV отчет: {filename}",
                )

            # Отправка Excel
            if os.path.exists(excel_path) and os.path.getsize(excel_path) > 0:
                excel_file = FSInputFile(excel_path, filename=f"groups_{filename}.xlsx")
                await self.bot.send_document(
                    chat_id=self.admin_chat_id,
                    document=excel_file,
                    caption=f"📈 Excel отчет: {filename}",
                )

        except Exception as e:
            await self.send_notification(f"🚨 Ошибка отправки отчета: {str(e)}")

    async def send_parsing_summary(
        self, time_str: str, status: str, found_groups_len: int
    ):
        status_emoji = "✅" if status == "completed" else "❌"

        message = (
            f"{status_emoji} <b>Парсинг списка групп {'завершен' if status == 'completed' else 'прерван'}</b>\n"
            f"⏱ Время выполнения: <code>{time_str}</code>\n"
            f"📊 Найдено групп: <code>{found_groups_len}</code>\n"
        )
        await self.send_notification(message)
