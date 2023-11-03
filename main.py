import asyncio
from datetime import date
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import (CallbackQuery, InlineKeyboardButton, FSInputFile,
                           InlineKeyboardMarkup, Message, BotCommand)
from config import Config, load_config
from functions import filter_date, save_clients, load_clients, calculations, give_predict


# Инициализируем логгер
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
    storage = MemoryStorage()
    # redis = Redis(host='localhost')
    # storage = RedisStorage(redis=redis)

    # Загружаем конфиг в переменную config
    config: Config = load_config(None)

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token,
              parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    # Создаем асинхронную функцию для создания меню
    async def set_main_menu(bot: Bot):
        # Создаем список с командами и их описанием для кнопки menu
        main_menu_commands = [
            # BotCommand(command='/help',
            #             description='Справка'),
            BotCommand(command='/start',
                        description='Начало сеанса'),
            BotCommand(command='/session',
                        description='Сеанс'),
            BotCommand(command='/stop',
                    description='Конец сеанса')
        ]
        await bot.set_my_commands(main_menu_commands)
        # await bot.delete_my_commands()

    # Создаем "базу данных" пользователей
    user_dict: dict[int, list(dict[str, str | int | bool])] = {}
    dp.startup.register(set_main_menu)


    # Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
    class FSMFillForm(StatesGroup):
        # Создаем экземпляры класса State, последовательно
        # перечисляя возможные состояния, в которых будет находиться
        # бот в разные моменты взаимодейтсвия с пользователем
        fill_name = State()        # Состояние ожидания ввода имени
        fill_bd = State()         # Состояние ожидания ввода др
        fill_gender = State()      # Состояние ожидания выбора пола
        # fill_bd_partner = State()     # Состояние ожидания ввода др пары
        fill_start_calculate = State()   # Состояние ожидания запроса на начало вычислений


    # Этот хэндлер будет срабатывать на команду /start вне FSM
    # и предлагать перейти к заполнению анкеты, отправив команду /session
    @dp.message(CommandStart(), StateFilter(default_state))
    async def process_start_command(message: Message):
        await message.answer(
            text='   Нумеролог Макс приветствует Вас!\n'
                'Всю жизнь Вас сопровождают числа, данные Вам при рожденьи - день, месяц и год рожденья.\n'
                'Эти числа оказывают огромное влияние на Вашу судьбу.\n'
                'Нумерология изучает это влияние и может дать Вам полезный совет.\n\n'
                'Сегодня я отвечаю на вопрос: Что день текущий мне готовит?\n'
                'Прогноз на сегодня от таро-нумеролога Макса - каждый день бесплатно!\n'
                'Для вычислений применяется новейший математический метод на основе анализа симметричных матриц.\n\n'
                'Помните, что таро-прогнозы - это всего лишь символический инструмент, и их интерпретация всегда зависит от контекста и собственных чувств.\n'
                # 'их интерпретация всегда зависит от контекста и собственных чувств.\n'
                'Вы готовы?\n'
                'Тогда нажимайте /session'
        )


    # Этот хэндлер будет срабатывать на команду "/stop" в состоянии
    # по умолчанию и сообщать, что эта команда работает внутри FSM
    @dp.message(Command(commands='stop'), StateFilter(default_state))
    async def process_cancel_command(message: Message):
        await message.answer(
            text='Вы находитесь вне сеанса.\n'
                'Чтобы начать сеанс - '
                'отправьте команду /session'
        )


    # Этот хэндлер будет срабатывать на команду "/stop" в любых состояниях,
    # кроме состояния по умолчанию и FSM
    @dp.message(Command(commands='stop'), ~StateFilter(default_state))
    async def process_cancel_command_state(message: Message, state: FSMContext):
        await message.answer(
            text='Вы вышли из сеанса.\n'
                'Чтобы вернуться - '
                'отправьте команду /session'
        )
        # Сбрасываем состояние и очищаем данные, полученные внутри состояний
        await state.clear()


    # Этот хэндлер будет срабатывать на команду /session
    # и переводить бота в состояние ожидания ввода имени
    @dp.message(Command(commands='session'), StateFilter(default_state))
    async def process_fillform_command(message: Message, state: FSMContext):
        await message.answer(text='Введите, пожалуйста, Ваше имя: ')
        # Устанавливаем состояние ожидания ввода имени
        await state.set_state(FSMFillForm.fill_name)


    # Этот хэндлер будет срабатывать, если введено корректное имя
    # и переводить в состояние ожидания ввода возраста
    @dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
    async def process_name_sent(message: Message, state: FSMContext):
        # Cохраняем введенное имя в хранилище по ключу "name"
        await state.update_data(name=message.text)
        await message.answer(text='Спасибо!\nА теперь введите, пожалуйста, Ваш день рожденья\n'
                            'в формате дд.мм.гггг: ')
        # Устанавливаем состояние ожидания ввода возраста
        await state.set_state(FSMFillForm.fill_bd)


    # Этот хэндлер будет срабатывать, если во время ввода имени
    # будет введено что-то некорректное
    @dp.message(StateFilter(FSMFillForm.fill_name))
    async def warning_not_name(message: Message):
        await message.answer(
            text='Это не похоже на имя.\n'
                'Пожалуйста, введите Ваше имя.\n'
                #  'Если вы хотите прервать заполнение анкеты -\n '
                #  'отправьте команду /stop'
        )


    # Этот хэндлер будет срабатывать, если введен корректный возраст
    # и переводить в состояние выбора пола
    @dp.message(StateFilter(FSMFillForm.fill_bd),
                lambda x: filter_date(x.text))
    async def process_age_sent(message: Message, state: FSMContext):
        # Cохраняем возраст в хранилище по ключу "bd"
        await state.update_data(bd=message.text)
        # Создаем объекты инлайн-кнопок
        male_button = InlineKeyboardButton(
            text='Мужской ♂',
            callback_data='male'
        )
        female_button = InlineKeyboardButton(
            text='Женский ♀',
                callback_data='female'
        )

        # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
        keyboard: list[list[InlineKeyboardButton]] = [
            [male_button, female_button]
        ]
        # Создаем объект инлайн-клавиатуры
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        # Отправляем пользователю сообщение с клавиатурой
        await message.answer(
            text='Спасибо!\nУкажите, пожалуйста, Ваш пол',
            reply_markup=markup
        )
        # Устанавливаем состояние ожидания выбора пола
        await state.set_state(FSMFillForm.fill_gender)


    # Этот хэндлер будет срабатывать, если во время ввода возраста
    # будет введено что-то некорректное
    @dp.message(StateFilter(FSMFillForm.fill_bd))
    async def warning_not_age(message: Message):
        await message.answer(
            text='Некорректная дата!\nДень рожденья должен быть введён в виде дд.мм.гггг\n'
                'Попробуйте еще раз.'
                #  'Попробуйте еще раз.\n\nЕсли Вы хотите прервать '
                #  'заполнение анкеты -\n\nотправьте команду /stop'
        )


    # Этот хэндлер будет срабатывать на нажатие кнопки при
    # выборе пола и переводит в состояние да/нет начать вычисления
    @dp.callback_query(StateFilter(FSMFillForm.fill_gender),
                    F.data.in_(['male', 'female']))
    async def process_gender_press(callback: CallbackQuery, state: FSMContext):
        # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
        # по ключу "gender"
        await state.update_data(gender=callback.data)
        # Удаляем сообщение с кнопками,
        # чтобы у пользователя не было желания тыкать кнопки
        await callback.message.delete()
            # Создаем объекты инлайн-кнопок
        yes_news_button = InlineKeyboardButton(
            text='Да',
            callback_data='yes_news'
        )
        no_news_button = InlineKeyboardButton(
            text='Нет, спасибо',
            callback_data='no_news')
        # Добавляем кнопки в клавиатуру (две в одном ряду)
        keyboard: list[list[InlineKeyboardButton]] = [
            [yes_news_button, no_news_button],
        ]
        # Создаем объект инлайн-клавиатуры
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        # Отправляем пользователю сообщение с клавиатурой
        await callback.message.answer(
            text='Начать вычисления?',
            reply_markup=markup
        )
        # Устанавливаем состояние ожидания старта вычислений
        await state.set_state(FSMFillForm.fill_start_calculate)


    # Этот хэндлер будет срабатывать, если во время выбора пола
    # будет введено/отправлено что-то некорректное
    @dp.message(StateFilter(FSMFillForm.fill_gender))
    async def warning_not_gender(message: Message):
        await message.answer(
            text='Пожалуйста, пользуйтесь кнопками '
                'при выборе пола\nЕсли вы хотите прервать '
                'заполнение анкеты -\nотправьте команду /stop'
        )


    # Этот хэндлер будет срабатывать на начинать или
    # не начинать вычисления и выводить из машины состояний
    @dp.callback_query(StateFilter(FSMFillForm.fill_start_calculate),
                    F.data.in_(['yes_news', 'no_news']))
    async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
        # Добавляем в "базу данных" анкету пользователя
        # по ключу id пользователя
        user_dict_all = load_clients()
        user_dict[callback.from_user.id] = await state.get_data()
        user_id = str(callback.from_user.id)
        # print(user_dict)
        # print(user_dict_all)
        flag = True
        if user_id in user_dict_all.keys():
            # if len(user_dict_all[user_id]) > 2:
            #     await callback.message.answer(
            #         text = 'Извините, но Вы превысили допустимое количество сеансов: 10\n'
            #     )
            #     flag = False
            # else:
            #     user_dict_all[user_id].append(user_dict[callback.from_user.id])
            user_dict_all[user_id].append(user_dict[callback.from_user.id])
        else:
            user_dict_all[user_id] = [user_dict[callback.from_user.id]]

        save_clients(user_dict_all)

        if user_dict[callback.from_user.id]["gender"] == 'female':
            gender_key = 0
        else:
            gender_key = 1

        today = date.today()
        # dd/mm/YY
        day_today = today.strftime("%d.%m.%Y")
        number_1, number_2 = calculations(str(user_dict[callback.from_user.id]["bd"]), str(day_today))
        # Отправляем в чат выпавшую карту
        card_path = "images/" + str(number_1) + ".jpg"
        card = FSInputFile(card_path)
        await bot.send_photo(callback.message.chat.id, photo=card)
        forecast = give_predict(number_1, gender_key)
        await callback.message.answer(
            text = f'Сегодня Ваше число силы: {number_1}\n\n'
                # f'Слабое число вашего союза: {number_2}\n\n'
                # 'Прогноз для вашей пары:\n\n'
                f'{forecast}'
                f'\n\nЕсли хотите знать больше - пишите по адресу: mishelnumerologie@gmail.com'
                f'\n\nСовместимость в паре, прогноз успеха в важном деле, любые таро-нумерологические исследования.'
        )
        # Завершаем машину состояний
        await state.clear()
        # Отправляем в чат сообщение с предложением посмотреть свою анкету
        # await callback.message.answer(
        #     text='Чтобы посмотреть данные Вашего запроса -\n'
        #         'отправьте команду /showdata'
        # )

    # Этот хэндлер будет срабатывать, если во время согласия на
    # вычисления будет введено/отправлено что-то некорректное
    @dp.message(StateFilter(FSMFillForm.fill_start_calculate))
    async def warning_not_wish_news(message: Message):
        await message.answer(
            text='Пожалуйста, воспользуйтесь кнопками!\n'
                'Если вы хотите прервать заполнение анкеты -\n'
                'отправьте команду /stop'
        )

    # Этот хэндлер будет срабатывать на отправку команды /showdata
    # и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
    @dp.message(Command(commands='showdata'), StateFilter(default_state))
    async def process_showdata_command(message: Message):
        # Отправляем пользователю анкету, если она есть в "базе данных"
        if message.from_user.id in user_dict:
            await message.answer(
                text = f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'День рожденья: {user_dict[message.from_user.id]["bd"]}\n'
                    f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
                    # f'День рожденья пары: {user_dict[message.from_user.id]["bd_partner"]}'
            )
        else:
            # Если анкеты пользователя в базе нет - предлагаем заполнить
            await message.answer(
                text='Вы еще не ввели Ваши данные.'
                'Чтобы приступить - отправьте команду /session'
            )


    # Этот хэндлер будет срабатывать на любые сообщения, кроме тех
    # для которых есть отдельные хэндлеры, вне состояний
    @dp.message(StateFilter(default_state))
    async def send_echo(message: Message):
        await message.reply(text='Извините, некорректная команда')


    # Запускаем поллинг
    # if __name__ == '__main__':
    #     # Регистрируем асинхронную функцию создания меню в диспетчере,
    #     # которая будет выполняться на старте бота,
    #     dp.startup.register(set_main_menu)
    #     dp.run_polling(bot)


# Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
