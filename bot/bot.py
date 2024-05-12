import logging

import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler

from commands import(
    inline_button_insert,
    start,
    help_command,
    find_email_command,
    find_email_query,
    FIND_EMAIL,
    get_emails_command,
    find_phone_number_command,
    find_phone_number_query,
    FIND_PHONE_NUMBER,
    get_phone_numbers_command,
    get_repl_logs_command,
    verify_password_command,
    verify_password_query,
    VERIFY_PASSWORD,
    get_release_command,
    get_uname_command,
    get_uptime_command,
    get_df_command,
    get_free_command,
    get_mpstat_command,
    get_w_command,
    get_auths_command,
    get_critical_command,
    get_ps_command,
    get_ss_command,
    get_apt_list_command,
    get_services_command
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


#Loading config data from .env
load_dotenv()

#Add commands in Menu Button
command_info = [
    ('start', 'Starts the bot'),
    ('help', 'Show some help'),
    ('find_email', 'Поиск email в тексте'),
    ('get_emails', 'Вывод данных о email-адресах'),
    ('find_phone_number', 'Поиск номеров телефонов в тексте'),
    ('get_phone_numbers', 'Вывод данных о номерах телефона'),
    ('get_repl_logs', 'Вывод логов о репликации'),
    ('verify_password', 'Проверка сложности пароля'),
    ('get_release', 'Информация о релизе'),
    ('get_uname', 'Информация о архитектуре процессора, имени хоста системы и версии ядра.'),
    ('get_uptime', 'Информация о времени работы'),
    ('get_df', 'Сбор информации о состоянии файловой системы'),
    ('get_free', 'Сбор информации о состоянии оперативной памяти.'),
    ('get_mpstat', 'Сбор информации о производительности системы.'),
    ('get_w', 'Сбор информации о работающих в данной системе пользователях.'),
    ('get_auths', 'Логи последних 10 входов в систему.'),
    ('get_critical', 'Логи последних 5 критических событий.'),
    ('get_ps', 'Сбор информации о запущенных процессах.'),
    ('get_ss', 'Сбор информации об используемых портах.'),
    ('get_apt_list', 'Сбор информации об установленных пакетах.'),
    ('get_services', 'Сбор информации о запущенных сервисах.')
]

command_handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    CommandHandler("get_emails", get_emails_command),
    CommandHandler("get_phone_numbers", get_phone_numbers_command),
    CommandHandler("get_repl_logs", get_repl_logs_command),
    CommandHandler("get_release", get_release_command),
    CommandHandler("get_uname", get_uname_command),
    CommandHandler("get_uptime", get_uptime_command),
    CommandHandler("get_df", get_df_command),
    CommandHandler("get_free", get_free_command),
    CommandHandler("get_mpstat", get_mpstat_command),
    CommandHandler("get_w", get_w_command),
    CommandHandler("get_auths", get_auths_command),
    CommandHandler("get_critical", get_critical_command),
    CommandHandler("get_ps", get_ps_command),
    CommandHandler("get_ss", get_ss_command),
    CommandHandler("get_apt_list", get_apt_list_command),
    CommandHandler("get_services", get_services_command)
]
entry_points = [
    CommandHandler("find_email", find_email_command),
    CommandHandler("find_phone_number", find_phone_number_command),
    CommandHandler("verify_password", verify_password_command)
]
states = {
            FIND_EMAIL : [MessageHandler(filters.TEXT & ~filters.COMMAND, find_email_query)],
            FIND_PHONE_NUMBER : [MessageHandler(filters.TEXT & ~filters.COMMAND, find_phone_number_query)],
            VERIFY_PASSWORD : [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password_query)]
        }

#Create Menu Button and filling it with commands
async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(commands=command_info)
    await application.bot.set_chat_menu_button()


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("TOKEN")).post_init(post_init).build()

    command_handlers.append(ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=[],
    ))

    # on different commands - answer in Telegram
    application.add_handlers(command_handlers)
    application.add_handler(CallbackQueryHandler(inline_button_insert))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()