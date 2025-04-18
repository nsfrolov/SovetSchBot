import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "" # ⁡⁢⁡⁢⁣⁣ПОМЕНЯЙТЕ ТОКЕН БОТА НА ВАШ⁡

# Функция для загрузки строк из файла
def load_lines(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

# Загрузка данных из файлов
motivator_lines = load_lines("motivator.txt")  # Мотиваторы
sovet_lines = load_lines("sovet.txt")  # Советы

# Хранилище пользователей, учителей и напоминаний
# users хранит данные в формате: {chat_id: {"fio": str, "role": str, "class": str}}
users = {}
reminders = []  # Список напоминаний: (title, reminder_time, target)
user_message_state = {}  # Состояние для отправки сообщений (например, "send_to_all" или "reminder_all")

# Клавиатуры
registration_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ученик"), KeyboardButton(text="Учитель")]
    ],
    resize_keyboard=True
)

compact_user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Совет"), KeyboardButton(text="Мотиватор")],
        [KeyboardButton(text="Напоминание"), KeyboardButton(text="Учителя")]
    ],
    resize_keyboard=True
)

compact_admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Совет"), KeyboardButton(text="Мотиватор")],
        [KeyboardButton(text="Напоминание"), KeyboardButton(text="Учителя")],
        [KeyboardButton(text="Напоминание всем"), KeyboardButton(text="Сообщение всем")]
    ],
    resize_keyboard=True
)

dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    # Инициализируем данные пользователя
    users[chat_id] = {"fio": None, "role": None, "class": None}
    await message.answer("Добро пожаловать! Для начала регистрации введите ваше ФИО (1, 2 или 3 слова):")

