import logging
import traceback
from zoneinfo import ZoneInfo
import os

from telegram import (
    Update,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Defaults,
)
# from telegram.helpers import escape_markdown

from data import TOKEN, MY_ID
# from database import Database
from lichess import get_lichess_activity_message, get_lichess_username_from_id


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.id not in about_to_set_lichess_username:
        return

    lichess_username = get_lichess_username_from_id(update.message.text.strip())
    if lichess_username is None:
        await update.message.reply_text('Такого пользователя не существует, повтори попытку')
        return

    about_to_set_lichess_username.remove(chat.id)
    # db.update_lichess_username(chat.id, lichess_username)
    await send_lichess_activity(update, lichess_username)


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global COMMANDS_SET
    chat = update.effective_chat
    if update.message.chat.PRIVATE:
        if chat.id == MY_ID and not COMMANDS_SET:
            COMMANDS_SET = True
            await context.bot.set_my_commands(commands=bot_commands, scope=BotCommandScopeAllPrivateChats())
            await context.bot.set_my_commands(commands=bot_commands_admin, scope=BotCommandScopeChat(MY_ID))
            await update.message.reply_text('👌')
            return

        # user = db.get_user(chat.id)
        # if user:
        #     if user.lichess_username:
        #         await send_lichess_activity(
        #             update=update,
        #             context=context,
        #             lichess_username=user.lichess_username,
        #             tg_username=user.tg_username,
        #             tg_id=user.tg_id
        #         )
        #
        #     else:
        #         await command_set_lichess_username(update, context)
        #
        # else:
        #     db.add_user(chat.id, chat.username, chat.first_name, chat.last_name)
        #     await context.bot.send_message(MY_ID, f'Добавлен пользователь @{chat.username} ({chat.id})')
        #     about_to_set_lichess_username.add(chat.id)
        #     await update.message.reply_text('Твой ник на Lichess?')


async def command_set_lichess_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_to_set_lichess_username.add(update.effective_chat.id)
    await update.message.reply_text('Напиши свой ник на Lichess')


# async def command_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_chat.id != MY_ID:
#         return
#
#     users = db.get_all_users()
#     msg = '*Пользователи бота:*\n'
#     for no, user in enumerate(users, start=1):
#         user.tg_last_name = f' {escape_markdown(user.tg_last_name)}' if user.tg_last_name else ''
#         lichess_username = escape_markdown(user.lichess_username) if user.lichess_username else '_ник на Lichess не установлен_'
#         msg += f'\n{no}) @{escape_markdown(user.tg_username)} ({user.tg_id}) — {escape_markdown(user.tg_first_name)}{user.tg_last_name} → {lichess_username}'
#     await context.bot.send_message(MY_ID, msg, parse_mode='markdown')


async def send_lichess_activity(update: Update, lichess_username: str, context: ContextTypes.DEFAULT_TYPE = None, tg_username: str = None, tg_id: int = None) -> None:
    msg = get_lichess_activity_message(lichess_username)
    if msg is None:
        await update.message.reply_text(f'Не удалось получить активность пользователя {lichess_username} на Lichess')
        if update.effective_chat.id != MY_ID:
            await context.bot.send_message(MY_ID, f'Не удалось получить активность пользователя @{tg_username} ({tg_id}) на Lichess.')
        return
    await update.message.reply_text(msg, parse_mode='markdownV2')


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'{context.error}\n{traceback.format_exc()}')


def run_bot():
    print('Starting bot...')
    defaults = Defaults(tzinfo=ZoneInfo('Europe/Moscow'))
    app = Application.builder().token(TOKEN).defaults(defaults).build()

    # Commands
    app.add_handler(CommandHandler('start', command_start))
    app.add_handler(CommandHandler('set_lichess_username', command_set_lichess_username))
    # app.add_handler(CommandHandler('_users', command_users))

    # Errors
    app.add_error_handler(handle_error)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Callbacks
    # app.add_handler(CallbackQueryHandler(handle_callback))

    # Pools the bot
    print('Polling...')
    app.run_polling(poll_interval=1)


if __name__ == '__main__':
    if os.name == 'posix':
        from setproctitle import setproctitle
        setproctitle('lichess_bot')

    # Настройка логов
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        filename='info.log',
        filemode='w',
        level=logging.INFO
    )
    logger = logging.getLogger('httpx')
    logger.setLevel(logging.WARNING)

    # db = Database()
    COMMANDS_SET = False
    about_to_set_lichess_username = set()

    bot_commands = [
        ('start', 'Старт'),
        ('set_lichess_username', 'Установить ник на Lichess'),
    ]
    bot_commands_admin = [
        ('start', 'Старт'),
        ('set_lichess_username', 'Установить ник на Lichess'),
        # ('_users', 'Список пользователей')
    ]
    run_bot()
