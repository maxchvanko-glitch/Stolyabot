import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Токен и админ ---
API_TOKEN = "8336832357:AAHuhasIfBKcukiHYCcQgDwGN8uvg8-oCtg"  # вставь свой токен от BotFather
ADMIN_ID =1253647898        # вставь свой telegram_id
DATA_FILE = "records.json"

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Машина состояний ---
class Booking(StatesGroup):
    was_here = State()
    workshop = State()
    stol_day = State()
    stol_time = State()
    stol_age = State()
    stol_name_year = State()
    pug_activity = State()
    pug_day = State()
    pug_time = State()
    pug_age = State()
    pug_name_year = State()
    cancel_choice = State()

# --- Работа с файлами ---
def load_records():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def count_in_slot(place, activity, day, time):
    records = load_records()
    return sum(1 for r in records if r["place"] == place and r["activity"] == activity and r["day"] == day and r["time"] == time)

# --- Старт ---
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Да", "Нет")
    await message.answer("Здравствуйте! Были ли вы у нас ранее?", reply_markup=kb)
    await Booking.was_here.set()

# --- Были ли вы ранее ---
@dp.message_handler(state=Booking.was_here)
async def process_was_here(message: types.Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        return
    if message.text == "Нет":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")
        await message.answer(
            "Мы — это творческие мастерские для детей: <b>Столяркино</b> и <b>Пуговкино</b>.\nХотите записаться?",
            reply_markup=kb
        )
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")
        await message.answer("Хотите записаться?", reply_markup=kb)
    await Booking.workshop.set()

# --- Выбор мастерской ---
@dp.message_handler(state=Booking.workshop)
async def process_workshop(message: types.Message, state: FSMContext):
    if message.text == "Нет":
        await message.answer("Будем рады видеть вас в следующий раз!", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return
    if message.text == "Да":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Столяркино", "Пуговкино")
        await message.answer("В какую мастерскую вы хотите записаться?", reply_markup=kb)
        return
    if message.text == "Столяркино":
        await state.update_data(place="Столяркино", activity="Обычные занятия")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
        await message.answer("Выберите день:", reply_markup=kb)
        await Booking.stol_day.set()
    elif message.text == "Пуговкино":
        await state.update_data(place="Пуговкино")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Рукоделие", "Вязание крючком", "Интересное рисование")
        await message.answer("Выберите занятие:", reply_markup=kb)
        await Booking.pug_activity.set()

# --- Ветка Столяркино ---
@dp.message_handler(state=Booking.stol_day)
async def process_stol_day(message: types.Message, state: FSMContext):
    await state.update_data(day=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == "Среда":
        kb.add("14:00", "18:00")
    elif message.text in ["Четверг", "Пятница"]:
        kb.add("10:00", "14:00", "18:00")
    elif message.text in ["Суббота", "Воскресенье"]:
        kb.add("10:00", "12:00", "14:00", "16:00", "18:00")
    await message.answer("Выберите время:", reply_markup=kb)
    await Booking.stol_time.set()

@dp.message_handler(state=Booking.stol_time)
async def process_stol_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("4-6", "7-9", "10+")
    await message.answer("Выберите возраст ребёнка:", reply_markup=kb)
    await Booking.stol_age.set()

@dp.message_handler(state=Booking.stol_age)
async def process_stol_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите имя и год рождения ребёнка (например: Анна 2018):", reply_markup=types.ReplyKeyboardRemove())
    await Booking.stol_name_year.set()

@dp.message_handler(state=Booking.stol_name_year)
async def process_stol_name_year(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if count_in_slot("Столяркино", "Обычные занятия", data["day"], data["time"]) >= 5:
        await message.answer("❌ В этой группе уже 5 записей, мест нет.")
        await state.finish()
        return
    record = {
        "place": "Столяркино",
        "activity": "Обычные занятия",
        "day": data["day"],
        "time": data["time"],
        "age": data["age"],
        "child": message.text,
        "parent": message.from_user.full_name,
        "tg_id": message.from_user.id
    }
    records = load_records()
    records.append(record)
    save_records(records)
    await message.answer(
        f"✅ Запись успешно создана!\n"
        f"<b>Мастерская:</b> Столяркино\n"
        f"<b>День:</b> {data['day']}\n"
        f"<b>Время:</b> {data['time']}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Ребёнок:</b> {message.text}"
    )
    await state.finish()

# --- Ветка Пуговкино ---
@dp.message_handler(state=Booking.pug_activity)
async def process_pug_activity(message: types.Message, state: FSMContext):
    act = message.text
    await state.update_data(activity=act)
    if act == "Рукоделие":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Вторник", "Четверг", "Суббота", "Воскресенье")
        await message.answer("Выберите день:", reply_markup=kb)
        await Booking.pug_day.set()
    elif act == "Вязание крючком":
        await state.update_data(day="Суббота", time="16:00")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("4-6", "7-9", "10+")
        await message.answer("Выберите возраст ребёнка:", reply_markup=kb)
        await Booking.pug_age.set()
    elif act == "Интересное рисование":
        await state.update_data(day="Воскресенье", time="14:00")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("4-6", "7-9", "10+")
        await message.answer("Выберите возраст ребёнка:", reply_markup=kb)
        await Booking.pug_age.set()

@dp.message_handler(state=Booking.pug_day)
async def process_pug_day(message: types.Message, state: FSMContext):
    day = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if day in ["Вторник", "Четверг"]:
        kb.add("18:00")
    elif day == "Суббота":
        kb.add("10:00", "12:00", "14:00")
    elif day == "Воскресенье":
        kb.add("10:00", "12:00")
    await state.update_data(day=day)
    await message.answer("Выберите время:", reply_markup=kb)
    await Booking.pug_time.set()

@dp.message_handler(state=Booking.pug_time)
async def process_pug_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("4-6", "7-9", "10+")
    await message.answer("Выберите возраст ребёнка:", reply_markup=kb)
    await Booking.pug_age.set()

@dp.message_handler(state=Booking.pug_age)
async def process_pug_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите имя и год рождения ребёнка (например: Анна 2018):", reply_markup=types.ReplyKeyboardRemove())
    await Booking.pug_name_year.set()

@dp.message_handler(state=Booking.pug_name_year)
async def process_pug_name_year(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if count_in_slot("Пуговкино", data["activity"], data["day"], data["time"]) >= 5:
        await message.answer("❌ В этой группе уже 5 записей, мест нет.")
        await state.finish()
        return
    record = {
        "place": "Пуговкино",
        "activity": data["activity"],
        "day": data["day"],
        "time": data["time"],
        "age": data["age"],
        "child": message.text,
        "parent": message.from_user.full_name,
        "tg_id": message.from_user.id
    }
    records = load_records()
    records.append(record)
    save_records(records)
    await message.answer(
        f"✅ Запись успешно создана!\n"
        f"<b>Мастерская:</b> Пуговкино\n"
        f"<b>Занятие:</b> {data['activity']}\n"
        f"<b>День:</b> {data['day']}\n"
        f"<b>Время:</b> {data['time']}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Ребёнок:</b> {message.text}"
    )
    await state.finish()

# --- Команды пользователя ---
@dp.message_handler(commands=["мои", "zapisi"])
async def cmd_my(message: types.Message):
    records = load_records()
    user_recs = [r for r in records if r["tg_id"] == message.from_user.id]
    if not user_recs:
        await message.answer("У вас пока нет записей.")
        return
    text = "📋 Ваши записи:\n\n"
    for i, r in enumerate(user_recs, start=1):
        text += (f"{i}. <b>{r['place']}</b> — {r['activity']}\n"
                 f"{r['day']} {r['time']}, возраст {r['age']}\n"
                 f"Ребёнок: {r['child']}\n\n")
    await message.answer(text)

@dp.message_handler(commands=["все", "spisok"])
async def cmd_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    records = load_records()
    if not records:
        await message.answer("Записей пока нет.")
        return
    text = "📋 Все записи:\n\n"
    for r in records:
        text += (f"<b>{r['place']}</b> — {r['activity']}\n"
                 f"{r['day']} {r['time']} (возраст {r['age']})\n"
                 f"Ребёнок: {r['child']}, Родитель: {r['parent']}\n\n")
    await message.answer(text)

# --- Отмена записи ---
@dp.message_handler(commands=["отмена", "cancel"], state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    records = load_records()
    user_recs = [r for r in records if r["tg_id"] == message.from_user.id]
    if not user_recs:
        await message.answer("❌ У вас нет активных записей.", reply_markup=types.ReplyKeyboardRemove())
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, r in enumerate(user_recs, start=1):
        kb.add(f"{i}. {r['place']} {r['day']} {r['time']}")
    await state.update_data(cancel_list=user_recs)
    await message.answer("Выберите запись для отмены:", reply_markup=kb)
    await Booking.cancel_choice.set()

@dp.message_handler(state=Booking.cancel_choice)
async def process_cancel_choice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_recs = data.get("cancel_list", [])
    try:
        idx = int(message.text.split(".")[0]) - 1
        record = user_recs[idx]
    except:
        await message.answer("❌ Пожалуйста, выберите запись из списка.")
        return
    records = load_records()
    records = [r for r in records if not (
        r["tg_id"] == record["tg_id"] and
        r["place"] == record["place"] and
        r["day"] == record["day"] and
        r["time"] == record["time"] and
        r["child"] == record["child"]
    )]
    save_records(records)
    await message.answer(f"✅ Запись <b>{record['place']} {record['day']} {record['time']}</b> отменена.",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# --- Тестовая команда для проверки работы ---
@dp.message_handler(commands=["test"])
async def test_cmd(message: types.Message):
    await message.answer("Бот работает!")

# --- Запуск ---
if __name__ == "__main__":
    print("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
