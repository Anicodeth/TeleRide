import asyncio
import logging
import sys
import sqlite3
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
    Contact
)

TOKEN = "6638058557:AAHVL5l3wwHryZ9mUtgK74VPRsfwVQySuBM"

# SQLite database initialization
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        phone_number TEXT,
        role TEXT
    )
''')

conn.commit()

form_router = Router()

class UserRegistration(StatesGroup):
    user_id = State()
    full_name = State()
    phone_number = State()
    role = State()

@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await message.answer("Welcome! I will guide you through the registration process. Please provide your full name.")
    
    await state.set_state(UserRegistration.full_name)

@form_router.message(UserRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please provide a valid full name.")
        return
    await state.update_data(full_name=message.text)
    data = await state.get_data()

    await message.answer(f"Thanks, {data['full_name']}! Now, please share your phone number (use the 'Share my phone number' feature).",
    reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text="Share my phone number", request_contact=True)],
                             ],
                             resize_keyboard=True
                         )
                         )

    await state.set_state(UserRegistration.phone_number)

@form_router.message(UserRegistration.phone_number)
async def process_phone_number(message: Contact, state: FSMContext):
    print(message.contact)
    user_id = message.contact.user_id  # Use Telegram user ID as primary key
    await state.update_data(user_id=user_id)
    phone_number = message.contact.phone_number
    await state.update_data(phone_number=phone_number)
    await message.answer(f"Great! I got your phone number: {phone_number}. Now, choose your role.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text="Driver"), KeyboardButton(text="Passenger")]
                             ],
                             resize_keyboard=True
                         ))

    await state.set_state(UserRegistration.role)

@form_router.message(UserRegistration.role)
async def process_role(message: Message, state: FSMContext):
    role = message.text
    await state.update_data(role=role)
    
    # Retrieve user data from state
    data = await state.get_data()

    # Store the user details in SQLite database
    cursor.execute("INSERT OR REPLACE INTO users (user_id, full_name, phone_number, role) VALUES (?, ?, ?, ?)",
                   (data['user_id'], data['full_name'], data['phone_number'], data['role']))
    conn.commit()

    await message.answer(f"Registration complete!\n\n"
                         f"Full Name: {data['full_name']}\n"
                         f"Phone Number: {data['phone_number']}\n"
                         f"Role: {data['role']}\n\n"
                         "You are now signed up!")

    # Finish the registration process and reset the state
    await state.clear()

async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
