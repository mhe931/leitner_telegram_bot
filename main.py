import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from config import TELEGRAM_BOT_TOKEN

# Initialize the database connection
conn = sqlite3.connect('flashcards.db', check_same_thread=False)
cursor = conn.cursor()

# Create necessary tables if they do not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message_id INTEGER,
    box INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')
conn.commit()

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    update.message.reply_text(
        "Welcome to the Leitner System Bot! Use /commands to see available commands."
    )

# List of available commands
def commands(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "/start - Register yourself\n"
        "/commands - List all available commands\n"
        "/review - Review flashcards due for today\n"
        "/reminder - Toggle daily reminders\n"
        "/all - Display all your flashcards\n"
        "/edit - Edit or delete flashcards\n"
    )

# Add flashcard
def add_flashcard(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    cursor.execute("INSERT INTO flashcards (user_id, message_id, box) VALUES (?, ?, ?)", (user_id, message_id, 1))
    conn.commit()
    update.message.reply_text("Flashcard added!")

# Review flashcards
def review(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT message_id FROM flashcards WHERE user_id = ? AND box = 1", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        update.message.reply_text("No flashcards to review.")
        return

    for flashcard in flashcards:
        message_id = flashcard[0]
        context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)
        keyboard = [
            [InlineKeyboardButton("True", callback_data=f'true_{message_id}'), InlineKeyboardButton("False", callback_data=f'false_{message_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=user_id, text="Did you remember?", reply_markup=reply_markup)

def handle_review_response(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data.split('_')
    response = data[0]
    message_id = int(data[1])
    user_id = query.from_user.id

    if response == 'true':
        cursor.execute("UPDATE flashcards SET box = box + 1 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
    else:
        cursor.execute("UPDATE flashcards SET box = 1 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
    conn.commit()
    query.edit_message_text(text="Flashcard updated!")

# Toggle daily reminders
def reminder(update: Update, context: CallbackContext) -> None:
    # This feature would typically require scheduling, which is out of the scope for this simple bot.
    update.message.reply_text("Reminder feature is not implemented in this example.")

# Display all flashcards
def display_all(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT message_id FROM flashcards WHERE user_id = ?", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        update.message.reply_text("You have no flashcards.")
        return

    for flashcard in flashcards:
        message_id = flashcard[0]
        context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)

# Edit flashcards
def edit_flashcards(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT id, message_id FROM flashcards WHERE user_id = ?", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        update.message.reply_text("You have no flashcards to edit.")
        return

    for flashcard in flashcards:
        flashcard_id = flashcard[0]
        message_id = flashcard[1]
        context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)
        keyboard = [
            [InlineKeyboardButton("Edit", callback_data=f'edit_{flashcard_id}'), InlineKeyboardButton("Delete", callback_data=f'delete_{flashcard_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=user_id, text="Edit or delete this flashcard?", reply_markup=reply_markup)

def handle_edit_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data.split('_')
    action = data[0]
    flashcard_id = int(data[1])
    user_id = query.from_user.id

    if action == 'delete':
        cursor.execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,))
        conn.commit()
        query.edit_message_text(text="Flashcard deleted!")
    elif action == 'edit':
        cursor.execute("SELECT message_id FROM flashcards WHERE id = ?", (flashcard_id,))
        message_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,))
        conn.commit()
        query.edit_message_text(text="Please send the new text for the flashcard.")
        context.user_data['edit_message_id'] = message_id

def handle_new_text(update: Update, context: CallbackContext) -> None:
    if 'edit_message_id' in context.user_data:
        user_id = update.message.from_user.id
        old_message_id = context.user_data.pop('edit_message_id')
        new_message_id = update.message.message_id
        cursor.execute("INSERT INTO flashcards (user_id, message_id, box) VALUES (?, ?, ?)", (user_id, new_message_id, 1))
        conn.commit()
        update.message.reply_text("Flashcard updated!")

def main() -> None:
    # Initialize the bot and dispatcher
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("review", review))
    dispatcher.add_handler(CommandHandler("reminder", reminder))
    dispatcher.add_handler(CommandHandler("all", display_all))
    dispatcher.add_handler(CommandHandler("edit", edit_flashcards))

    # Register message handlers
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, add_flashcard))
    dispatcher.add_handler(MessageHandler(Filters.reply, handle_new_text))

    # Register callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(handle_review_response, pattern='^true_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_review_response, pattern='^false_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_edit_delete, pattern='^edit_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_edit_delete, pattern='^delete_'))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
