import logging
from datetime import datetime, timedelta, time
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from config import * 


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Database connection
def connect_db():
    return sqlite3.connect('leitner_system.db')

# Commands list
COMMANDS = {
    'start': 'Start using the bot and register yourself.',
    'review': 'Review flashcards due for today.',
    'reminder': 'Enable or disable daily reminders.',
    'box': 'See the status of your Leitner boxes.',
    'all': 'View all your flashcards.',
    'commands': 'Show all available commands with descriptions.',
    'edit': 'Edit or delete your flashcards.'
}

# Start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (user.id,))
    conn.commit()
    conn.close()
    commands_list = '\n'.join([f'/{cmd} - {desc}' for cmd, desc in COMMANDS.items()])
    update.message.reply_text(f'Welcome to the Leitner System Bot! Send your flashcards as messages.\n\nAvailable commands:\n{commands_list}')

# Commands command
def show_commands(update: Update, context: CallbackContext) -> None:
    commands_list = '\n'.join([f'/{cmd} - {desc}' for cmd, desc in COMMANDS.items()])
    update.message.reply_text(f'Available commands:\n{commands_list}')

# Add flashcard
def add_flashcard(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    question = update.message.text
    conn = connect_db()
    c = conn.cursor()
    c.execute('INSERT INTO flashcards (user_id, question, box, review_date) VALUES ((SELECT id FROM users WHERE chat_id = ?), ?, 1, ?)', 
              (user.id, question, (datetime.now() + timedelta(days=1)).date()))
    conn.commit()
    conn.close()
    update.message.reply_text('Flashcard added!')

# Review command
def review(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT id, question FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?) AND review_date <= ?', 
              (user.id, datetime.now().date()))
    flashcards = c.fetchall()
    conn.close()

    if flashcards:
        for card in flashcards:
            keyboard = [
                [InlineKeyboardButton("True", callback_data=f'true_{card[0]}')],
                [InlineKeyboardButton("False", callback_data=f'false_{card[0]}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(f'Question: {card[1]}', reply_markup=reply_markup)
    else:
        update.message.reply_text('No flashcards to review today.')

# Handle inline button responses
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_response, card_id = query.data.split('_')

    conn = connect_db()
    c = conn.cursor()
    if user_response == 'true':
        # Move to the next box
        c.execute('SELECT box FROM flashcards WHERE id = ?', (card_id,))
        box = c.fetchone()[0]
        new_box = box + 1
        new_review_date = datetime.now() + timedelta(days=2**(new_box - 1))
        c.execute('UPDATE flashcards SET box = ?, review_date = ? WHERE id = ?', 
                  (new_box, new_review_date.date(), card_id))
    else:
        # Move to the first box
        new_review_date = datetime.now() + timedelta(days=1)
        c.execute('UPDATE flashcards SET box = 1, review_date = ? WHERE id = ?', 
                  (new_review_date.date(), card_id))
    conn.commit()
    conn.close()
    query.edit_message_text(text=f"Your response: {user_response.capitalize()}")

# Reminder command
def reminder(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT reminder_enabled FROM users WHERE chat_id = ?', (user.id,))
    reminder_enabled = c.fetchone()[0]

    new_status = not reminder_enabled
    c.execute('UPDATE users SET reminder_enabled = ? WHERE chat_id = ?', (new_status, user.id))
    conn.commit()
    conn.close()

    status = 'enabled' if new_status else 'disabled'
    update.message.reply_text(f'Reminder {status}.')

# Box status command
def box_status(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT box, COUNT(*) FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?) GROUP BY box', 
              (user.id,))
    boxes = c.fetchall()
    conn.close()

    if boxes:
        status = '\n'.join([f'Box {box[0]}: {box[1]} cards' for box in boxes])
    else:
        status = 'You have no cards in your Leitner boxes.'

    update.message.reply_text(status)

# All flashcards command
def all_flashcards(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT question, box FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)', 
              (user.id,))
    flashcards = c.fetchall()
    conn.close()

    if flashcards:
        response = '\n\n'.join([f'Question: {card[0]}\nBox: {card[1]}' for card in flashcards])
    else:
        response = 'You have no flashcards.'

    update.message.reply_text(response)

# Edit flashcards command
def edit_flashcards(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT id, question FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)', 
              (user.id,))
    flashcards = c.fetchall()
    conn.close()

    if flashcards:
        keyboard = [
            [InlineKeyboardButton(f"Edit: {card[1]}", callback_data=f'edit_{card[0]}'), 
             InlineKeyboardButton(f"Delete: {card[1]}", callback_data=f'delete_{card[0]}')]
            for card in flashcards
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Select a question to edit or delete:', reply_markup=reply_markup)
    else:
        update.message.reply_text('You have no flashcards to edit or delete.')

# Handle edit/delete inline button responses
def edit_delete_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    action, card_id = query.data.split('_')

    if action == 'edit':
        context.user_data['editing'] = card_id
        query.edit_message_text(text='Please send the new question text:')
    elif action == 'delete':
        conn = connect_db()
        c = conn.cursor()
        c.execute('DELETE FROM flashcards WHERE id = ?', (card_id,))
        conn.commit()
        conn.close()
        query.edit_message_text(text='Flashcard deleted!')

# Handle new question text for editing
def handle_new_question(update: Update, context: CallbackContext) -> None:
    if 'editing' in context.user_data:
        card_id = context.user_data['editing']
        new_question = update.message.text

        conn = connect_db()
        c = conn.cursor()
        c.execute('UPDATE flashcards SET question = ? WHERE id = ?', (new_question, card_id))
        conn.commit()
        conn.close()

        del context.user_data['editing']
        update.message.reply_text('Flashcard updated!')

# Daily reminders
def daily_reminder(context: CallbackContext) -> None:
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT chat_id FROM users WHERE reminder_enabled = 1')
    users = c.fetchall()
    conn.close()

    for user in users:
        context.bot.send_message(chat_id=user[0], text='Time to review your flashcards! Use /review to start.')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("review", review))
    dp.add_handler(CommandHandler("reminder", reminder))
    dp.add_handler(CommandHandler("box", box_status))
    dp.add_handler(CommandHandler("all", all_flashcards))
    dp.add_handler(CommandHandler("commands", show_commands))
    dp.add_handler(CommandHandler("edit", edit_flashcards))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_flashcard))
    dp.add_handler(MessageHandler(Filters.text & Filters.reply, handle_new_question))
    dp.add_handler(CallbackQueryHandler(button, pattern='^(true|false)_'))
    dp.add_handler(CallbackQueryHandler(edit_delete_button, pattern='^(edit|delete)_'))

    job_queue = updater.job_queue
    job_queue.run_daily(daily_reminder, time=time(hour=9, minute=0, second=0))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
