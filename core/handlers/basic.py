from aiogram.types import Message, TextQuote
from core.handlers import apsched
from core.settings import settings
from aiogram import Bot

bot = Bot(token=settings.bots.bot_token)


async def get_start(message: Message):
    await message.reply(text='Hi', parse_mode='Markdown')


async def get_lboard(message: Message):
    await apsched.leader_board(bot)

