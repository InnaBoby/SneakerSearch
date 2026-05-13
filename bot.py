import os
import logging
import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
import asyncio
import logging

# #local_mode
# from dotenv import load_dotenv
# load_dotenv()

logger = logging.getLogger(__name__)

SERVER_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

if PROXY_URL:
    bot_session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=bot_session)
else:
    bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать")]
    ],
    resize_keyboard=True, # чтобы кнопка не была на пол-экрана
    input_field_placeholder="Загрузи фото"
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для поиска похожих кросовок. Загрузи фотку кроссовка и я найду 3 похожие модели",
        reply_markup=start_keyboard,
        parse_mode="HTML"
        )
    
@dp.message(F.text == "Начать")
async def start_instruction(message: types.Message):
    instruction = (
        "Пришли мне фото кроссовок, и я найду 3 похожие модели \n",
        "<i>Жду твое фото!</i>"
    )
    await message.answer(instruction, parse_mode="HTML")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]
    
    file_info = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file_info.file_path)

    await message.answer("Начинаю поиск")

    # отправляем фото на эндпоинт API
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('upload_image', photo_bytes, filename='query.jpg', content_type='image/jpeg')

        async with session.post(SERVER_URL, data=data) as response:
            print(response.status)
            if response.status == 200:
                result = await response.json()
                items = result.get("results", [])

                if not items:
                    await message.answer("Ничего не нашел, попробуй другое фото")
                    return
                
                if isinstance(items, str):
                    await message.answer(f"Я не нашел кроссовки на загруженном фото. Попробуй загрузить другое фото!")
                    return

                # 3. Выводим результаты (топ-3)
                for item in items[:3]:
                    caption = (f"{item['brand']} {item['model']}\n")
                    # await message.answer(caption)
                    
                    # отправляем фото похожих кандидатов
                    await message.answer_photo(FSInputFile(item['image_url']), caption=caption)
                    
            else:
                await message.answer(f"Ошибка {response.status}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
