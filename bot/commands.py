from telegram import ForceReply, Update
from telegram.ext import ContextTypes, ConversationHandler

import re
import logging
import paramiko

from dotenv import dotenv_values, find_dotenv

#Loading config data from .env
config = dotenv_values(find_dotenv())

#States in conversation handler
FIND_EMAIL, FIND_PHONE_NUMBER, VERIFY_PASSWORD =range(3)

#Connect and send a request to the host and receiving a response
def query_SSH(query : str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=config['RM_HOST'], username=config['RM_USER'], password=config['RM_PASSWORD'], port=config['RM_PORT'])
    stdin, stdout, stderr = client.exec_command(query)
    data = stdout.read().decode() + stderr.read().decode()
    client.close()
    return str(data).replace('\\n', '\n').replace('\\t', '\t')

#Sending a message Telegram regardless of length
async def send_reply(update: Update, data: str) -> None:
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
       await update.message.reply_text(text=text)

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
    regex = re.compile(r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")
    email = update.message.text
    result = re.finditer(regex, email)
    msg = ''
    i = 0
    for match in result:
        i+=1
        msg += f'{i}. {match.group(0)}\n'
    if msg:
        msg = "Найденные email адреса:\n" + msg
    else:
        msg = "В тексте не содержатся email адреса."
    send_reply(msg)
    return ConversationHandler.END


async def find_phone_number_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /find_phone_number is issued."""
    await update.message.reply_text("Введите текст:")
    return FIND_PHONE_NUMBER

async def find_phone_number_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regex = re.compile(r"(8|\+7)+[ \-\(]?\(?(\d{3})\)?[ \-\)]?(\d{3})[ \-]?(\d{2})[ \-]?(\d{2})")
    phone_number = update.message.text
    result = re.finditer(regex, phone_number)
    msg = ''
    i = 0
    for match in result:
        i+=1
        msg += f'{i}. {match.group(0)}\n'
    if msg:
        msg = "Найденные номера телефонов:\n" + msg
    else:
        msg = "В тексте не содержатся номера телефонов."
    send_reply(msg)
    return ConversationHandler.END


async def verify_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /verify_password is issued."""
    await update.message.reply_text("Введите текст:")
    return VERIFY_PASSWORD

async def verify_password_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    regex = re.compile(r"^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$")
    verify_password = update.message.text
    result = re.search(regex, verify_password)
    if result:
        msg = "Пароль сложный"
    else:
        msg = "Пароль простой"
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def get_release_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_release is issued."""
    data = query_SSH(r'cat /etc/*release')
    send_reply(data)


async def get_uname_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_uname is issued."""
    data = query_SSH(r'uname -a')
    send_reply(data)


async def get_uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_uptime is issued."""
    data = query_SSH(r'uptime')
    send_reply(data)


async def get_df_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_df is issued."""
    data = query_SSH(r'df -a')
    send_reply(data)


async def get_free_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_free is issued."""
    data = query_SSH(r'free -h')
    send_reply(data)


async def get_mpstat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_mpstat is issued."""
    data = query_SSH(r'mpstat -P ALL')
    send_reply(data)


async def get_w_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_w is issued."""
    data = query_SSH(r'w -sfi')
    send_reply(data)


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
    send_reply(data)

async def get_ss_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_ss is issued."""
    data = query_SSH(r'ss -l')
    send_reply(data)

async def get_apt_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_apt_list is issued."""
    data = " ".join(str(element) for element in context.args)
    if data:
        data = query_SSH(r'apt list ' + data)
    else:
        data = query_SSH(r'apt list --installed')
    send_reply(data)


async def get_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /get_apt_list is issued."""
    data = query_SSH(r'systemctl list-units --type=service --state=active')
    send_reply(data)
