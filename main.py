import logging
from datetime import datetime, timedelta
import sqlite3
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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

# Start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (user.id,))
    conn.commit()
    conn.close()
    update.message.reply_text('Welcome to the Leitner System Bot! Send your flashcards as messages.')

# Add flashcard
def add_flashcard(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    if update.message.text:
        question = update.message.text
        conn = connect_db()
        c = conn.cursor()
        c.execute('INSERT INTO flashcards (user_id, question, box, review_date) VALUES ((SELECT id FROM users WHERE chat_id = ?), ?, 1, ?)', (user.id, question, (datetime.now() + timedelta(days=1)).date()))
        conn.commit()
        conn.close()
        update.message.reply_text('Flashcard added!')

# Review command
def review(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT id, question FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?) AND review_date <= ?', (user.id, datetime.now().date()))
    flashcards = c.fetchall()
    conn.close()

    if flashcards:
        for card in flashcards:
            update.message.reply_text(f'Question: {card[1]}\nSend your answer:')
            context.user_data['reviewing'] = card[0]
            return
    else:
        update.message.reply_text('No flashcards to review today.')

# Answer handling
def handle_answer(update: Update, context: CallbackContext) -> None:
    if 'reviewing' in context.user_data:
        card_id = context.user_data['reviewing']
        user_answer = update.message.text

        conn = connect_db()
        c = conn.cursor()
        c.execute('SELECT answer FROM flashcards WHERE id = ?', (card_id,))
        correct_answer = c.fetchone()[0]
        conn.close()

        if user_answer.lower() == correct_answer.lower():
            update.message.reply_text('Correct!')
            # Move to the next box
            conn = connect_db()
            c = conn.cursor()
            c.execute('UPDATE flashcards SET box = box + 1, review_date = ? WHERE id = ?', ((datetime.now() + timedelta(days=2**(box - 1))).date(), card_id))
            conn.commit()
            conn.close()
        else:
            update.message.reply_text(f'Incorrect! The correct answer is: {correct_answer}')
            # Move to the first box
            conn = connect_db()
            c = conn.cursor()
            c.execute('UPDATE flashcards SET box = 1, review_date = ? WHERE id = ?', ((datetime.now() + timedelta(days=1)).date(), card_id))
            conn.commit()
            conn.close()

        del context.user_data['reviewing']

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
    c.execute('SELECT box, COUNT(*) FROM flashcards WHERE user_id = (SELECT id FROM users WHERE chat_id = ?) GROUP BY box', (user.id,))
    boxes = c.fetchall()
    conn.close()

    if boxes:
        status = '\n'.join([f'Box {box[0]}: {box[1]} cards' for box in boxes])
    else:
        status = 'You have no cards in your Leitner boxes.'

    update.message.reply_text(status)

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
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_flashcard))
    dp.add_handler(MessageHandler(Filters.text & Filters.reply, handle_answer))

    job_queue = updater.job_queue
    job_queue.run_daily(daily_reminder, time=datetime.time(hour=9, minute=0, second=0))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
