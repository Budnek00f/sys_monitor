import logging
import psutil
import subprocess
import os
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота (получить у @BotFather)
BOT_TOKEN = "5696379337:AAFOKBjO0wiMZDs2lqsc7RPPFnODOJK4Qi4"

# ID администраторов (можно получить через @userinfobot)
ADMIN_IDS = [86458589]  # Замените на ваш ID 

# Клавиатура для удобства
KEYBOARD = ReplyKeyboardMarkup([
    ['/status', '/reboot'],
    ['/disk', '/processes'],
    ['/help']
], resize_keyboard=True)

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Я бот для мониторинга сервера.\n"
        "Используй /help для списка команд.",
        reply_markup=KEYBOARD
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/status - Информация о состоянии сервера
/disk - Информация о дисковом пространстве
/processes - Список процессов
/reboot - Перезагрузка сервера (только для админов)
/help - Справка по командам
"""
    await update.message.reply_text(help_text, reply_markup=KEYBOARD)

async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о состоянии сервера"""
    try:
        # Информация о CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Информация о памяти
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)
        memory_used = round(memory.used / (1024**3), 2)
        memory_percent = memory.percent
        
        # Информация о загрузке системы
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Форматируем время загрузки
        boot_time_formatted = datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')
        
        status_text = f"""
🖥️ Статус сервера:

💾 CPU:
  - Использование: {cpu_percent}%
  - Ядер: {cpu_count}

📊 Память:
  - Всего: {memory_total} GB
  - Использовано: {memory_used} GB ({memory_percent}%)

⏰ Время работы:
  - Запущен: {boot_time_formatted}
  - Аптайм: {int(hours)}ч {int(minutes)}м {int(seconds)}с
"""
        await update.message.reply_text(status_text, reply_markup=KEYBOARD)
        
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении статуса: {e}")

async def disk_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о дисковом пространстве"""
    try:
        disk_text = "💿 Дисковое пространство:\n\n"
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = round(usage.total / (1024**3), 2)
                used_gb = round(usage.used / (1024**3), 2)
                free_gb = round(usage.free / (1024**3), 2)
                percent = usage.percent
                
                disk_text += f"📁 {partition.mountpoint}:\n"
                disk_text += f"  - Всего: {total_gb} GB\n"
                disk_text += f"  - Использовано: {used_gb} GB ({percent}%)\n"
                disk_text += f"  - Свободно: {free_gb} GB\n\n"
                
            except PermissionError:
                continue
        
        await update.message.reply_text(disk_text, reply_markup=KEYBOARD)
        
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении информации о дисках: {e}")

async def processes_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о процессах"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Сортируем по использованию CPU
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        
        processes_text = "🔍 Топ процессов по CPU:\n\n"
        for i, proc in enumerate(processes[:10], 1):  # Показываем топ-10
            processes_text += f"{i}. PID {proc['pid']}: {proc['name']}\n"
            processes_text += f"   CPU: {proc['cpu_percent'] or 0:.1f}%"
            processes_text += f"   Memory: {proc['memory_percent'] or 0:.1f}%\n\n"
        
        await update.message.reply_text(processes_text, reply_markup=KEYBOARD)
        
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении информации о процессах: {e}")

async def reboot_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезагрузка сервера"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды!")
        return
    
    try:
        await update.message.reply_text("🔄 Инициирую перезагрузку сервера...")
        
        # Команда для перезагрузки (для Linux)
        if os.name == 'posix':
            # Безопасный способ - через systemctl
            subprocess.run(['sudo', 'systemctl', 'reboot'], check=True)
        # Для Windows
        elif os.name == 'nt':
            subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
        else:
            await update.message.reply_text("❌ Неподдерживаемая операционная система")
            return
            
        await update.message.reply_text("✅ Команда на перезагрузку отправлена!")
        
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка при перезагрузке: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Неожиданная ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()
    
    if text in ['статус', 'status']:
        await server_status(update, context)
    elif text in ['диск', 'disk']:
        await disk_info(update, context)
    elif text in ['процессы', 'processes']:
        await processes_info(update, context)
    elif text in ['перезагрузка', 'reboot']:
        await reboot_server(update, context)
    else:
        await update.message.reply_text(
            "Используйте команды из меню или /help для справки.",
            reply_markup=KEYBOARD
        )

def main():
    """Запуск бота"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", server_status))
        application.add_handler(CommandHandler("disk", disk_info))
        application.add_handler(CommandHandler("processes", processes_info))
        application.add_handler(CommandHandler("reboot", reboot_server))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        print("Бот запущен...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()