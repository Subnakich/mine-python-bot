import subprocess
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import filters
import time

# Токен бота
TOKEN = 'TOKEN HERE'
admins = ['YOUR TELEGRAM ID HERE']

string_check_start = '[minecraft/DedicatedServer]: Done'
string_check_stop = 'All dimensions are saved'
string_check_players = 'players online'
string_check_error = 'Что-то произошло. Мне не удалось вывести ответ сервера'

path_to_run_file = 'YOUT PATH HERE'

# Инициализируем бота и диспатчер
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)
server: subprocess.Popen

# Функция для проверки лога на наличие определенной фразы
def check_reply(filename, string_check):
    with open(filename, 'r') as f:
        # Читаем файл и разделяем по строкам
        lines = f.read().split('\n')

        # Инвертируем порядок строк (чтобы ловить свежий ответ)
        lines = lines[::-1]

        # Поиск последней строки с заданной
        for i in range(len(lines)):
            if string_check in lines[i]:
                # Обрезаем строки до найденной
                lines = lines[i::-1]
                break

        if any(string_check in line for line in lines):
            return "".join(lines)
        else:
            return string_check_error

# Функция для запуска сервера Minecraft
async def start_minecraft_server(userId):

    output = subprocess.check_output(['ps', '-A'])
    output = output.decode('utf-8')
    if 'java' not in output:

        # Запускаем команду в терминале, выводим логи в out.log и err.log
        with open('out.log','w') as out, open('err.log','w') as err:
            process = subprocess.Popen([path_to_run_file], stdout=out, stdin=subprocess.PIPE, stderr=err, encoding='utf-8', text=True, universal_newlines=True)

        # Даем глобальный доступ в нашему процессу
        global server
        server = process

        while check_reply('out.log', string_check_start) == string_check_error:
            time.sleep(20)

        await bot.send_message(chat_id=userId, text='Сервер запущен')
    else:
        await bot.send_message(chat_id=userId, text='Сервер уже запущен!')
    
# Функция для остановки сервера Minecraft
async def stop_minecraft_server(userId):
    
    output = subprocess.check_output(['ps', '-A'])
    output = output.decode('utf-8')
    if 'java' in output:
        await bot.send_message(chat_id=userId, text='Останавливаю сервер..')

        # Командой /stop останавливаем сервер
        server.stdin.write("stop\n")
        server.stdin.flush()

        # Усыпляем ненадолго, чтобы сервер успел остановиться
        time.sleep(30)
        outputs = check_reply('out.log', string_check_stop)

        await bot.send_message(chat_id=userId, text=outputs[0])
    else:
        await bot.send_message(chat_id=userId, text='Сервер Minecraft не запущен')    

# Функция для проверки статуса сервера
async def check_minecrfat_server(userId):
    output = subprocess.check_output(['ps', '-A'])
    output = output.decode('utf-8')
    if 'java' in output:
        await bot.send_message(chat_id=userId, text='Сервер Minecraft запущен. Сейчас узнаем, кто в игре')

        # Командой /list запрашиваем список игроков сервера    
        server.stdin.write("list\n")
        server.stdin.flush()

        # Усыпляем ненадолго, чтобы команда успела отработать и сервер прислал ответ
        time.sleep(5)
        outputs = check_reply('out.log', string_check_players)

        # Отравляем список игроков
        await bot.send_message(chat_id=userId, text=outputs)
    else:
        await bot.send_message(chat_id=userId, text='Сервер Minecraft не запущен')

# Хендлер для команды /start
@dp.message_handler(commands=['start'])
@dp.throttled(rate=60)
async def start_command(message: types.Message):
    # Отправляем сообщение с инструкцией для проверки сервера Minecraft
    await message.reply("Для просмотра состояния сервера доступна команда /status")

# Хендлер для команды /status
@dp.message_handler(commands=['status'])
@dp.throttled(rate=30)
async def status(message: types.Message):
    await message.reply("Проверяю состояние сервера...")
    await check_minecrfat_server(message.from_user.id)

# Хендлер для команды /start_server
@dp.message_handler(filters.IDFilter(user_id=admins), commands=['start_server'])
@dp.throttled(rate=60)
async def minecraft_command(message: types.Message):
    await message.reply("Запускаю сервер Minecraft...")
    await start_minecraft_server(message.from_user.id)

# Хендлер для команды /stop_server
@dp.message_handler(filters.IDFilter(user_id=admins), commands=['stop_server'])
@dp.throttled(rate=60)
async def stop_server(message: types.Message):
    await stop_minecraft_server(message.from_user.id)
    await message.reply('Сервер Minecraft остановлен. Все измерения сохранены')

# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
