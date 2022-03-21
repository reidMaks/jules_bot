import html
import json
import logging
import os
import traceback

from telegram import Update, ForceReply, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from helpers import remove_audio_files

from irregular_verbs import IrregularVerbsSet
from quiz import Quiz


QUIZ_MAP = {}

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    in_entity = update.message or update.callback_query.message 
    context.bot.send_message(chat_id=in_entity.chat_id, text=message, parse_mode=ParseMode.HTML)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def get_random_iv(update: Update, context: CallbackContext):
    word = IrregularVerbsSet.get_random_verb()
    text = word.get_spelling()
    voice, *params = word.get_voice()

    if params:
        voice_params = dict(voice=params[0],
                            duration=round(params[2], 0))
    else:
        voice_params = dict(voice=voice)

    message = update.message.reply_voice(**voice_params,
                                         caption=text,
                                         parse_mode=ParseMode.MARKDOWN_V2)

    word.voice = message.effective_attachment
    remove_audio_files()


def get_all_iv(update: Update, context: CallbackContext):
    for word in IrregularVerbsSet.verbs_extended:
  
        text = word.get_spelling()
        voice, *params = word.get_voice()

        if params:
            voice_params = dict(voice=params[0],
                                duration=round(params[2], 0))
        else:
            voice_params = dict(voice=voice)

        message = update.message.reply_voice(**voice_params,
                                            caption=text,
                                            parse_mode=ParseMode.MARKDOWN_V2)

        word.voice = message.effective_attachment
        remove_audio_files()


def feedback(update: Update, context: CallbackContext):
    text = "З питань розвитку бота чи в разі виникнення проблем в його роботі, пишіть @kms_live"
    update.message.reply_text(text)

def start_quiz(update: Update, context: CallbackContext):
    global QUIZ_MAP
    user = update.message.from_user.id
    existed_quiz = QUIZ_MAP.get(user)
    if not existed_quiz:
        existed_quiz = Quiz(update.message)
        QUIZ_MAP[user] = existed_quiz
    else:
        message = existed_quiz.message
        message.reply_text('Here is your quiz', reply_to_message_id=message.message_id)

def callback_handler(update: Update, context: CallbackContext):
    global QUIZ_MAP
    user = update.callback_query.from_user.id
    existed_quiz = QUIZ_MAP.get(user)

    if not existed_quiz:
        update.callback_query.answer("🪲 Sorry. Something went wrong... Try creating a new quiz",
                                     show_alert=True)
        return
    
    existed_quiz.process(update)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv("TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("get_random_iv", get_random_iv))
    dispatcher.add_handler(CommandHandler("start_quiz", start_quiz))
    dispatcher.add_handler(CommandHandler("get_all_iv", get_all_iv))
    dispatcher.add_handler(CommandHandler("feedback", feedback))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    dispatcher.add_handler(CallbackQueryHandler(callback_handler))

    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
