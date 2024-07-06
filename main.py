from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
from core.handlers import apsched
from core.settings import settings
from core.handlers.basic import get_start, get_lboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.infrastructure.db_config import create_tables_if_not_exist
from aiogram.filters import Command
import asyncio
import logging
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def start_bot(bot:Bot):
    await bot.send_message(settings.bots.admin_id, text='Старт!')


async def start():
    logging.basicConfig(filename='botLog.txt',
                        filemode='a',
                        level=logging.INFO,
                        format="%(asctime)s - [%(levelname)s] - %(name)s - "
                               "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
                        datefmt='%H:%M:%S')

    bot = Bot(token=settings.bots.bot_token)
    dp = Dispatcher()

    try:
        create_tables_if_not_exist(bot)
    except Exception as e:
        await bot.send_message(chat_id=settings.bots.admin_id,
                               text=f"ВОЗНИКЛА ОШИБКА С БАЗОЙ ДАННЫХ \n\n {e}",
                               parse_mode='Markdown')
        return

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    scheduler.add_job(apsched.post_news, trigger='interval', seconds=600,
                      kwargs={'num_news': 10,
                              'bot': bot})

    scheduler.add_job(apsched.leader_board, trigger='cron', day_of_week='sat', hour=15, minute=48,
                      kwargs={'bot': bot})

    scheduler.start()

    dp.startup.register(start_bot)

    dp.message.register(get_start, Command(commands=['start']))
    dp.message.register(get_lboard, Command(commands=['lb']))

    try:
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())


