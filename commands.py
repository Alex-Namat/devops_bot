from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import logging
import re
import paramiko
import psycopg2
from psycopg2 import Error, sql

import os
from dotenv import load_dotenv
from shlex import quote

load_dotenv()

#States in conversation handler
FIND_EMAIL, FIND_PHONE_NUMBER, VERIFY_PASSWORD =range(3)

#Connect and send a request to the host and receiving a response
def query_SSH(query : str) -> str:
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
        stdin, stdout, stderr = client.exec_command(query)
        data = stdout.read().decode() + stderr.read().decode()
        logging.info("SSH: Команда %s успешно выполнена", query)
        return str(data).replace('\\n', '\n').replace('\\t', '\t')
    except (Exception) as error:
        logging.error("Ошибка при работе с SSH: %s", error)
        return "Ошибка при работе с SSH"
    finally:
        if client.get_transport() is not None:
            client.close()

#Connect and send a request to the data base and receiving a response
def query_DB(sql : sql.SQL) -> tuple:
    connection = None
    data = ""
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                password=os.getenv('DB_PASSWORD'),
                                host=os.getenv('DB_HOST'),
                                port=os.getenv('DB_PORT'), 
                                database=os.getenv('DB_DATABASE'))
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(query = sql)
        if cursor.pgresult_ptr is not None:
            for row in cursor:
                data += ' '.join(map(str, row)) + '\n'  
        logging.info("PostgreSQL: Команда %s успешно выполнена", sql.as_string)
        return True, data
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return False, data 
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


async def inline_button_insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    data = context.user_data[query.data + "_data"].split('\n')
    table = context.user_data[query.data + "_table"]
    column = context.user_data[query.data + "_column"]
    text = ''
    for row in data:
        result = query_DB(sql.SQL("INSERT INTO {table} ({column}) VALUES ({value});")
                    .format(table = sql.Identifier(table),
                            column = sql.Identifier(column),
                            value = sql.Literal(row)))
        if result[0]:
            text += f"{column.capitalize()}: {row} успешно сохранён\n"
        else:
            text += f"{column.capitalize()}: {row} не сохранён\n'" 
    msg = await query.edit_message_text(text=text[:4096])
    if not msg:
        msgs = [text[i:i + 4096] for i in range(1, len(text), 4096)]
        for i in msgs:
            await update.message.reply_text(text=i,reply_to_message_id=msg.message_id)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def find_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /find_email is issued."""
    await update.message.reply_text("Введите текст:")
    return FIND_EMAIL

async def find_email_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regex = re.compile(r"((?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\]))")
    email = update.message.text
    id = str(update.update_id)
    result = re.finditer(regex, email)
    data = '\n'.join(match.group(0) for match in result)
    context.user_data[id + "_data"] = data
    context.user_data[id + "_table"] = "emails"
    context.user_data[id + "_column"] = "email"
    if data:        
        data = "Найденные email адреса:\n" + data
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for i in range(0, len(msgs)-1):
            await update.message.reply_text(text=msgs[i])
        await update.message.reply_text(msgs[-1], reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Записать данные", callback_data=id)]]))
    else:
       await update.message.reply_text(text="В тексте не содержатся email адреса.")
    return ConversationHandler.END


async def get_emails_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_emails is issued."""
    result = query_DB(sql.SQL("SELECT * FROM emails"))
    if result[0]:
        data = result[1]
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for text in msgs:
            await update.message.reply_text(text=text)
    else:
       await update.message.reply_text(text="Ошибка при работе с PostgreSQL.")


async def find_phone_number_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /find_phone_number is issued."""
    await update.message.reply_text("Введите текст:")
    return FIND_PHONE_NUMBER

async def find_phone_number_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regex = re.compile(r"(?:\+7|8)+[ \-\(]?\(?(\d{3})\)?[ \-\)]?(\d{3})[ \-]?(\d{2})[ \-]?(\d{2})")
    phone_number = update.message.text
    id = str(update.update_id)
    result = re.finditer(regex, phone_number)
    data = '\n'.join(match.group(0) for match in result)
    context.user_data[id + "_data"] = data
    context.user_data[id + "_table"] = "phones"
    context.user_data[id + "_column"] = "phone"
    if data:        
        data = "Найденные номера телефонов:\n" + data
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for i in range(0, len(msgs)-1):
            await update.message.reply_text(text=msgs[i])
        await update.message.reply_text(msgs[-1], reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Записать данные", callback_data=id)]]))
    else:
       await update.message.reply_text(text="В тексте не содержатся номера телефонов.")
    return ConversationHandler.END

async def get_phone_numbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_phone_numbers is issued."""
    result = query_DB(sql.SQL("SELECT * FROM phones"))
    if result[0]:
        data = result[1]
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for text in msgs:
            await update.message.reply_text(text=text)
    else:
       await update.message.reply_text(text="Ошибка при работе с PostgreSQL.")


async def get_repl_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_repl_logs is issued."""
    result = query_DB(sql.SQL("SELECT log_line  \
                            FROM regexp_split_to_table(pg_read_file(pg_current_logfile()), E'\n')log_line \
                            WHERE regexp_substr(log_line,{regex}, 1, 1, 'i', 1) is not null;")
                            .format(regex = sql.Literal('replication|репликации|' + os.getenv('DB_REPL_USER') + '@')))
    if result[0]:
        data = result[1]
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for text in msgs:
            await update.message.reply_text(text=text)
    else:
       await update.message.reply_text(text="Ошибка при работе с PostgreSQL.")


async def verify_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /verify_password is issued."""
    await update.message.reply_text("Введите текст:")
    return VERIFY_PASSWORD

async def verify_password_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regex = re.compile(r"^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[!@#$%^&*()]).{8,}$")
    verify_password = update.message.text
    result = re.search(regex, verify_password)
    if result:
        data = "Пароль сложный"
    else:
        data = "Пароль простой"
    await update.message.reply_text(data)
    return ConversationHandler.END


async def get_release_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_release is issued."""
    data = query_SSH(r'cat /etc/*release')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_uname_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_uname is issued."""
    data = query_SSH(r'uname -a')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_uptime is issued."""
    data = query_SSH(r'uptime')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_df_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_df is issued."""
    data = query_SSH(r'df -h')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_free_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_free is issued."""
    data = query_SSH(r'free -h')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_mpstat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_mpstat is issued."""
    data = query_SSH(r'mpstat -P ALL')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_w_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_w is issued."""
    data = query_SSH(r'w -sfi')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_auths_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_auths is issued."""
    data = query_SSH(r'last -10R')
    await update.message.reply_text(data)


async def get_critical_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_critical is issued."""
    data = query_SSH(r'journalctl -p crit | tail -n 5')
    await update.message.reply_text(data)


async def get_ps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_ps is issued."""
    data = query_SSH(r'ps')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)

async def get_ss_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_ss is issued."""
    data = query_SSH(r'ss -a')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)

async def get_apt_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_apt_list is issued."""
    data = " ".join(quote(str(element)) for element in context.args)
    if data:
        data = query_SSH(r'apt list --installed ' + data)
    else:
        data = query_SSH(r'apt list --installed')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)


async def get_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_apt_list is issued."""
    data = query_SSH(r'systemctl list-units --type=service --state=active')
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)
