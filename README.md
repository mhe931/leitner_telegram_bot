# leitner_telegram_bot
Leitner box python telegram bot
This project is a Telegram bot that implements a Leitner system for flashcard-based learning. The bot allows users to add flashcards, review them at scheduled intervals, receive daily reminders, and check their Leitner box status. The data is stored in a SQLite database.

## Features

- **Add Flashcards**: Users can send messages as flashcards (text only).
- **Review Flashcards**: The bot will present flashcards for review based on the Leitner system schedule.
- **Daily Reminders**: Users can enable/disable daily reminders to review their flashcards.
- **Leitner Box Status**: Users can check the status of their Leitner boxes to see how many flashcards are in each box.

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/mhe931/leitner_telegram_bot.git
    cd leitner_telegram_bot
    ```

2. **Install the required libraries**:
    ```sh
    pip install python-telegram-bot==13.7
    ```

3. **Create the SQLite database**:
    ```python
    import sqlite3

    def create_db():
        conn = sqlite3.connect('leitner_system.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     id INTEGER PRIMARY KEY,
                     chat_id INTEGER UNIQUE,
                     reminder_enabled BOOLEAN DEFAULT 1)''')

        c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     question TEXT,
                     answer TEXT,
                     box INTEGER DEFAULT 1,
                     review_date DATE,
                     FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit()
        conn.close()

    create_db()
    ```

4. **Set your Telegram Bot Token**:
   Replace `"YOUR_TELEGRAM_BOT_TOKEN"` in the `main` function with your actual bot token from [BotFather](https://core.telegram.org/bots#botfather).

## Usage

1. **Start the bot**:
    ```sh
    python bot.py
    ```

2. **Interact with the bot**:
    - **/start**: Register yourself in the bot's database.
    - **Send messages**: Add flashcards by sending text messages.
    - **/review**: Review flashcards due for today.
    - **/reminder**: Toggle daily reminders.
    - **/box**: Check the status of your Leitner boxes.

## How It Works

### Adding Flashcards

Users add flashcards by simply sending a text message to the bot. Each flashcard is stored in the database with an initial box value of 1 and a review date set to the next day.

### Reviewing Flashcards

When the user issues the `/review` command, the bot fetches all flashcards due for review (those with a review date of today or earlier) and presents them one by one. Users reply with their answers, and the bot checks if they are correct. Correct answers move the flashcard to the next box with a review date set to `2^box` days later. Incorrect answers reset the flashcard to box 1 with the review date set to the next day.

### Daily Reminders

Users can enable or disable daily reminders using the `/reminder` command. If enabled, the bot will send a reminder message every day at 9 AM to review flashcards.

### Leitner Box Status

Users can check the number of flashcards in each Leitner box using the `/box` command.

## Contributing

Feel free to submit issues, fork the repository, and send pull requests. Contributions are welcome!

## License

This project is licensed under the MIT License.

## Acknowledgements

- [python-telegram-bot](https://python-telegram-bot.org/) - Python wrapper for the Telegram Bot API.
- [SQLite](https://www.sqlite.org/) - Lightweight database engine.

