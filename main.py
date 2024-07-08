import sqlite3
import datetime
from config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext, JobQueue, ContextTypes

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

cursor.execute('''
CREATE TABLE IF NOT EXISTS reminders (
    user_id INTEGER PRIMARY KEY,
    reminder_time TEXT,
    enabled INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')
conn.commit()

# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    
    # Get user details
    user = update.message.from_user
    user_name = user.full_name
    user_telegram_id = user.id
    username = user.username
    
    # Fetch user profile photos
    bot: Bot = context.bot
    profile_photos = await bot.get_user_profile_photos(user_id)
    
    if profile_photos.total_count > 0:
        photo_file_id = profile_photos.photos[0][-1].file_id  # Get the highest resolution photo
    else:
        photo_file_id = None
    
    # Message to admin
    message = (
        f"New user joined:\n"
        f"Name: {user_name}\n"
        f"Telegram ID: {user_telegram_id}\n"
        f"Username: @{username if username else 'N/A'}"
    )
    
    # Send the message and the profile photo (if available) to the admin
    await bot.send_message(chat_id=ADMIN_ID, text=message)
    if photo_file_id:
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id)
    
    await update.message.reply_text(
        "Welcome to the Leitner System Bot! Use /commands to see available commands."
    )

# Help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Welcome to the Leitner System Bot!\n\n"
        "This bot helps you to learn and memorize information using the Leitner system, which is a popular method of spaced repetition.\n\n"
        "How it works:\n"
        "1. You add flashcards with the information you want to learn.\n"
        "2. The flashcards are placed in different boxes (or levels).\n"
        "3. When you review a flashcard correctly, it moves to the next box, increasing the interval before you review it again.\n"
        "4. If you answer incorrectly, the flashcard moves back to the first box, ensuring you review it more frequently.\n\n"
        "Commands:\n"
        "/start - Register yourself and start using the bot\n"
        "/commands - List all available commands\n"
        "/review - Review flashcards due for today\n"
        "/reminder - Toggle daily reminders\n"
        "/box - Display the status of your flashcard boxes\n"
        "/all - Display all your flashcards\n"
        "/edit - Edit or delete flashcards\n"
        "/help - Show this help message\n"
        "/new - Show how to add new flashcards\n"
    )
    await update.message.reply_text(help_text)

# Commands list handler
async def commands(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "/start - Register yourself and start using the bot\n"
        "/commands - List all available commands\n"
        "/review - Review flashcards due for today\n"
        "/reminder - Toggle daily reminders\n"
        "/box - Display the status of your flashcard boxes\n"
        "/all - Display all your flashcards\n"
        "/edit - Edit or delete flashcards\n"
        "/help - Show help message about how the bot works and what is the Leitner system\n"
        "/new - Show how to add new flashcards\n"
    )

# New command handler
async def new(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("No need a command to add a card, just send the text.")

# Add flashcard
async def add_flashcard(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    cursor.execute("INSERT INTO flashcards (user_id, message_id, box) VALUES (?, ?, ?)", (user_id, message_id, 1))
    conn.commit()
    await update.message.reply_text("Flashcard added!")

# Review flashcards
async def review(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT message_id FROM flashcards WHERE user_id = ? AND box = 1", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        await update.message.reply_text("No flashcards to review.")
        return

    for flashcard in flashcards:
        message_id = flashcard[0]
        await context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)
        keyboard = [
            [InlineKeyboardButton("True", callback_data=f'true_{message_id}'), InlineKeyboardButton("False", callback_data=f'false_{message_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="Did you remember?", reply_markup=reply_markup)

async def handle_review_response(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    response = data[0]
    message_id = int(data[1])
    user_id = query.from_user.id

    if response == 'true':
        cursor.execute("UPDATE flashcards SET box = box + 1 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
    else:
        cursor.execute("UPDATE flashcards SET box = 1 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
    conn.commit()
    await query.edit_message_text(text="Flashcard updated!")

# Toggle daily reminders
async def reminder(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT enabled FROM reminders WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        enabled = not result[0]
        cursor.execute("UPDATE reminders SET enabled = ? WHERE user_id = ?", (enabled, user_id))
    else:
        enabled = 1
        reminder_time = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%H:%M")  # Default reminder time
        cursor.execute("INSERT INTO reminders (user_id, reminder_time, enabled) VALUES (?, ?, ?)", (user_id, reminder_time, enabled))
    conn.commit()
    
    await update.message.reply_text(f"Daily reminders {'enabled' if enabled else 'disabled'}.")

# Display box status
async def box(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT box, COUNT(*) FROM flashcards WHERE user_id = ? GROUP BY box", (user_id,))
    box_status = cursor.fetchall()

    if not box_status:
        await update.message.reply_text("You have no flashcards.")
        return

    message = "Box Status:\n"
    for box, count in box_status:
        message += f"Box {box}: {count} flashcards\n"
    
    await update.message.reply_text(message)

# Display all flashcards
async def display_all(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT message_id FROM flashcards WHERE user_id = ?", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        await update.message.reply_text("You have no flashcards.")
        return

    for flashcard in flashcards:
        message_id = flashcard[0]
        await context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)

# Edit flashcards
async def edit_flashcards(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT id, message_id FROM flashcards WHERE user_id = ?", (user_id,))
    flashcards = cursor.fetchall()

    if not flashcards:
        await update.message.reply_text("You have no flashcards to edit.")
        return

    for flashcard in flashcards:
        flashcard_id = flashcard[0]
        message_id = flashcard[1]
        await context.bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id)
        keyboard = [
            [InlineKeyboardButton("Edit", callback_data=f'edit_{flashcard_id}'), InlineKeyboardButton("Delete", callback_data=f'delete_{flashcard_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="Edit or delete this flashcard?", reply_markup=reply_markup)

async def handle_edit_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action = data[0]
    flashcard_id = int(data[1])
    user_id = query.from_user.id

    if action == 'delete':
        cursor.execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,))
        conn.commit()
        await query.edit_message_text(text="Flashcard deleted!")
    elif action == 'edit':
        cursor.execute("SELECT message_id FROM flashcards WHERE id = ?", (flashcard_id,))
        message_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,))
        conn.commit()
        await query.edit_message_text(text="Please send the new text for the flashcard.")
        context.user_data['edit_message_id'] = message_id

async def handle_new_text(update: Update, context: CallbackContext) -> None:
    if 'edit_message_id' in context.user_data:
        user_id = update.message.from_user.id
        old_message_id = context.user_data.pop('edit_message_id')
        new_message_id = update.message.message_id
        cursor.execute("INSERT INTO flashcards (user_id, message_id, box) VALUES (?, ?, ?)", (user_id, new_message_id, 1))
        conn.commit()
        await update.message.reply_text("Flashcard updated!")

# Send daily reminders
async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT user_id, reminder_time FROM reminders WHERE enabled = 1")
    reminders = cursor.fetchall()
    now = datetime.datetime.now().strftime("%H:%M")

    for user_id, reminder_time in reminders:
        if now == reminder_time:
            await context.bot.send_message(chat_id=user_id, text="Time to review your flashcards! Use /review to start.")

def main() -> None:
    # Initialize the bot and dispatcher
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("review", review))
    application.add_handler(CommandHandler("reminder", reminder))
    application.add_handler(CommandHandler("box", box))
    application.add_handler(CommandHandler("all", display_all))
    application.add_handler(CommandHandler("edit", edit_flashcards))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_flashcard))
    application.add_handler(MessageHandler(filters.REPLY, handle_new_text))

    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(handle_review_response, pattern='^true_'))
    application.add_handler(CallbackQueryHandler(handle_review_response, pattern='^false_'))
    application.add_handler(CallbackQueryHandler(handle_edit_delete, pattern='^edit_'))
    application.add_handler(CallbackQueryHandler(handle_edit_delete, pattern='^delete_'))

    # Schedule daily reminders
    application.job_queue.run_daily(send_daily_reminders, time=datetime.time(hour=0, minute=0))  # Adjust time as needed

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