@dp.message()
async def message_handler(message: types.Message):
    chat_id = message.chat.id

    # Если пользователь не зарегистрирован (не вызвал /start), просим начать с команды /start
    if chat_id not in users and message.text != "/start":
        await message.answer("❌ Вы ещё не зарегистрированы. Пожалуйста, начните с команды /start.")
        return

    # Обработка команды /start
    if message.text == "/start":
        users[chat_id] = {"fio": None, "role": None, "class": None}
        await message.answer("Добро пожаловать! Для начала регистрации введите ваше ФИО (1, 2 или 3 слова):")
        return

    # Этап 1: Ввод ФИО
    if users[chat_id]["fio"] is None:
        fio = message.text.strip()
        if 1 <= len(fio.split()) <= 3:
            users[chat_id]["fio"] = fio
            await message.answer(f"Спасибо, {fio}! Теперь выберите вашу роль (нажмите кнопку):", reply_markup=registration_keyboard)
        else:
            await message.answer("ФИО должно состоять из 1, 2 или 3 слов. Попробуйте снова.")
        return

    # Этап 2: Выбор роли
    if users[chat_id]["role"] is None:
        role = message.text.strip().lower()
        if role in ["ученик", "учитель"]:
            users[chat_id]["role"] = role
            if role == "учитель":
                # Учителя будем получать из данных users, поэтому отдельный список teachers не обязателен,
                # но если нужен, можно добавить: teachers.append(users[chat_id]["fio"])
                pass
            await message.answer("Введите ваш класс (например: 10А):")
        else:
            await message.answer("Пожалуйста, выберите одну из ролей: Ученик или Учитель.")
        return

    # Этап 3: Ввод класса
    if users[chat_id]["class"] is None:
        user_class = message.text.strip()
        users[chat_id]["class"] = user_class
        keyboard = compact_admin_keyboard if users[chat_id]["role"] == "учитель" else compact_user_keyboard
        await message.answer(f"Регистрация завершена! Ваша роль: {users[chat_id]['role'].capitalize()}, класс: {user_class}.\n"
                             "Теперь выберите действие из меню ниже.", reply_markup=keyboard)
        return

    # Основной функционал после регистрации
    if users[chat_id]["fio"] and users[chat_id]["role"] and users[chat_id]["class"]:
        if message.text == "Совет":
            random_sovet = random.choice(sovet_lines) if sovet_lines else "Советы отсутствуют."
            await message.answer(f"Ваш совет:\n💡 {random_sovet}")
        elif message.text == "Мотиватор":
            random_motivator = random.choice(motivator_lines) if motivator_lines else "Мотиваторы отсутствуют."
            await message.answer(f"Ваш мотиватор:\n🔥 {random_motivator}")
        elif message.text == "Напоминание":
            await message.answer("Введите напоминание в формате:\nНазвание события; YYYY-MM-DD HH:MM")
        elif message.text == "Учителя":
            # Фильтруем учителей по классу: выводим только тех, у кого класс совпадает с классом текущего пользователя
            current_class = users[chat_id]["class"]
            filtered_teachers = [data["fio"] for uid, data in users.items() 
                                 if data["role"] == "учитель" and data["class"] == current_class]
            if filtered_teachers:
                teacher_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t, callback_data=f"contact_{t}")]
                    for t in filtered_teachers
                ])
                await message.answer("Выберите учителя, с которым хотите связаться:", reply_markup=teacher_keyboard)
            else:
                await message.answer("В вашем классе нет зарегистрированных учителей.")
        elif message.text == "Напоминание всем" and users[chat_id]["role"] == "учитель":
            # Устанавливаем флаг для ввода массового напоминания
            await message.answer("Введите массовое напоминание в формате:\nНазвание события; YYYY-MM-DD HH:MM")
            user_message_state[chat_id] = "reminder_all"
        elif message.text == "Сообщение всем" and users[chat_id]["role"] == "учитель":
            await message.answer("Введите текст сообщения, которое вы хотите отправить всем пользователям.")
            user_message_state[chat_id] = "send_to_all"
        # Если учитель уже выбрал режим массового напоминания, обрабатываем его ввод
        elif chat_id in user_message_state and user_message_state[chat_id] == "reminder_all":
            try:
                title, datetime_str = message.text.split(";")
                reminder_time = datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M")
                reminders.append((title.strip(), reminder_time, "всем"))
                await message.answer("✅ Массовое напоминание успешно создано!")
            except ValueError:
                await message.answer("Ошибка формата. Пример:\nНазвание события; YYYY-MM-DD HH:MM")
            del user_message_state[chat_id]
        # Обработка личных напоминаний (если текст содержит ';' и флаг массового напоминания не установлен)
        elif ";" in message.text:
            try:
                title, datetime_str = message.text.split(";")
                reminder_time = datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M")
                reminders.append((title.strip(), reminder_time, chat_id))
                await message.answer("✅ Личное напоминание успешно создано!")
            except ValueError:
                await message.answer("Ошибка формата. Пример:\nНазвание события; YYYY-MM-DD HH:MM")
        elif chat_id in user_message_state and user_message_state[chat_id] == "send_to_all":
            for uid in users.keys():
                await message.bot.send_message(uid, f"📢 Сообщение от учителя {users[chat_id]['fio']}:\n\n{message.text}")
            await message.answer("✅ Сообщение успешно отправлено всем пользователям.")
            del user_message_state[chat_id]
        # Обработка отправки сообщения конкретному учителю через callback
        elif chat_id in user_message_state:
            selected_teacher = user_message_state.pop(chat_id)
            teacher_chat_id = next((uid for uid, data in users.items() if data["fio"] == selected_teacher), None)
            if teacher_chat_id:
                await message.bot.send_message(teacher_chat_id, f"📩 Сообщение от пользователя {users[chat_id]['fio']}:\n\n{message.text}")
                await message.answer(f"Сообщение успешно отправлено учителю: {selected_teacher}.")
            else:
                await message.answer(f"Не удалось найти учителя с именем {selected_teacher}.")
        else:
            await message.answer("Пожалуйста, используйте кнопки меню для выбора действия.")
    else:
        await message.answer("❌ Регистрация не завершена. Начните с команды /start.")

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    # Обработка нажатий на список учителей
    if callback.data.startswith("contact_"):
        teacher_name = callback.data.split("_")[1]
        user_message_state[callback.from_user.id] = teacher_name
        await callback.message.answer(f"Введите сообщение для учителя {teacher_name}:")
        await callback.answer()

async def send_reminders(bot: Bot):
    while True:
        now = datetime.now()
        due_reminders = [r for r in reminders if r[1] <= now]
        for title, reminder_time, target in due_reminders:
            reminders.remove((title, reminder_time, target))
            if target == "всем":
                for uid in users.keys():
                    await bot.send_message(uid, f"🔔 Напоминание для всех:\n\n{title}")
            else:
                await bot.send_message(target, f"🔔 Ваше напоминание:\n\n{title}")
        await asyncio.sleep(60)

async def main():
    bot = Bot(TOKEN)
    asyncio.create_task(send_reminders(bot))  # Фоновая задача для уведомлений о напоминаниях
    await dp.start_polling(bot)

print("Бот запущен...")
asyncio.run(main())
